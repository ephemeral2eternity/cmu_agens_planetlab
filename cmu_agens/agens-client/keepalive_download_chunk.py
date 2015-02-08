import httplib
import os

def keepalive_download_chunk(conn, vidName, chunk_name):
	conn.request('GET', '/' + vidName + '/' + chunk_name, headers={"Connection":" keep-alive"})
	try:
		r = conn.getresponse()
	except:
		conn.connect()
		r = conn.getresponse()

	if r.status == 200:
		print "ok"
	else:
		print "problem : the query returned %s because %s" % (r.status, r.reason) 
		

	localCache = './tmp/'

	# Create a cache folder locally
	try:
        	os.stat(localCache)
	except:
        	os.mkdir(localCache)

	localFile = localCache + chunk_name.replace('/', '-')

	f = open(localFile, 'wb')
	file_size = int(r.getheaders()[0][1])

	file_size_dl = 0
	block_sz = 8192
	while True:
		buffer = r.read(block_sz)
		if not buffer:
			break

	file_size_dl += len(buffer)
	f.write(buffer)
	status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
	status = status + chr(8)*(len(status)+1)

	f.close()
	return file_size
