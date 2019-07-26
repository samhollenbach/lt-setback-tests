import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import datetime
from tariff import Tariff


def collect_stats(site, target_set, peaks=True, intervals=False,
                  max_baseline=False):
    stat_set = []
    max_peak = max([max(t['soc']) for t in target_set])
    for target in target_set:
        tariff = Tariff('pge')
        target = tariff.apply_period(load=target)
        stat_set.append(
            get_target_stats(site, target, peaks=peaks, intervals=intervals,
                             max_baseline=max_baseline,
                             max_peak=max_peak))
    return stat_set


def get_target_stats(site, target, peaks=True, intervals=False,
                     max_baseline=False, max_peak=None):
    target_stats = {
        'site': site,
        **feature_base_stats(target, 'temperature')
    }
    if peaks:
        target_stats = {**target_stats,
                        **peak_stats(target, max_peak=max_peak)}
    if intervals:
        target_stats = {**target_stats,
                        **interval_stats(target, max_peak=max_peak)}
    if max_baseline:
        target_stats = {**target_stats,
                        **max_baseline_stats(target)}
    return target_stats


def feature_base_stats(target, feature):
    return {
        f'{feature}_max': max(target[feature]),
        f'{feature}_min': min(target[feature]),
        f'{feature}_avg': sum(target[feature]) / len(target[feature]),
        f'{feature}_range': (max(target[feature]) - min(target[feature]))
    }


def find_target_peaks(target, prominence=10, distance=12, width=8,
                      height=None,
                      height_factor=0.3):
    soc = target['soc']

    # for timestamp, interval in target.iterrows():
    # print(interval)

    if not height:
        height = max(soc) * height_factor
    peaks, properties = find_peaks(soc, prominence=prominence,
                                   distance=distance, width=width,
                                   height=height)
    return peaks, properties


def peak_stats(target, max_peak=None):
    soc = target['soc']
    old_power = target['baseline']
    new_power = target['load_values']

    height_threshold = (max_peak * 0.0) if max_peak else None
    peaks, properties = find_target_peaks(target, height=height_threshold)

    peak_results = []
    for i, p in enumerate(peaks):
        left_base = properties['left_bases'][i]
        right_base = properties['right_bases'][i]
        max_old_load = max(old_power.iloc[left_base:right_base])
        max_new_load = max(new_power.iloc[left_base:right_base])
        peak_charge_limit = target['charge_limits'].iloc[p]
        peak_discharge_limit = target['discharge_limits'].iloc[p]
        offset = target['offsets'].iloc[p]
        offset_normalized = offset / peak_discharge_limit
        peak_vals = soc.iloc[left_base:right_base]
        peak_auc = sum(peak_vals)
        peak = {
            'peak_soc': soc.iloc[p],
            'peak_soc_time': target.iloc[p].name,
            'charge_start_time': target.iloc[left_base].name,
            'discharge_end_time': target.iloc[right_base].name,
            'charge_limit': peak_charge_limit,
            'discharge_limit': peak_discharge_limit,
            'offset': offset,
            'offset_normalized': offset_normalized,
            'peak_soc_auc': peak_auc,
            'baseline_peak_load': max_old_load,
            'target_peak_load': max_new_load,
        }
        peak_results.append(peak)

    return {'peaks': peak_results}


def max_baseline_stats(target):
    if 'On-Peak' in target['period'].unique():
        on_peak_target = target[target['period'] == 'On-Peak']
    else:
        on_peak_target = target
    interval = on_peak_target.loc[on_peak_target['baseline'].idxmax()]
    if not interval['offsets'] and not interval['soc']:
        return {'intervals': []}

    inter = {
        'timestamp': interval.name,
        'baseline_load': interval['baseline'],
        'target_load': interval['load_values'],
        'soc': interval['soc'],
        'charge_limit': interval['charge_limits'],
        'discharge_limit': interval['discharge_limits'],
        'offset': interval['offsets'],
        'offset_normalized': interval['offsets'] / interval[
            'discharge_limits'],
        'temperature': interval['temperature'],
        'period': interval['period']
    }

    return {'intervals': [inter]}


def interval_stats(target, max_peak=None):
    height_threshold = (max_peak * 0.2) if max_peak else None
    peaks, properties = find_target_peaks(target, height=height_threshold)
    max_interval_timestamp = target.loc[target['baseline'].idxmax()].name
    interval_results = []
    for i, p in enumerate(peaks):
        left_base = properties['left_bases'][i]
        right_base = properties['right_bases'][i]
        target_period = target.iloc[left_base:right_base]
        for timestamp, interval in target_period.iterrows():
            if timestamp != max_interval_timestamp:
                continue
            if not interval['discharge_limits']:
                continue

            inter = {
                'timestamp': timestamp,
                'baseline_load': interval['baseline'],
                'target_load': interval['baseline'],
                'soc': interval['soc'],
                'charge_limit': interval['charge_limits'],
                'discharge_limit': interval['discharge_limits'],
                'offset': interval['offsets'],
                'offset_normalized': interval['offsets'] / interval[
                    'discharge_limits'],
                'temperature': interval['temperature']
            }
            interval_results.append(inter)
    return {'intervals': interval_results}


def flatten_stat_data(stats, timestamp_to_min=True, by='peaks'):
    def to_mins(timestamp):
        if not timestamp_to_min or not isinstance(timestamp,
                                                  datetime.datetime):
            return timestamp
        return (timestamp.hour * 60 + timestamp.minute)

    stat_data = []
    for stat_day in stats:
        for frame in stat_day[by]:
            stats = {
                **{k: v for k, v in stat_day.items() if
                   k is not by},
                **{k: to_mins(v) for k, v in frame.items()},

            }
            stat_data.append(stats)
    return stat_data


def find_daily_monthly_days(daily_targets, daily_stats, monthly_targets,
                            monthly_stats):
    keep_targets = []
    for day_targets, day_stats, monthly_day_targets, monthly_day_stats \
            in zip(
        daily_targets,
        daily_stats,
        monthly_targets,
        monthly_stats):
        if monthly_day_stats['peaks']:
            keep_targets.append(
                (day_targets, day_stats, monthly_day_targets,
                 monthly_day_stats))
    return keep_targets
