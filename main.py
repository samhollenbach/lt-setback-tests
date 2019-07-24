import os
import matplotlib.pyplot as plt
from pprint import pprint
import pandas as pd
from pickle_jar import pickle_jar
from iterative_optimizer import run_iterative_optimizer
import load
import savings
from display import lt_plot, peak_plot, stat_plot, stat_plot_intervals, \
    stat_plot_compare
import analyze


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
    print(start, end)
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
    print(start, end)
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
            lambda t: f"{t.year}-{t.month}-{t.day}"))
    monthly_targets_days = final_monthly.groupby('date')
    monthly_targets_days = [m[1] for m in monthly_targets_days]
    return monthly_targets_days, daily_targets


def single_day_analysis(targets, id):
    max_peak = max([max(t['soc']) for t in targets])
    cur = targets[id]
    ax = lt_plot(cur, max_peak=max_peak)
    plt.show()
    peaks, properties = analyze.find_target_peaks(cur)
    ax2 = peak_plot(cur, peaks, properties, max_peak=max_peak)
    plt.show()


#####################
# Initialize Script #
#####################


sites = ['WM3138', 'WM3708', 'WN5606', 'WM5859', 'WM3140',
         'WM3796', 'WM4132', 'WM5603', 'WM5635']

for site in sites[:1]:
    # site = 'WFROS'
    start = "2018-06-01 00:00:00-07"
    end = "2019-05-31 23:45:00-07"
    # power_file = 'input/WFROS_timeseries_filled.csv'
    print(site)
    path = 'input/'
    power_file = [os.path.join(path, i) for i in os.listdir(path) if
                  os.path.isfile(os.path.join(path, i)) and
                  site in i][0]
    print(power_file)
    config_file = 'input/WF_LTSB_mass_and_SST.csv'
    power_data, master_conf = load.load_data('WFROS',
                                             start,
                                             end,
                                             power_file,
                                             config_file)
    master_conf['optimize_energy'] = False

    #############################
    # Get Monthly/Daily Targets #
    #############################
    monthly_targets_days, daily_targets = get_monthly_daily_targets(power_data,
                                                                    master_conf)

    # print(list(monthly_targets_days[0].columns))
    # for i in range(105, 220):
    i = len(daily_targets) - 1
    single_day_analysis(daily_targets, i)

    ###########################
    # Get Monthly/Daily Stats #
    ###########################
    stats_monthly = analyze.collect_stats(monthly_targets_days,
                                          max_baseline=True)
    stats_daily = analyze.collect_stats(daily_targets, max_baseline=True)

    # stat_plot_compare(stats_monthly, stats_daily)
    stat_plot_intervals(stats_monthly, f'{site} - Monthly Optimization',
                        x='timestamp',
                        y='offset_normalized',
                        c='temperature_max')
    stat_plot_intervals(stats_daily, f'{site} - Daily Optimization',
                        x='timestamp',
                        y='offset_normalized',
                        c='temperature_max')
    stat_plot_intervals(stats_monthly, f'{site} - Monthly Optimization',
                        x='baseline_load',
                        y='offset_normalized',
                        c='temperature_max')
    stat_plot_intervals(stats_daily, f'{site} - Daily Optimization',
                        x='baseline_load',
                        y='offset_normalized',
                        c='temperature_max')
    plt.show()

    ########################################
    # Match Monthly Run Days to Daily Runs #
    ########################################
    monthly_run_days = analyze.find_daily_monthly_days(daily_targets,
                                                       stats_daily,
                                                       monthly_targets_days,
                                                       stats_monthly)

# for day_targets, day_stats, month_targets, month_stats, in monthly_run_days:
#     lt_plot(day_targets)
#     lt_plot(month_targets)
#     plt.show()
