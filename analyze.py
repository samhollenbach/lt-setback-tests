import sklearn.cluster
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import pylab


def collect_stats(target_set):
    stat_set = []
    max_peak = max([max(t['soc']) for t in target_set])
    for target in target_set:
        stat_set.append(get_target_stats(target, max_peak=max_peak))
    return stat_set


def get_target_stats(target, max_peak=None):
    return {
        **feature_base_stats(target, 'temperature'),
        # **feature_base_stats(target, 'soc'),
        **peak_stats(target, max_peak=max_peak)
    }


def peak_stats(target, max_peak=None):
    soc = target['soc']
    old_power = target['baseline']
    new_power = target['load_values']
    max_old_load = max(old_power)
    max_new_load = max(new_power)
    peak_clip = max_old_load - max_new_load

    height_threshold = (max_peak * 0.4) if max_peak else None
    peaks, properties = find_target_peaks(target, height=height_threshold)

    peak_results = []
    for i, p in enumerate(peaks):
        left_base = properties['left_bases'][i]
        right_base = properties['right_bases'][i]

        peak_vals = soc.iloc[left_base:right_base]
        peak_auc = sum(peak_vals)
        peak = {
            'peak': soc.iloc[p],
            'peak_time': target.iloc[p].name,
            'charge_start': target.iloc[left_base].name,
            'discharge_end': target.iloc[right_base].name,
            'peak_auc': peak_auc
        }
        peak_results.append(peak)

    return {'max_baseline': max_old_load,
            'max_target': max_new_load,
            'peak_clip': peak_clip,
            'peaks': peak_results}


def feature_base_stats(target, feature):
    return {
        f'{feature}_max': max(target[feature]),
        f'{feature}_min': min(target[feature]),
        f'{feature}_range': (max(target[feature]) - min(target[feature]))
    }


def find_target_peaks(target, prominence=5, distance=18, width=6, height=None,
                      height_factor=0.5):
    soc = target['soc']

    if not height:
        height = max(soc) * height_factor
    peaks, properties = find_peaks(soc, prominence=prominence,
                                   distance=distance, width=width,
                                   height=height)
    return peaks, properties
