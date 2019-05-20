import json
import glob
from pathlib import Path
from ripe.atlas.sagan import TracerouteResult
import numpy as np
import re
import matplotlib.pyplot as plt
from collections import defaultdict

with open('builtin_msm_id.json', 'r') as f:
    msm_id_list = json.load(f)

def get_trace_stat(msm_file):
    nb_hops_list = []
    with open(msm_file, 'r') as f:
        results = json.load(f)
        for result in results:
            parsed_result = TracerouteResult.get(result)
            nb_hops = parsed_result.total_hops
            if(nb_hops != None and parsed_result.is_success):
                nb_hops_list.append(nb_hops)
    if(nb_hops_list):
        return np.median(nb_hops_list), np.max(nb_hops_list), np.min(nb_hops_list)
    else:
        return None, None, None

data_folder = Path('data/')
trace_stat_dict = {}

for probe_folder in data_folder.iterdir():
    probe_id = probe_folder.parts[-1]
    trace_stat_dict[probe_id] = defaultdict()

    for msm_dest in msm_id_list[1].keys():
        trace_stat_dict[probe_id][msm_dest] = defaultdict()
        trace_stat_dict[probe_id][msm_dest]['max_hops'] = []
        trace_stat_dict[probe_id][msm_dest]['min_hops'] = []
        trace_stat_dict[probe_id][msm_dest]['med_hops'] = []
        for msm_id in msm_id_list[1][msm_dest]:
            msm_file = '{}/{}.json'.format(probe_folder,msm_id)
            if Path(msm_file).is_file():
                med_hops, max_hops, min_hops = get_trace_stat(msm_file)
                trace_stat_dict[probe_id][msm_dest]['max_hops'].append(max_hops)
                trace_stat_dict[probe_id][msm_dest]['min_hops'].append(min_hops)
                trace_stat_dict[probe_id][msm_dest]['med_hops'].append(med_hops)
            else:
                trace_stat_dict[probe_id][msm_dest]['max_hops'].append(None)
                trace_stat_dict[probe_id][msm_dest]['min_hops'].append(None)
                trace_stat_dict[probe_id][msm_dest]['med_hops'].append(None)

print(trace_stat_dict)
# with open("results/trace_stat_dict.json", "w") as f:
#     json.dump(trace_stat_dict, f, indent=4, sort_keys=True)

def compute_stat_list(stat_value):
    nb_hops_dlist = [t[stat_value] for k in trace_stat_dict.values() for t in k.values() if t[stat_value][0] != None and t[stat_value][1] != None]
 
    nb_hops_v4 = list(zip(*nb_hops_dlist))[0]
    nb_hops_v6 = list(zip(*nb_hops_dlist))[1]
    nb_hops_diff = [x-y for (x,y) in zip(nb_hops_v4,nb_hops_v6)]
    return nb_hops_v4, nb_hops_v6, nb_hops_diff

max_nb_hops_v4, max_nb_hops_v6, max_nb_hops_diff = compute_stat_list('max_hops')
min_nb_hops_v4, min_nb_hops_v6, min_nb_hops_diff = compute_stat_list('min_hops')
med_nb_hops_v4, med_nb_hops_v6, med_nb_hops_diff = compute_stat_list('med_hops')

def cdf_plot(hop_diff):
    n_bins = 100000
    fig, ax = plt.subplots(figsize=(8, 6))
    # plot the cumulative histogram

    counts, bin_edges = np.histogram(hop_diff, bins=n_bins)
    cdf = np.cumsum(counts)
    ax.plot(bin_edges[1:], cdf/cdf[-1])

    # tidy up the figure
    ax.grid(True)
    #ax.legend(loc='right')
    ax.set_xlabel('Hop difference between IPv4 and IPv6')
    ax.set_ylabel('CDF')
    #ax.set_xscale('log')

    plt.show()

cdf_plot(max_nb_hops_diff)
cdf_plot(min_nb_hops_diff)
cdf_plot(med_nb_hops_diff)

def diag_plot(hop_v4, hop_v6):
    fig, ax = plt.subplots(figsize=(8, 6))
    plt.plot(hop_v6,hop_v4,'x')
    ax.set_xlabel('IPv6 Hop')
    ax.set_ylabel('IPv4 Hop')
    # ax.set_ylim([0,400])
    # ax.set_xlim([0,400])
    plt.show()

diag_plot(med_nb_hops_v4, med_nb_hops_v6)
diag_plot(max_nb_hops_v4, max_nb_hops_v6)
diag_plot(min_nb_hops_v4, min_nb_hops_v6)
