## Tolerate a chunk request fault via retrying.
# tolerate_error.py
# Chen Wang, Oct. 23, 2015
# chenw@cmu.edu
import sys
import time
from download_chunk import *
from mpd_parser import *

### ===========================================================================================================
## Chunk request failure handler
### ===========================================================================================================
def ft_download_chunk(retry_srv, retry_num, video_name, chunk_id):
	vchunk_sz = 0
	error_num = 0
	rsp_code = 'Unknown'
	error_codes = {}
	while (vchunk_sz == 0) and (error_num < retry_num):
		# Try to download again the chunk
		(vchunk_sz, chunk_srv_ip, rsp_code) = download_chunk(retry_srv, video_name, chunk_id)
		if not rsp_code.startswith('2'):
			error_codes[time.time()] = rsp_code
			print rsp_code

		error_num = error_num + 1

	return (vchunk_sz, chunk_srv_ip, error_codes)

### ===========================================================================================================
## mpd_parser failure handler
### ===========================================================================================================
def ft_mpd_parser(retry_srv, retry_num, video_name):
	error_num = 0
	rsts = ''
	while (not rsts) and (error_num < retry_num):
		rsts = mpd_parser(retry_srv, video_name)
		error_num += 1

	return rsts
