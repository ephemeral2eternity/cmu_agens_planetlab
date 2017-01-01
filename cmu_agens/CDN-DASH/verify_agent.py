from communication.comm_manager import *
from communication.thread_wrapper import *
from monitor.get_hop_info import *
from multiprocessing import freeze_support
from utils.client_utils import *
import client_config
import csv


### Connect to the manager to obtain the verfification agents to ping
if __name__ == '__main__':
    if sys.platform == 'win32':
        freeze_support()

    if len(sys.argv) > 1:
        srv_to_probe = sys.argv[1]
    else:
        srv_to_probe = "az.cmu-agens.com"

    if len(sys.argv) > 2:
        duration_to_probe = int(sys.argv[2])
    else:
        duration_to_probe = client_config.duration_to_probe

    if len(sys.argv) > 3:
        probe_step = int(sys.argv[3])
    else:
        probe_step = client_config.probe_step


    client_name = getMyName()
    cur_ts = time.strftime("%m%d%H%M%S")
    rtt_trace_file = client_name + "-" + srv_to_probe + "-" + cur_ts  + "_rtt.csv"
    out_rtt_trace = open(client_config.csv_trace_folder + rtt_trace_file, 'wb')
    rtt_csv_writer = csv.DictWriter(out_rtt_trace, fieldnames=client_config.rtt_trace_fields)
    rtt_csv_writer.writeheader()

    my_ip, _ = get_ext_ip()

    for i in range(duration_to_probe/probe_step):
        time_start = time.time()
        rtt, srv_ip = getMnRTT(srv_to_probe)
        if not srv_ip:
            srv_ip = srv_to_probe

        curTS = time.time()
        cur_rst = dict(TS=curTS, src=my_ip, dst=srv_ip, rtt=rtt)
        rtt_csv_writer.writerow(cur_rst)
        ### Add report rtt to monitor server.
        duration =  time.time() - time_start

        if duration < probe_step:
            time.sleep(probe_step - duration)

    out_rtt_trace.close()