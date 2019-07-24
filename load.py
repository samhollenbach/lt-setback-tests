import pytz
import pandas as pd
from pickle_jar import pickle_jar
import config
import util


def read_power_data(power_file, config):
    target_tz = pytz.timezone(config['optimizer_config']['timezone'])
    start = pd.to_datetime(config['start'])
    end = pd.to_datetime(config['end'])
    try:
        start = start.tz_localize(target_tz)
    except TypeError:
        start = start.tz_convert(target_tz)

    try:
        end = end.tz_localize(target_tz)
    except TypeError:
        end = end.tz_convert(target_tz)

    timestamps = pd.date_range(start, end, freq='15T')

    try:
        df = pd.read_csv(power_file, parse_dates=['timestamp'])
    except ValueError:
        df = pd.read_excel(power_file, parse_dates=['timestamp'])

    df['timestamp'] = timestamps
    df.set_index('timestamp', drop=True, inplace=True)

    df = df[(df.index >= start) & (df.index <= end)]
    df = df.assign(
        month=df.index.to_series(keep_tz=True).apply(
            lambda t: f"{t.year}-{t.month}"))
    df = df.assign(
        date=df.index.to_series(keep_tz=True).apply(
            lambda t: f"{t.year}-{t.month}-{t.day}"))
    df['timestamp'] = df.index.to_series(keep_tz=True)

    if 'crs_new' in df.columns:
        df['crs_baseline'] = df['crs_new'].copy()
        df.drop('crs_new', axis=1, inplace=True)

    return df


@pickle_jar(detect_changes=True)
def load_data(site, start, end, power_file, config_file):
    master_conf = config.get_master_config(site, start, end,
                                           config_file)
    power_data = read_power_data(power_file,
                                 master_conf)

    master_conf['optimizer_config']['MRC'] = power_data.crs_baseline.max() + 2

    power_data = util.add_thermal_info(power_data, master_conf)

    power_data = power_data.drop('crs_baseline', axis=1)
    return power_data, master_conf
