import json
import glob
from pathlib import Path
from ripe.atlas.sagan import TracerouteResult
import numpy as np
import sys
import matplotlib.pyplot as plt
from collections import defaultdict
import seaborn as sns

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
        return nb_hops_list
    else:
        return None

def init_stat(country_code):
    for time_folder in data_folder.glob('data-*/'):
        for probe_folder in time_folder.glob('*[0-9]'):
            probe_id = probe_folder.parts[-1]
            trace_stat_dict[probe_id] = defaultdict()
            if (country_code and int(probe_id) not in probes[country_code]):
                continue
            for msm_dest in msm_id_list[1].keys():
                trace_stat_dict[probe_id][msm_dest] = defaultdict()
                trace_stat_dict[probe_id][msm_dest]['nb_hops'] = []

def get_stat(country_code):
    init_stat(country_code)
    for time_folder in data_folder.glob('data-*/'):
        for probe_folder in time_folder.glob('*[0-9]'):
            probe_id = probe_folder.parts[-1]
            if (country_code and int(probe_id) not in probes[country_code]):
                continue
            for msm_dest in msm_id_list[1].keys():
                for msm_id in msm_id_list[1][msm_dest]:
                    msm_file = '{}/{}.json'.format(probe_folder,msm_id)
                    if Path(msm_file).is_file():
                        nb_hops = get_trace_stat(msm_file)
                        trace_stat_dict[probe_id][msm_dest]['nb_hops'].append(nb_hops)
                    else:
                        trace_stat_dict[probe_id][msm_dest]['nb_hops'].append(None)

def compute_stat_list(stat_value):
    nb_hops_dlist = [t[stat_value] for k in trace_stat_dict.values() 
                    for t in k.values() if t[stat_value][0] != None and t[stat_value][1] != None]
 
    nb_hops_v4 = list(zip(*nb_hops_dlist))[0]
    nb_hops_v6 = list(zip(*nb_hops_dlist))[1]
    nb_hops_v4_list = [item for sublist in nb_hops_v4 for item in sublist]
    nb_hops_v6_list = [item for sublist in nb_hops_v6 for item in sublist]
    nb_hops_diff_list = [x-y for (x,y) in zip(nb_hops_v4_list,nb_hops_v6_list)]
    return nb_hops_v4_list, nb_hops_v6_list, nb_hops_diff_list

def cdf_plot(nb_hops_v4, nb_hops_v6):
    n_bins = 100000
    fig, ax = plt.subplots(figsize=(8, 6))
    # plot the cumulative histogram

    counts, bin_edges = np.histogram(nb_hops_v4, bins=n_bins)
    cdf = np.cumsum(counts)
    ax.plot(bin_edges[1:], cdf/cdf[-1])

    counts, bin_edges = np.histogram(nb_hops_v6, bins=n_bins)
    cdf = np.cumsum(counts)
    ax.plot(bin_edges[1:], cdf/cdf[-1])

    # tidy up the figure
    ax.grid(True)
    #ax.legend(loc='right')
    ax.set_xlabel('Hop difference between IPv4 and IPv6')
    ax.set_ylabel('CDF')
    #ax.set_xlim(0,400)
    #ax.set_xscale('log')

    plt.savefig('{}/trace-cdf.eps'.format(result_folder))

def hist_plot(nb_hops):
    num_bins = 6
    sns.set()
    fig, ax = plt.subplots()

    # the histogram of the data
    #n, bins, patches = ax.hist(nb_hops, bins=[-15,-12,-9,-6,-3,0,3,6,9,12,15], weights=np.ones(len(nb_hops))/len(nb_hops))
    sns.distplot(nb_hops, kde=False, bins=[-15,-12,-9,-6,-3,0,3,6,9,12,15], hist_kws={'weights':np.ones(len(nb_hops))/len(nb_hops)})
    ax.set_ylabel('Probability density')
    ax.set_xlabel('Number of hops difference')
    ax.grid(axis='y')
    # Tweak spacing to prevent clipping of ylabel
    fig.tight_layout()
    plt.savefig('{}/trace-hist.eps'.format(result_folder))

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
    trace_stat_dict = {}
    get_stat(country_code)

    with open("results/trace_stat_dict.json", "w") as f:
        json.dump(trace_stat_dict, f, indent=4, sort_keys=True)
    
    nb_hops_v4, nb_hops_v6, nb_hops_diff = compute_stat_list('nb_hops')
    cdf_plot(nb_hops_v4, nb_hops_v6)
    hist_plot(nb_hops_diff)
