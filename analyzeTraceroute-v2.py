import json
import glob
from pathlib import Path
from ripe.atlas.sagan import TracerouteResult
import numpy as np
import sys
import matplotlib.pyplot as plt
from collections import defaultdict

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
    trace_stat_dict = {}
    get_stat(country_code)
    
    print(trace_stat_dict)

    with open("results/trace_stat_dict.json", "w") as f:
        json.dump(trace_stat_dict, f, indent=4, sort_keys=True)
    
    nb_hops_v4, nb_hops_v6, nb_hops_diff = compute_stat_list('nb_hops')
    print(nb_hops_v4, nb_hops_v6, nb_hops_diff)
