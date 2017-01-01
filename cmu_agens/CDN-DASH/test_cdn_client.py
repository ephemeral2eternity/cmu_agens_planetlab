## Testing the CDN client in a VoD System
# test_cdn_client.py
# Chen Wang, Oct. 23, 2015
# chenw@cmu.edu
from utils.client_utils import *

from dash_client import *
from utils.test_utils import *

### Get client name and attache to the closest cache agent
client_name = getMyName()

if len(sys.argv) > 1:
	cdn_host = sys.argv[1]
else:
	cdn_host = 'az.cmu-agens.com'

if len(sys.argv) > 2:
	video_name = sys.argv[2]
else:
	video_name = 'BBB'

## Denote the server info
srv_addr = cdn_host + '/videos'

### Get the server to start streaming
dash_client(srv_addr, video_name)

if os.path.exists(os.getcwd() + "/tmp/"):
	shutil.rmtree(os.getcwd() + "/tmp/")

