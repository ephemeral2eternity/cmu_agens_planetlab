## Testing the CDN client in a VoD System
# test_cdn_client.py
# Chen Wang, Oct. 23, 2015
# chenw@cmu.edu
from utils.client_utils import *

from adaptive_client import *
from dash_client import *
from utils.test_utils import *

### Get client name and attache to the closest cache agent
client_name = getMyName()

script_full_path = os.path.realpath(__file__)
script_path, filename = os.path.split(script_full_path)
latest_config_file = script_path + '/config/cdn-qoes.json'
org_config_file = script_path + '/config/cdn-urls.json'

if not os.path.exists(latest_config_file):
	cdns = json.load(open(org_config_file))
else:
	cdns = json.load(open(latest_config_file))

# methods = ['Azure', 'Fastly', 'Rackspace', 'CloudFront', 'Adapt1', 'Adapt2']
## Default CDN setting
video_name = 'st'
selected_method = 'Azure'

### Get the server to start streaming
cur_ts = time.time()

## Testing rtt based server selection
# waitRandom(1, 100)
if len(sys.argv) > 1:
	selected_method = sys.argv[1]

if len(sys.argv) > 2:
	video_name = sys.argv[2]

print selected_method, video_name
if selected_method == "Adapt1":
	print "[Adapt1]: Use Adaptive CDN selection methods to select among Azure CDN and CloudFront!"
	adapt_cdn = {}
	adapt_cdn['Azure'] = cdns['Azure'].copy()
	adapt_cdn['CloudFront'] = cdns['CloudFront'].copy()
	updated_adapt_cdn = adaptive_client(adapt_cdn, video_name, selected_method)
	cdns['Azure'] = updated_adapt_cdn['Azure'].copy()
	cdns['CloudFront'] = updated_adapt_cdn['CloudFront'].copy()
elif selected_method == "Adapt2":
	print "[Adapt2]: Use Adaptive CDN selection methods to select among Azure CDN and Rackspace!"
	adapt_cdn = {}
	adapt_cdn['Azure'] = cdns['Azure'].copy()
	adapt_cdn['Rackspace'] = cdns['Rackspace'].copy()
	updated_adapt_cdn = adaptive_client(adapt_cdn, video_name, selected_method)
	cdns['Azure'] = updated_adapt_cdn['Azure'].copy()
	cdns['Rackspace'] = updated_adapt_cdn['Rackspace'].copy()
elif selected_method in cdns.keys():
	print "Use " + selected_method + " CDN to stream video!"
	selected_url = cdns[selected_method]['url']
	sqs = dash_client(selected_url, video_name, selected_method)
	cdns[selected_method]['QoE'] = sqs
else:
	print "[Error] Selected method is not available: ", selected_method

print "Updated CDN SQS: ", cdns

try:
	with open(latest_config_file, 'w') as outfile:
		json.dump(cdns, outfile, sort_keys = True, indent = 4, ensure_ascii=False)
except:
	os.remove(latest_config_file)