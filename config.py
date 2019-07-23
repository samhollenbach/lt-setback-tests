import pandas as pd
from functools import partial

from optimizer_engine.cop import farenheit_to_celsius
from util import master_cop_eq


def get_master_config(site, start, end, lt_config_file):
    site_id_map = {'WFROS': "pge_e19_2019"}
    lt_conf = get_lt_config(lt_config_file)
    lt_capacity = lt_conf.loc[lt_conf.Store == site]['mass_derated'].iloc[0]
    sst_max_f = lt_conf.loc[lt_conf.Store == site]['SST_max'].iloc[0]
    sst_min_f = lt_conf.loc[lt_conf.Store == site]['SST_min'].iloc[0]
    sst_mid_f = (sst_max_f + sst_min_f) / 2
    cop_mid_sst = partial(master_cop_eq, farenheit_to_celsius(sst_mid_f))
    cop_max_sst = partial(master_cop_eq, farenheit_to_celsius(sst_max_f))
    master = {
        'site': site,
        'site_id': site_id_map[site],
        'start': start,
        'end': end,
        'optimizer_config': get_optimizer_config(site_id_map[site], start, end,
                                                 lt_capacity),
        'lt_config': lt_conf,
        'lt_capacity': lt_capacity,
        'sst_max_f': sst_max_f,
        'sst_mid_f': sst_mid_f,
        'sst_min_f': sst_min_f,
        'cop_mid_sst': cop_mid_sst,
        'cop_max_sst': cop_max_sst,
        'sst_factor': 0.15,
    }
    return master


def get_optimizer_config(site_id, start, end, lt_capacity):
    config = {
        "timezone": "US/Pacific",
        "site_id": site_id,
        "start": start,
        "end": end,
        "MDL": 1000,
        "MCL": 1000,
        "min_charge_offset": 5,
        "min_discharge_offset": 5,
        # "RTE_setpoint": 0.65,
        "RB_capacity": lt_capacity,
        "M": 1000,
        "SOC_initial": 0,
        "cop_dchg_coefficients": [0],  # Already provided in timeseries data
        "cop_chg_coefficients": [0],  # Already provided in timeseries data
        "constraints": {
            "time_transition": False,
            "minimum_charge_offset": False,
            "minimum_discharge_offset": False,
            "chg_limit_curve": False,
            "dchg_limit_curve": False,
            "fixed_rte": False
        },
        "outputs": {
            "timestamp": True,
            "baseline": True,
            "offsets": True,
            "load_values": True,
            "soc": True,
            "charge_limits": True,
            "discharge_limits": True,
            "cop_dchg": True,
            "cop_chg": True,
            "temperature": True
        }
    }
    return config


def get_lt_config(config_file):
    config_lt = pd.read_csv(config_file)
    return config_lt
