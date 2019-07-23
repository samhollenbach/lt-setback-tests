import pulp
import datetime
from util import get_sst, get_charge_cop
from optimizer_engine.cop import farenheit_to_celsius, celsius_to_farenheit
from lt_optimizer import Optimizer
from savings import get_bill_calculator


def run_iterative_optimizer(loads, config):
    optimizer_config = config['optimizer_config']
    bill_calculator = get_bill_calculator(optimizer_config)
    targets = []
    for time_frame, load in loads:

        previous_total_savings = 0
        previous_diff = 0
        iteration_limit = 10
        optimizer_config['start'] = load.index[0]
        optimizer_config['end'] = load.index[-1]
        count = 0

        while True:
            print(time_frame)
            count += 1

            optimizer = Optimizer(optimizer_config)
            target = optimizer.solve(load)
            print(pulp.LpStatus[optimizer.frame.status])

            baseline_demand = bill_calculator.calculate_demand_bill(
                target, load_column='baseline')
            baseline_energy = bill_calculator.calculate_energy_bill(
                target, load_column='baseline')

            ideal_demand = bill_calculator.calculate_demand_bill(target)
            ideal_energy = bill_calculator.calculate_energy_bill(target)

            demand_savings = baseline_demand - ideal_demand
            energy_savings = baseline_energy - ideal_energy

            total_savings = demand_savings + energy_savings

            savings_diff = abs(total_savings - previous_total_savings)

            print("Solved for count {}".format(count))
            print("Total Savings {}".format(total_savings))
            print("Delta in savings {}".format(savings_diff))

            if count == iteration_limit:
                print("Warning: Optimizer iteration limit reached")
                break

            if (savings_diff < 10 or abs(savings_diff - previous_diff) < 1):
                break

            previous_total_savings = total_savings
            previous_diff = savings_diff

            sst_df = get_sst(target.soc, config)
            oat_df = farenheit_to_celsius(target.temperature)

            load = load.assign(cop_charge=get_charge_cop(sst_df, oat_df))

        target.drop(columns=['timestamp'], inplace=True)
        target['sst'] = list(
            map(celsius_to_farenheit, get_sst(target['soc'], config)))
        targets.append(target)

        print(f"Completed optimizing for {time_frame}")

    return targets
