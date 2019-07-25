import matplotlib.pyplot as plt
import numpy as np
from analyze import flatten_stat_data
from sklearn.preprocessing import normalize
import analyze
import pandas as pd


def lt_plot(site, data, t1=None, t2=None, max_peak=None):
    if t1 is None:
        t1 = data.index[0]
    if t2 is None:
        t2 = data.index[-1]

    fig, ax = plt.subplots(figsize=(14, 8))
    plt.title(f"LT Optimization for {site}")

    # plotting power related graphs on first y axis
    ln1 = ax.plot(data.offsets[t1:t2],
                  label="Offset")
    ln2 = ax.plot(data.baseline[t1:t2],
                  label='Building Power')
    ln3 = ax.plot(data.load_values[t1:t2],
                  label='New Building Power')
    ln4 = ax.plot(-data.charge_limits[t1:t2],
                  label='Max Charge Values')
    ln5 = ax.plot(data.discharge_limits[t1:t2],
                  label='Max Discharge Values')
    ln7 = ax.plot(data.temperature[t1:t2],
                  label='Temperature')

    ax.set_xlabel('Time period')
    ax.set_ylabel('Power in KW')

    start, end = ax.get_xlim()
    # ax.set_xticks(np.arange(start, end, 8))
    # ax.set_xticklabels(sv)
    # plt.xticks(np.arange(start+33.55, end+33.55, 16), sv, rotation=90);

    # creating second y axis and plotting SOC
    ax2 = ax.twinx()
    ln6 = ax2.plot(data.soc[t1:t2], '--',
                   label="SOC")

    ax2.set_ylabel('State of charge in KWhe')

    ax.axhline(0, color='black')

    # Managing labels and legend
    lns = ln1 + ln2 + ln3 + ln4 + ln5 + ln6 + ln7
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, loc='best')
    if max_peak:
        ax2.set_ylim(-14, max_peak)
    return ax


def peak_plot(target, peaks, properties, max_peak=None):
    x = target['soc']
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.plot(x.values)
    ax.plot(peaks, x.iloc[peaks], "x")

    left_bases = properties['left_bases']
    ax.plot(left_bases, x.iloc[left_bases], "x", color="green")
    right_bases = properties['right_bases']
    ax.plot(right_bases, x.iloc[right_bases], "x", color="red")
    ax.vlines(x=peaks, ymin=x.iloc[peaks] - properties["prominences"],
              ymax=x.iloc[peaks], color="C1")
    ax.hlines(y=properties["width_heights"], xmin=properties["left_ips"],
              xmax=properties["right_ips"], color="C1")
    if max_peak:
        ax.set_ylim(-14, max_peak)
    return ax


def stat_plot(stats, label=None):
    ax = setup_stat_plot()
    peak_stat_data = flatten_stat_data(stats)
    get_stat_plot(ax, peak_stat_data,
                  x='baseline_peak_load',
                  y='offset_normalized',
                  s='temperature_avg',
                  c='temperature_max')
    if label:
        ax.set_title(label)
    return ax


def stat_plot_intervals(stats, label=None, **kwargs):
    ax = setup_stat_plot()
    peak_stat_data = flatten_stat_data(stats, by='intervals')
    get_stat_plot(ax, peak_stat_data, **kwargs)
    if label:
        ax.set_title(label)
    return ax


def stat_plot_compare(stats_monthly, stats_daily):
    ax = setup_stat_plot()

    colors = ['green', 'red']
    for i, stats in enumerate((stats_monthly, stats_daily)):
        peak_stat_data = flatten_stat_data(stats)
        get_stat_plot(ax, peak_stat_data,
                      x='baseline_peak_load',
                      y='offset_normalized',
                      s='temperature_max',
                      c=colors[i])
    ax.legend(['Monthly', 'Daily'])
    return ax


def setup_stat_plot():
    fig, ax = plt.subplots(figsize=(14, 8))
    return ax


def get_stat_plot(ax, peak_stat_data, x='', y='',
                  c=None, s=None, marker='o'):
    def stat(name):
        return [stats[name] for stats in peak_stat_data]

    try:
        ax.set_xlabel(feature_display_settings[x]['axis_label'])
        ax.set_xlim(*feature_display_settings[x]['limits'])
    except KeyError:
        pass
    x = stat(x)
    try:
        ax.set_ylabel(feature_display_settings[y]['axis_label'])
        ax.set_ylim(*feature_display_settings[y]['limits'])
    except KeyError:
        pass
    y = stat(y)
    try:
        c = stat(c)
    except KeyError:
        pass
    if not s:
        s = 30
    elif not isinstance(s, int):
        s = normalize(np.array(stat(s)).reshape(1, -1)) * 500
    ax.scatter(x=x, y=y, c=c, s=s, marker=marker)
    return ax


def single_day_analysis(site, targets, date):
    if isinstance(date, str):
        date = pd.to_datetime(date).date()
    max_peak = max([max(t['soc']) for t in targets])
    for target in targets:
        if target.index[0].date() == date:
            cur = target
            break
    # cur = targets[id]
    ax = lt_plot(site, cur, max_peak=max_peak)
    plt.show()
    peaks, properties = analyze.find_target_peaks(cur)
    ax2 = peak_plot(cur, peaks, properties, max_peak=max_peak)
    plt.show()


feature_display_settings = {
    'timestamp': {
        'limits': (0, 24 * 60),
        'axis_label': 'Timestamp in Minutes'
    },
    'temperature_max': {
        'limits': (0, 100),
        'axis_label': 'Maximum Temperature (F)'
    },
    'temperature_avg': {
        'limits': (0, 100),
        'axis_label': 'Average Temperature (F)'
    },
    'baseline_peak_soc': {
        'limits': (0, 700),
        'axis_label': 'Max Baseline SoC'
    },
    'target_peak_soc': {
        'limits': (0, 700),
        'axis_label': 'Max Target SoC (Threshold)'
    },
    'baseline_load': {
        # 'limits': (0, 1000),
        'axis_label': 'Current Baseline Load (kW)'
    },
    'offset': {
        'limits': (-60, 60),
        'axis_label': 'Offset'
    },
    'offset_normalized': {
        'limits': (-1.1, 1.1),
        'axis_label': 'Offset (Normalized)'
    },
    'charge_start_time': {
        'limits': (0, 24 * 60),
        'axis_label': 'Charge Start Time in Minutes'
    },
    'peak_soc_time': {
        'limits': (0, 24 * 60),
        'axis_label': 'Time of Peak SoC in Minutes'
    },
    'discharge_end_time': {
        'limits': (0, 24 * 60),
        'axis_label': 'Discharge End Time in Minutes'
    },
}
