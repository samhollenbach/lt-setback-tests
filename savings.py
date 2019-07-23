import datetime
import pandas as pd
from tariff.bill_calculator import BillCalculator


def get_bill_calculator(config):
    return BillCalculator(config['site_id'])


def generate_savings_table(targets, config):
    savings = []
    bill_calculator = get_bill_calculator(config)
    for num, target in enumerate(targets):
        target = target.copy()

        target = target.reset_index()

        baseline_demand = bill_calculator.calculate_demand_bill(
            target, load_column='baseline')
        baseline_energy = bill_calculator.calculate_energy_bill(
            target, load_column='baseline')
        ideal_demand = bill_calculator.calculate_demand_bill(target)
        ideal_energy = bill_calculator.calculate_energy_bill(target)

        baseline_bill = baseline_demand + baseline_energy

        demand_savings = baseline_demand - ideal_demand
        energy_savings = baseline_energy - ideal_energy

        total_savings = demand_savings + energy_savings

        dchg = target[target['offsets'] > 0]['offsets'].sum()
        chg = target[target['offsets'] < 0]['offsets'].sum()
        rte = dchg / -chg

        month = datetime.date(1900, num + 1, 1).strftime('%b')

        row = (
            month, config['lt_capacity'], demand_savings, energy_savings,
            total_savings,
            baseline_bill,
            rte)
        savings.append(row)

    savings_columns = [
        'month',
        'LT_capacity',
        'demand_savings',
        'energy_savings',
        'total_savings',
        'baseline_bill',
        'rte'
    ]
    savings_table = pd.DataFrame(savings, columns=savings_columns)
    return savings_table
