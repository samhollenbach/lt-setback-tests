import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np
import datetime
from sklearn.preprocessing import normalize


def lt_plot(data, t1=None, t2=None, max_peak=None):
    if t1 is None:
        t1 = data.index[0]
    if t2 is None:
        t2 = data.index[-1]

    fig, ax = plt.subplots(figsize=(14, 8))
    plt.title("LT Optimization for WM1554 Rack A")

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


def stat_plot(stats):
    fig, ax = plt.subplots(figsize=(14, 8))
    peak_stat_data = []

    def stat(name):
        return [stats[name] for stats in peak_stat_data]

    peak_stat_data = get_peak_stat_data(stats)

    x = stat('peak_time')
    x2 = stat('charge_start')
    y = stat('temp_avg')
    y2 = stat('temp_max')
    y3 = stat('peak_auc')
    y4 = stat('peak')

    s = normalize(np.array(y4).reshape(1, -1)) * 500

    # ax.scatter(x, y, c=c)
    ax.scatter(x2, y, s=s, marker='x', c=y2)
    ax.set_xlabel('Time of day in minutes')
    ax.set_ylabel('Temperature (F)')
    ax.set_xlim(0, 24 * 60)
    ax.set_ylim(0, 100)
    return ax


def stat_plot_compare(stats_monthly, stats_daily):
    fig, ax = plt.subplots(figsize=(14, 8))

    peak_stat_data = []

    def stat(name):
        return [stats[name] for stats in peak_stat_data]

    colors = ['green', 'red']
    # ax.scatter(x2, y, marker='x', c=c)
    ax.set_xlabel('Time of day in minutes')
    ax.set_ylabel('Temperature (F)')
    ax.set_xlim(0, 24 * 60)
    ax.set_ylim(0, 100)
    for i, stats in enumerate((stats_monthly, stats_daily)):
        peak_stat_data = get_peak_stat_data(stats)
        x = stat('peak_time')
        x2 = stat('charge_start')
        x3 = stat('discharge_end')
        y = stat('temp_avg')
        y2 = stat('temp_avg')
        y3 = stat('peak_auc')
        y4 = stat('peak')

        s = normalize(np.array(y4).reshape(1, -1)) * 500

        ax.scatter(x2, y, s=s, c=colors[i], alpha=0.6)
    ax.legend(['Monthly', 'Daily'])
    return ax


def get_peak_stat_data(stats):
    peak_stat_data = []

    def to_mins(timestamp):
        if not isinstance(timestamp, datetime.datetime):
            return timestamp
        return (timestamp.hour * 60 + timestamp.minute)

    for stat_day in stats:
        temp_avg = stat_day['temperature_avg']
        temp_max = stat_day['temperature_max']
        for peak in stat_day['peaks']:
            peak_stat_fields = ['peak_time', 'charge_start',
                                'discharge_end',
                                'peak_auc', 'peak']
            stats = {
                'temp_max': temp_max,
                'temp_avg': temp_avg,
                **{k: to_mins(v) for k, v in peak.items() if
                   k in peak_stat_fields}
            }
            peak_stat_data.append(stats)
    return peak_stat_data
