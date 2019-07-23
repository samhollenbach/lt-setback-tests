from optimizer_engine.cop import farenheit_to_celsius
from tariff import Tariff
from tariff.bill_calculator import BillCalculator


def master_cop_eq(sst, oat):
    return 0.03365441 * sst - 0.03725518 * oat + 3.681996189703361 + 0.35


def add_thermal_info(power_data, config):
    power_data = add_cops(power_data, config)
    power_data = add_charge_limits(power_data, config)
    power_data = add_heat_leak(power_data, config)
    return power_data


def add_cops(df, config):
    # ADD COP's according to master equation at mid point SST
    df = df.assign(oat_c=df.temperature.apply(farenheit_to_celsius))
    # USE COP AT MID SST & ITERATE
    df = df.assign(cop_charge=df.oat_c.apply(config['cop_max_sst']))
    # USE COP AT MAX SST
    return df.assign(cop_discharge=df.oat_c.apply(config['cop_max_sst']))


def add_charge_limits(df, config):
    # ADD charge limits
    df = df.assign(
        charge_limits=config['optimizer_config']['MRC'] - df.crs_baseline)
    # ADD discharge limits
    return df.assign(discharge_limits=df.crs_baseline)


def add_heat_leak(df, config):
    # ADD heat leak column
    return df.assign(heat_leak=get_heat_leak(df, config))


def get_sst(soc, config):
    sst_min_c = farenheit_to_celsius(config['sst_min_f'])
    sst_max_c = farenheit_to_celsius(config['sst_max_f'])

    m = (sst_max_c - sst_min_c) / (0 - config['lt_capacity'])

    c = sst_min_c - m * config['lt_capacity']

    return soc.apply(lambda x: m * x + c)


def get_charge_cop(sst_list, oat_list):
    cop_charge = []

    for sst, oat in zip(sst_list, oat_list):
        cop_charge.append(master_cop_eq(sst, oat))

    return cop_charge


def get_heat_leak(df, config):
    df = df.assign(
        oat_c=df.temperature.apply(lambda t: farenheit_to_celsius(t)))

    cop_heat_leak = df.oat_c.apply(lambda v: config['cop_max_sst'](v))

    heat_load = df.discharge_limits * cop_heat_leak

    heat_leak = heat_load * config['sst_factor'] / config['lt_capacity']

    return heat_leak


def get_demand_reductions(df, targets, config):
    peak_demand_reductions = []
    mid_peak_demand_reductions = []
    non_coincident_demand_reductions = []

    tariff = Tariff(config['site_id'])
    bill_calculator = BillCalculator(config['site_id'])

    for num, month in enumerate(targets):

        baseline_demand = bill_calculator.demand_peaks(month,
                                                       load_column="baseline")
        target_demand = bill_calculator.demand_peaks(month,
                                                     load_column="load_values")

        season = tariff.season(month.timestamp.iloc[0])
        if season == "summer":
            nc_baseline = baseline_demand["summer"]["Non-Coincident"]
            nc_target = target_demand["summer"]["Non-Coincident"]
            mp_baseline = baseline_demand["summer"]["Mid-Peak"]
            mp_target = target_demand["summer"]["Mid-Peak"]
            op_baseline = baseline_demand["summer"]["On-Peak"]
            op_target = target_demand["summer"]["On-Peak"]

            non_coincident_demand_reductions.append(nc_baseline - nc_target)
            mid_peak_demand_reductions.append(mp_baseline - mp_target)
            peak_demand_reductions.append(op_baseline - op_target)

        elif season == "winter":
            nc_baseline = baseline_demand["winter"]["Non-Coincident"]
            nc_target = target_demand["winter"]["Non-Coincident"]
            mp_baseline = baseline_demand["winter"]["Mid-Peak"]
            mp_target = target_demand["winter"]["Mid-Peak"]

            non_coincident_demand_reductions.append(nc_baseline - nc_target)
            mid_peak_demand_reductions.append(mp_baseline - mp_target)
            peak_demand_reductions.append(0)

    df = df.assign(peak_demand_reductions=peak_demand_reductions)
    df = df.assign(midpeak_demand_reductions=mid_peak_demand_reductions)
    df = df.assign(
        non_coincident_demand_reductions=non_coincident_demand_reductions)

    return df
