from multiprocessing import Process, freeze_support
from communication.post_info import *
from comm_monitor import *

def fork_cache_client_info(locator, client_info, srv_ip, cdn_host, isDiag=True):
    p = Process(target=cache_client_info, args=(locator, client_info, srv_ip, cdn_host, isDiag))
    p.start()
    return p

def fork_locate_anomaly(locator, client_ip, srv_ip, qoe):
    p = Process(target=locate_anomaly, args=(locator, client_ip, srv_ip, qoe))
    p.start()
    return p

def fork_update_attributes(diag_aent, client_ip, srv_ip, qoe):
    p = Process(target=updateAttribute, args=(diag_aent, client_ip, srv_ip, qoe))
    p.start()
    return p

def fork_add_event(diag_agent, client, eventType, prevVal, curVal):
    p = Process(target=add_event, args=(diag_agent, client, eventType, prevVal, curVal))
    p.start()
    return p

def fork_diagnose_anomaly(diagAgent, client_ip, srv_ip, qoe, anomalyType):
    p = Process(target=diagnose_anomaly, args=(diagAgent, client_ip, srv_ip, qoe, anomalyType))
    p.start()
    return p

def fork_add_qoe(monitor, src, dst, chunkID, qoe):
    p = Process(target=addQoE, args=(monitor, src, dst, chunkID, qoe))
    p.start()
    return p