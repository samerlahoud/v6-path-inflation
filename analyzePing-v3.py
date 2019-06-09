'''
This version of ping analysis combines all RTT values from each measurement file and from each measurement campaign.
The final results include two RTT lists (v4 and v6) for each probe
'''

import json
import glob
from pathlib import Path
from ripe.atlas.sagan import PingResult
import numpy as np
import sys
import matplotlib.pyplot as plt
from collections import defaultdict

def get_rtt_stat(msm_file):
    med_rtt_list = []
    max_rtt_list = []
    min_rtt_list = []
    with open(msm_file, 'r') as f:
        results = json.load(f)
        for result in results:
            parsed_result = PingResult.get(result)
            med_rtt = parsed_result.rtt_median
            max_rtt = parsed_result.rtt_max
            min_rtt = parsed_result.rtt_min
            if(med_rtt != None):
                med_rtt_list.append(med_rtt)
                max_rtt_list.append(max_rtt)
                min_rtt_list.append(min_rtt)
    if(med_rtt_list):
        return med_rtt_list, max_rtt_list, min_rtt_list
    else:
        return None, None, None

def init_stat(country_code):
    for time_folder in data_folder.glob('data-*/'):
        for probe_folder in time_folder.glob('*[0-9]'):
            probe_id = probe_folder.parts[-1]
            rtt_stat_dict[probe_id] = defaultdict()
            if (country_code and int(probe_id) not in probes[country_code]):
                continue
            for msm_dest in msm_id_list[0].keys():
                rtt_stat_dict[probe_id][msm_dest] = defaultdict()
                rtt_stat_dict[probe_id][msm_dest]['med'] = []
                rtt_stat_dict[probe_id][msm_dest]['max'] = []
                rtt_stat_dict[probe_id][msm_dest]['min'] = []

def get_stat(country_code):
    init_stat(country_code)
    for time_folder in data_folder.glob('data-*/'):
        for probe_folder in time_folder.glob('*[0-9]'):
            probe_id = probe_folder.parts[-1]
            if (country_code and int(probe_id) not in probes[country_code]):
                continue
            for msm_dest in msm_id_list[0].keys():
                for msm_id in msm_id_list[0][msm_dest]:
                    msm_file = '{}/{}.json'.format(probe_folder,msm_id)
                    if Path(msm_file).is_file():
                        med_rtt, max_rtt, min_rtt = get_rtt_stat(msm_file)
                        rtt_stat_dict[probe_id][msm_dest]['med'].append(med_rtt)
                        rtt_stat_dict[probe_id][msm_dest]['max'].append(max_rtt)
                        rtt_stat_dict[probe_id][msm_dest]['min'].append(min_rtt)
                    else:
                        rtt_stat_dict[probe_id][msm_dest]['med'].append(None)
                        rtt_stat_dict[probe_id][msm_dest]['max'].append(None)
                        rtt_stat_dict[probe_id][msm_dest]['min'].append(None)

def compute_stat_list(stat_value):
    rtt_dlist = [t[stat_value] for k in rtt_stat_dict.values() 
                    for t in k.values() if t[stat_value][0] != None and t[stat_value][1] != None]
 
    rtt_v4 = list(zip(*rtt_dlist))[0]
    rtt_v6 = list(zip(*rtt_dlist))[1]
    rtt_v4_list = [item for sublist in rtt_v4 for item in sublist]
    rtt_v6_list = [item for sublist in rtt_v6 for item in sublist]
    rtt_diff_list = [x-y for (x,y) in zip(rtt_v4_list,rtt_v6_list)]
    return rtt_v4_list, rtt_v6_list, rtt_diff_list

def cdf_plot(rtt_v4, rtt_v6, stat_type):
    n_bins = 100000
    fig, ax = plt.subplots(figsize=(8, 6))
    # plot the cumulative histogram

    counts, bin_edges = np.histogram(rtt_v4, bins=n_bins)
    cdf = np.cumsum(counts)
    ax.plot(bin_edges[1:], cdf/cdf[-1])

    counts, bin_edges = np.histogram(rtt_v6, bins=n_bins)
    cdf = np.cumsum(counts)
    ax.plot(bin_edges[1:], cdf/cdf[-1])

    # tidy up the figure
    ax.grid(True)
    #ax.legend(loc='right')
    ax.set_xlabel('RTT {} (msec)'.format(stat_type))
    ax.legend(['IPv4', 'IPv6'])
    ax.set_ylabel('CDF')
    #ax.set_xlim(0,400)
    ax.set_xscale('log')

    plt.savefig('{}/rtt-{}-cdf.eps'.format(result_folder, stat_type))

def hist_plot(rtt, stat_type):
    num_bins = 20
    fig, ax = plt.subplots()

    # the histogram of the data
    n, bins, patches = ax.hist(rtt, num_bins, density=1)
    ax.set_ylabel('Probability density')
    ax.set_xlabel('RTT {} (msec)'.format(stat_type))
    ax.grid(True)
    # Tweak spacing to prevent clipping of ylabel
    fig.tight_layout()
    plt.savefig('{}/rtt-{}-hist.eps'.format(result_folder, stat_type))

def diag_plot(rtt_v4, rtt_v6):
    fig, ax = plt.subplots(figsize=(8, 6))
    plt.plot(rtt_v6,rtt_v4,'x')
    ax.set_xlabel('IPv6 RTT (msec)')
    ax.set_ylabel('IPv4 RTT (msec)')
    # ax.set_ylim([0,400])
    # ax.set_xlim([0,400])
    plt.show()

if __name__ == "__main__":
    with open('builtin_msm_id.json', 'r') as f:
        msm_id_list = json.load(f)

    with open('probes.json', 'r') as f:
        probes = json.load(f)

    if(len(sys.argv)>=2):
        country_code = str(sys.argv[1])
    else:
        country_code = None

    data_folder = Path('./')
    result_folder = './results'
    rtt_stat_dict = {}
    get_stat(country_code)
    
    with open("results/rtt_stat_dict.json", "w") as f:
        json.dump(rtt_stat_dict, f, indent=4, sort_keys=True)
   
    med_rtt_v4, med_rtt_v6, med_rtt_diff = compute_stat_list('med')
    max_rtt_v4, max_rtt_v6, max_rtt_diff = compute_stat_list('max')
    min_rtt_v4, min_rtt_v6, min_rtt_diff = compute_stat_list('min')

    cdf_plot(max_rtt_v4, max_rtt_v6, 'maximum')
    cdf_plot(med_rtt_v4, med_rtt_v6, 'median')
    cdf_plot(min_rtt_v4, min_rtt_v6, 'minimum')

    hist_plot(min_rtt_diff, 'minimum')
