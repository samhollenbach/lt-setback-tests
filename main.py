import os
import matplotlib.pyplot as plt
from pprint import pprint
import pandas as pd
from pickle_jar import pickle_jar
import load
import savings
from display import lt_plot, peak_plot, stat_plot, stat_plot_intervals, \
    stat_plot_compare, single_day_analysis
import analyze

#####################
# Initialize Script #
#####################


non_solar_sites = ['WM3138', 'WM3708', 'WM5606', 'WM5859', 'WM4132']
solar_sites = ['WM3140', 'WM3796', 'WM5603', 'WM5635', 'WFSTC']

solar = True

label = 'Solar' if solar else 'Non-Solar'

solar_stats_daily = []
solar_stats_monthly = []
solar_stats_monthly_months = []
non_solar_stats_daily = []
non_solar_stats_monthly = []
non_solar_stats_monthly_months = []

if solar:
    sites = solar_sites[:]
else:
    sites = non_solar_sites[:]

for site in sites[-1:]:
    start = "2018-06-01 00:00:00-07"
    end = "2019-05-31 23:45:00-07"
    if site == 'WFSTC':
        start = "2019-06-01 00:00:00-07"
        end = "2019-07-21 23:45:00-07"

    # power_file = 'input/WFROS_timeseries_filled.csv'
    print(f'Running site {site}')
    path = 'input/'
    power_file = [os.path.join(path, i) for i in os.listdir(path) if
                  os.path.isfile(os.path.join(path, i)) and
                  site in i][0]

    if site.startswith('WF'):
        config_file = 'input/WF_LTSB_mass_and_SST.csv'
    elif site.startswith('WM'):
        config_file = 'input/WM_LTSB_mass_and_SST_new.csv'
    else:
        print(f"Can't find proper config file for {site}")
        continue

    power_data, master_conf = load.load_data(site,
                                             start,
                                             end,
                                             power_file,
                                             config_file)
    master_conf['optimize_energy'] = False

    #############################
    # Get Monthly/Daily Targets #
    #############################
    monthly_targets_days, daily_targets = load.get_monthly_daily_targets(
        power_data,
        master_conf)

    monthly_targets = load.get_monthly_targets(power_data, master_conf)
    # print(list(monthly_targets_days[0].columns))
    # for i in range(156, 220):

    ###########################
    # Get Monthly/Daily Stats #
    ###########################
    print(f"Calculating Statistics for site {site}\n ")
    stats_monthly = analyze.collect_stats(site, monthly_targets_days,
                                          max_baseline=True)
    # stats_monthly = []
    stats_daily = analyze.collect_stats(site, daily_targets, max_baseline=True)
    # stats_daily = []
    stats_monthly_months = analyze.collect_stats(site, monthly_targets,
                                                 max_baseline=True)

    stats_monthly_months_flat = analyze.flatten_stat_data(stats_monthly_months,
                                                          timestamp_to_min=False,
                                                          by='intervals')

    #####################
    # Identify Key Days #
    #####################

    key_stat_intervals = []
    for stat_interval in stats_monthly_months_flat:
        # pprint(stat_interval)

        single_day_analysis(site,
                            monthly_targets_days,
                            '2019-06-11')

        # summer_months = [5, 6, 7, 8, 9, 10]
        #         # if stat_interval['timestamp'].month not in summer_months:
        #         #     continue
        pprint(stat_interval)
        if stat_interval['baseline_load'] >= 275:
            pprint(stat_interval)
        # offset_noramlized = stat_interval['offset'] / stat_interval[
        #     'discharge_limit']
        # if offset_noramlized < 0.999 and stat_interval[
        #     'baseline_load'] >= 200:
        #     pprint(stat_interval)
        #     print(offset_noramlized)
        #     key_stat_intervals.append(stat_interval)
        # single_day_analysis(site,
        #                     monthly_targets_days,
        #                     stat_interval['timestamp'].date())

    ###########################
    # Add Data To Site Groups #
    ###########################
    if solar:
        solar_stats_monthly.append(stats_monthly)
        solar_stats_daily.append(stats_daily)
        solar_stats_monthly_months.append(stats_monthly_months)

    else:
        non_solar_stats_monthly.append(stats_monthly)
        non_solar_stats_daily.append(stats_daily)
        non_solar_stats_monthly_months.append(stats_monthly_months)

    ###################
    # Show Site Plots #
    ###################
    # show_plots = (site == 'WFSTC')
    show_plots = False

    if show_plots:
        # stat_plot_compare(stats_monthly, stats_daily)
        # stat_plot_intervals(stats_monthly, f'{site} - Monthly Optimization',
        #                     x='timestamp',
        #                     y='offset_normalized',
        #                     c='temperature_max')
        # stat_plot_intervals(stats_daily, f'{site} - Daily Optimization',
        #                     x='timestamp',
        #                     y='offset_normalized',
        #                     c='temperature_max')
        # stat_plot_intervals(stats_monthly, f'{site} - Monthly Optimization',
        #                     x='baseline_load',
        #                     y='offset_normalized',
        #                     c='temperature_max')
        # stat_plot_intervals(stats_daily, f'{site} - Daily Optimization',
        #                     x='baseline_load',
        #                     y='offset_normalized',
        #                     c='temperature_max')
        stat_plot_intervals(stats_monthly_months,
                            f'Solar Sites - Max Baseline for Month',
                            x='timestamp',
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
    # for day_targets, day_stats, month_targets, month_stats, \
    #         in monthly_run_days:
    #     # lt_plot(day_targets)
    #     print('test')
    #     lt_plot(site, month_targets)
    #     plt.show()

    # if site == 'WM3140':
    #     for month_target in monthly_targets:
    #         lt_plot(site, month_target)
    #         plt.show()

    ##################
    # Savings Tables #
    ##################
    savings = savings.generate_savings_table(monthly_targets, master_conf)
    pprint(savings)

show_plots_all = False
if show_plots_all:
    if solar:
        smonthly = [stats_month for stats_monthly in solar_stats_monthly
                    for stats_month in stats_monthly]
        sdaily = [stats_day for stats_daily in solar_stats_daily
                  for stats_day in stats_daily]
        smonthly_months = [stats_month for stats_monthly in
                           solar_stats_monthly_months
                           for stats_month in stats_monthly]
    else:
        smonthly = [stats_month for stats_monthly in non_solar_stats_monthly
                    for stats_month in stats_monthly]
        sdaily = [stats_day for stats_daily in non_solar_stats_daily
                  for stats_day in stats_daily]
        smonthly_months = [stats_month for stats_monthly in
                           non_solar_stats_monthly_months
                           for stats_month in stats_monthly]

    stat_plot_intervals(smonthly,
                        f'{label} Sites - Monthly Optimization',
                        x='timestamp',
                        y='offset_normalized',
                        c='temperature_max')
    stat_plot_intervals(sdaily,
                        f'{label} Sites - Daily Optimization',
                        x='timestamp',
                        y='offset_normalized',
                        c='temperature_max')
    stat_plot_intervals(smonthly,
                        f'{label} Sites - Monthly Optimization',
                        x='baseline_load',
                        y='offset_normalized',
                        c='temperature_max')
    stat_plot_intervals(sdaily,
                        f'{label} Sites - Daily Optimization',
                        x='baseline_load',
                        y='offset_normalized',
                        c='temperature_max')
    stat_plot_intervals(smonthly_months,
                        f'{label} Sites - Max Baseline for Summer Month',
                        x='baseline_load',
                        y='offset_normalized',
                        c='temperature_max')
    stat_plot_intervals(smonthly_months,
                        f'{label} Sites - Max Baseline for Summer Month',
                        x='timestamp',
                        y='offset_normalized',
                        c='temperature_max')
    plt.show()
