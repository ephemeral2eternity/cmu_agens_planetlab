## Common parameters
import os

cdn_host = "az.cmu-agens.com"
manager = "manage.cmu-agens.com"
monitor = "monitor.cmu-agens.com"


### Parameters for streaming
num_runs = 5
video_name = "BBB"
update_period = 12
cdn_srv_addr = cdn_host + '/videos/'


### Parameters for verify agents
duration_to_probe = 3600
probe_step = 10

csv_trace_folder = os.getcwd() + "/dataQoE/"
route_trace_folder = os.getcwd() + "/routeData/"
qoe_trace_fields = ["TS", "Buffer", "Freezing", "QoE1", "QoE2", "Representation", "Response", "Server", "ChunkID"]
rtt_trace_fields = ["TS", "src", "dst", "rtt"]

try:
    os.stat(csv_trace_folder)
except:
    os.mkdir(csv_trace_folder)

try:
    os.stat(route_trace_folder)
except:
    os.mkdir(route_trace_folder)
