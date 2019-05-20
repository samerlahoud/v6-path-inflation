import json
from ripe.atlas.cousteau import ProbeRequest
from collections import defaultdict

with open('countries.json', 'r') as f:
    countries = json.load(f)

probe_dict = defaultdict(list)

for country in countries.items():
    country_code = country[1]
    filters = {"country_code": country_code, "status":  1, "tags": "system-ipv4-capable", "tags": "system-ipv6-capable"}
    probes = ProbeRequest(**filters)
    for probe in probes:
        probe_dict[country_code].append(probe["id"])

with open("probes.json", "w") as f:
    json.dump(probe_dict, f, indent=4, sort_keys=True)