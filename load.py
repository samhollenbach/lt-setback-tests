import pytz
import pandas as pd
from pickle_jar.pickle_jar import pickle_jar
import config
import util
from iterative_optimizer import run_iterative_optimizer


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

    try:
        df = pd.read_csv(power_file, parse_dates=['timestamp'])
    except ValueError:
        df = pd.read_excel(power_file, parse_dates=['timestamp'])

    df['timestamp'] = df['timestamp'].apply(
        lambda t: t.replace(tzinfo=target_tz))

    if start < df.iloc[0]['timestamp']:
        print("Start time out of bounds of data, clipping")
        start = df.iloc[0]['timestamp']
    if end > df.iloc[-1]['timestamp']:
        print("End time out of bounds of data, clipping")
        end = df.iloc[-1]['timestamp']

    df = df[(df.timestamp >= start) & (df.timestamp <= end)]
    timestamps = pd.date_range(start, end, freq='15T', tz=target_tz)

    try:
        df['timestamp'] = timestamps
    except ValueError:
        df['timestamp'] = timestamps[:-4]
    df.set_index('timestamp', drop=True, inplace=True)

    df = df.assign(
        month=df.index.to_series(keep_tz=True).apply(
            lambda t: f"{t:%Y}-{t:%m}"))
    df = df.assign(
        date=df.index.to_series(keep_tz=True).apply(
            lambda t: f"{t:%Y}-{t:%m}-{t:%d}"))
    df['timestamp'] = df.index.to_series(keep_tz=True)

    if 'temperature' not in df.columns and 'dbt' in df.columns:
        df['temperature'] = df['dbt'].copy()
        df.drop('dbt', axis=1, inplace=True)

    if 'crs_new' in df.columns:
        df['crs_baseline'] = df['crs_new'].copy()
        df.drop('crs_new', axis=1, inplace=True)

    return df


@pickle_jar(detect_changes=True, reload=True)
def load_data(site, start, end, power_file, config_file):
    master_conf = config.get_master_config(site, start, end,
                                           config_file)
    power_data = read_power_data(power_file,
                                 master_conf)

    master_conf['optimizer_config']['MRC'] = power_data.crs_baseline.max() + 2

    power_data = util.add_thermal_info(power_data, master_conf)

    power_data = power_data.drop('crs_baseline', axis=1)
    return power_data, master_conf


@pickle_jar(detect_changes=True)
def get_monthly_targets(data, conf, start=None, end=None):
    """
    Run optimizer on each month in dataset and collect targets.

    :param DataFrame data: Power data
    :param conf: LT Setback Config object
    :param str start: Start time of data to analyze
    :param str end: End timestamp of data to analyze
    :return: List of target DataFrames for each month
    """
    if start is None:
        start = pd.to_datetime(data.index[0])
    else:
        start = pd.to_datetime(start)
    if end is None:
        end = pd.to_datetime(data.index[-1])
    else:
        end = pd.to_datetime(end)
    data_slice = data[(data.index >= start) & (data.index <= end)]

    conf['optimizer_config']['start'] = start
    conf['optimizer_config']['end'] = end
    conf['start'] = start
    conf['end'] = end
    months = data_slice.groupby('month')
    return run_iterative_optimizer(months, conf)


@pickle_jar(detect_changes=True)
def get_daily_targets(data, conf, start=None, end=None):
    """
    Run optimizer on each individual day in data set and collect targets.

    :param DataFrame data: Power data
    :param conf: LT Setback Config object
    :return: List of target DataFrames for each month
    :param str start: Start time of data to analyze
    :param str end: End timestamp of data to analyze
    :return:
    """
    if start is None:
        start = pd.to_datetime(data.index[0])
    else:
        start = pd.to_datetime(start)
    if end is None:
        end = pd.to_datetime(data.index[-1])
    else:
        end = pd.to_datetime(end)
    data_slice = data[(data.index >= start) & (data.index <= end)]

    conf['optimizer_config']['start'] = start
    conf['optimizer_config']['end'] = end
    conf['start'] = start
    conf['end'] = end
    data_slice = data_slice.groupby('date')
    return run_iterative_optimizer(data_slice, conf)


@pickle_jar(detect_changes=True)
def get_monthly_daily_targets(power_data, master_conf):
    monthly_targets = get_monthly_targets(power_data, master_conf)

    daily_targets = get_daily_targets(power_data, master_conf)

    final_monthly = pd.concat(monthly_targets)
    final_monthly = final_monthly.assign(
        date=final_monthly.index.to_series(keep_tz=True).apply(
            lambda t: f"{t:%Y}-{t:%m}-{t:%d}"))
    monthly_targets_days = final_monthly.groupby('date')
    monthly_targets_days = [m[1] for m in monthly_targets_days]
    return monthly_targets_days, daily_targets
