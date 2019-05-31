import json
from ripe.atlas.cousteau import AtlasResultsRequest
from datetime import datetime, timedelta
import os

#start_date = datetime(2019, 5, 15, 8)-timedelta(days=20,hours=12)
#stop_date = start_date + timedelta(hours=1)
start_date = datetime.utcnow()-timedelta(hours=2)
stop_date = start_date + timedelta(hours=1)
with open('probes.json', 'r') as f:
    probes = json.load(f)

with open('builtin_msm_id.json', 'r') as f:
    msm_id_list = json.load(f)

for country in probes:
    for probe in probes[country]:
        print(probe)
        folder_name = "data-{}/{}/".format(int(datetime.timestamp(start_date)),probe)
        os.makedirs(os.path.dirname(folder_name),exist_ok=True)

        for msm_list in msm_id_list:        
            for msm_pair in msm_list.values():
                for msm_id in msm_pair:
                    kwargs = {
                        "msm_id": msm_id,
                        "start": start_date,
                        "stop": stop_date,
                        "probe_ids": probe
                    }
                    msm_median_rtt = []
                    is_success, results = AtlasResultsRequest(**kwargs).create()
                    if is_success:
                        with open("data-{}/{}/{}.json".format(int(datetime.timestamp(start_date)),probe,msm_id), "w") as f:
                            json.dump(results, f, indent=4, sort_keys=True)
            #     for result in results:
            #         parsed_result = PingResult.get(result)
            #         if(parsed_result.rtt_average):
            #             median_rtt = np.median(parsed_result.rtt_median)
            #         else: 
            #             continue
            #         if(median_rtt):
            #             msm_median_rtt.append(np.median(parsed_result.rtt_median))
            # print(msm_median_rtt)