import os

## File paths
current_folder = os.path.dirname(__file__)
probe_path = current_folder + '/probe/'
try:
    os.stat(probe_path)
except:
    os.mkdir(probe_path)

trace_path = current_folder + '/trace/'
try:
    os.stat(trace_path)
except:
    os.mkdir(trace_path)

info_path = current_folder + '/hostinfo/'
try:
    os.stat(trace_path)
except:
    os.mkdir(trace_path)