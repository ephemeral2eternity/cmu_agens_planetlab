#### Temporal analysis of recent QoE data
# detect_anomaly.py
# Chen Wang, Nov. 10, 2016
# chenw@cmu.edu
from utils.params import *

def detect_anomaly(recent_qoes):
    anomaly_idx = [x for x in recent_qoes if x <= qoe_th]
    anomaly_pts = len(anomaly_idx)
    total_pts = len(recent_qoes)
    if anomaly_pts > 0:
        isAnomaly = True
        anomaly_ratio = anomaly_pts / float(total_pts)
        if anomaly_ratio < 0.2:
            anomaly_type = "occasional"
        elif anomaly_ratio < 0.7:
            anomaly_type = "recurrent"
        else:
            anomaly_type = "persistent"
    else:
        isAnomaly = False
        anomaly_type = None

    return (isAnomaly, anomaly_type)
