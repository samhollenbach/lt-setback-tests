import pytz
import pandas as pd


def read_power_data(power_file, config):
    target_tz = pytz.timezone('UTC')
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

    # timestamps = pd.date_range(start, end, freq='15T')

    # data_tz = pytz.timezone(config['optimizer_config']['timezone'])
    df = pd.read_csv(power_file, parse_dates=['timestamp'])
    df.set_index('timestamp', drop=True, inplace=True)
    # df.index = pd.DatetimeIndex([i.replace(tzinfo=data_tz) for i in
    # df.index])
    df.index = df.index.tz_localize(target_tz)
    df = df[(df.index >= start) & (df.index <= end)]
    df = df.assign(
        month=df.index.to_series(keep_tz=True).apply(
            lambda t: f"{t.year}-{t.month}"))
    df = df.assign(
        date=df.index.to_series(keep_tz=True).apply(
            lambda t: f"{t.year}-{t.month}-{t.day}"))
    df['timestamp'] = df.index.to_series(keep_tz=True)
    return df
