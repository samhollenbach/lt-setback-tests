import matplotlib.pyplot as plt
from pprint import pprint
import pandas as pd
import config
import load
import savings
from display import lt_plot, peak_plot, stat_plot, stat_plot_compare
import util
import analyze
from iterative_optimizer import run_iterative_optimizer
from pickle_jar import pickle_jar


@pickle_jar(detect_changes=True)
def load_data(site, start, end, power_file, config_file):
    master_conf = config.get_master_config(site, start, end,
                                           config_file)
    power_data = load.read_power_data(power_file,
                                      master_conf)

    master_conf['optimizer_config']['MRC'] = power_data.crs_baseline.max() + 2

    power_data = util.add_thermal_info(power_data, master_conf)

    power_data = power_data.drop('crs_baseline', axis=1)
    return power_data, master_conf


# @pickle_jar(detect_changes=False)
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
    print(start, end)
    data_slice = data[(data.index >= start) & (data.index <= end)]

    conf['optimizer_config']['start'] = start
    conf['optimizer_config']['end'] = end
    conf['start'] = start
    conf['end'] = end
    months = data_slice.groupby('month')
    return run_iterative_optimizer(months, conf)


# @pickle_jar(detect_changes=False)
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
    print(start, end)
    data_slice = data[(data.index >= start) & (data.index <= end)]

    conf['optimizer_config']['start'] = start
    conf['optimizer_config']['end'] = end
    conf['start'] = start
    conf['end'] = end
    data_slice = data_slice.groupby('date')
    return run_iterative_optimizer(data_slice, conf)


@pickle_jar(detect_changes=False)
def get_monthly_daily_targets(power_data, master_conf):
    monthly_targets = get_monthly_targets(power_data, master_conf)

    daily_targets = get_daily_targets(power_data, master_conf)

    final_monthly = pd.concat(monthly_targets)
    final_monthly = final_monthly.assign(
        date=final_monthly.index.to_series(keep_tz=True).apply(
            lambda t: f"{t.year}-{t.month}-{t.day}"))
    monthly_targets_days = final_monthly.groupby('date')
    monthly_targets_days = [m[1] for m in monthly_targets_days]
    return monthly_targets_days, daily_targets


def single_day_analysis(targets, id):
    max_peak = max([max(t['soc']) for t in targets])
    cur = targets[id]
    ax = lt_plot(cur, max_peak=max_peak)
    plt.show()
    peaks, properties = analyze.find_target_peaks(cur, height=max_peak / 2)
    ax2 = peak_plot(cur, peaks, properties, max_peak=max_peak)
    plt.show()


site = 'WFROS'
start = "2018-06-01 00:00:00-07"
end = "2019-05-31 23:45:00-07"
power_file = 'input/WFROS_timeseries_filled.csv'
config_file = 'input/WF_LTSB_mass_and_SST.csv'
power_data, master_conf = load_data(site, start, end, power_file, config_file)
master_conf['optimize_energy'] = False

monthly_targets_days, daily_targets = get_monthly_daily_targets(power_data,
                                                                master_conf)

# for i in range(100, 220):
#     single_day_analysis(monthly_targets_days, i)

stats_monthly = analyze.collect_stats(monthly_targets_days)
stats_daily = analyze.collect_stats(daily_targets)

ax = stat_plot(stats_daily)
ax2 = stat_plot(stats_monthly)
ax3 = stat_plot_compare(stats_monthly, stats_daily)
plt.show()

monthly_run_days = analyze.find_daily_monthly_days(daily_targets, stats_daily,
                                                   monthly_targets_days,
                                                   stats_monthly)

for day_targets, day_stats, month_targets, month_stats, in monthly_run_days:
    lt_plot(day_targets)
    lt_plot(month_targets)
    plt.show()
