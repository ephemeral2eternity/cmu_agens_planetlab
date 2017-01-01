## Streaming Videos from a CDN and do traceroute and pings to the CDN
# trace_cdn.py
# Chen Wang, Mar. 3, 2016
# chenw@cmu.edu
import csv
from qdiag_client_agent import *
from multiprocessing import freeze_support
from monitor.get_hop_info import *
from utils.test_utils import *
from communication.connect_cloud_agent import *
import client_config

## Denote the server info
# cdn_host = 'cmu-agens.azureedge.net'
# cdn_host = 'aws.cmu-agens.com'
if __name__ == '__main__':
	if sys.platform == 'win32':
		freeze_support()

	if len(sys.argv) > 1:
		num_runs = int(sys.argv[1])
	else:
		num_runs = client_config.num_runs

	waitRandom(1, 300)
	## ==================================================================================================
	# Get Client INFO, streaming configuration file, CDN server and route to the CDN and report the route
	# INFO to the anomaly locator agent
	## ==================================================================================================
	client_name = getMyName()
	client_ip, client_info = get_ext_ip()
	client_info['name'] = client_name
	device_info = get_device_info()
	client_info['device'] = device_info
	## Create Trace CSV file
	cur_ts = time.strftime("%m%d%H%M%S")
	client_ID = client_name + "_" + cur_ts
	client_info['id'] = client_ID

	## ==================================================================================================
	### Manager and monitor, etc.
	## ==================================================================================================
	diag_agent_info = get_my_cloud_agent(client_config.manager)
	diag_agent = diag_agent_info['ip']

	## ==================================================================================================
	### Initialize the trace writer
	## ==================================================================================================
	qoe_trace_file = client_ID + "_QoE.csv"
	out_qoe_trace = open(client_config.csv_trace_folder + qoe_trace_file, 'wb')
	qoe_csv_writer = csv.DictWriter(out_qoe_trace, fieldnames=client_config.qoe_trace_fields)
	qoe_csv_writer.writeheader()

	for i in range(num_runs):
		qdiag_client_agent(diag_agent, client_info, qoe_csv_writer)

		if os.path.exists(os.getcwd() + "/tmp/"):
			shutil.rmtree(os.getcwd() + "/tmp/")

	## Close tracefile
	out_qoe_trace.close()
