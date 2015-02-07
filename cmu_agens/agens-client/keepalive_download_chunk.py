import httplib

def keepalive_download_chunk(conn, vidName, chunk_name):
	conn.request('GET', '/' + vidName + '/' + chunk_name)
	r = conn.getresponse()	

	localCache = './tmp/'

	# Create a cache folder locally
	try:
        	os.stat(localCache)
	except:
        	os.mkdir(localCache)

	localFile = localCache + chunk_name.replace('/', '-')

	f = open(localFile, 'wb')
	meta = u.info()
	file_size = int(meta.getheaders("Content-Length")[0])
	# print "Downloading: %s Bytes: %s" % (localFile, file_size)

	file_size_dl = 0
	block_sz = 8192
	while True:
		buffer = u.read(block_sz)
		if not buffer:
			break

	file_size_dl += len(buffer)
	f.write(buffer)
	status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
	status = status + chr(8)*(len(status)+1)
	# print status,

	f.close()
	# u.close()
	return file_size
