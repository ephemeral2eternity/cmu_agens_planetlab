#!/usr/bin/python
# Cooperative Client Agent in QoE based Anomaly Localization System
# coop_agent.py
# Chen Wang, chenw@cmu.edu
# Jun. 16, 2015
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os # os. path
from attach_cache_agent import *
from test_utils import *
from coop_utils import *
import urlparse

## Globe Variables
PORT = 8717
hostname = getMyName()

# Get Trace Routes from all servers
all_hops = get_all_routes()

#==========================================================================================
# Write out an welcome page showing all routes to all cache agents deployed in Google Cloud
#==========================================================================================
def welcome_page():
    part1 = "<html>  \
                <title>  \
                    Client Peer " + hostname + "Listening on Port: " + str(PORT) + " \
                </title> \
                <body>  \
                	<h1>Client Peer " + hostname + "Listening on Port: " + str(PORT) + "</h1> \
                    <h1> The routes from client " + hostname + "to all servers include followings: </h1> \
                    <ul>"

    part2 = ""
    for srv in all_hops.keys():
    	part2 = part2 + "<li>" + srv + "<ul>"
    	cur_hops = all_hops[srv]
    	for hop_id in sorted(cur_hops.keys()):
    		part2 = part2 + "<li>" + str(hop_id)  + ", " + cur_hops[hop_id]['Name'] + "</li>"

    	part2 = part2 + "</ul></li>"

    part3 = "</ul> \
                </body> \
            </html>"

    page = part1 + part2 + part3
    return page

#==========================================================================================
# Handle peer client's requests on querying the route info and QoE
#==========================================================================================
class MyHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		try:
			if "ico" in self.command:
				return

			## Show all the traceroute info to all servers
			elif self.path == '/':
				page = welcome_page()
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				self.wfile.write(page)
				return

			## Get the QoE, video, and route info from a peer client
			elif self.path.startswith('/get?'):
				vidID = int(self.path.split('?')[1])

				info = get_info(vidID)

				pkt = wrapPKT(info)

				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.send_header('Params', json.dumps(pkt))
				self.end_headers()

				cur_page = "<h1>The packet sent to other clients for anomaly localization is: </h1>"
				cur_page = cur_page + "<p>" + json.dumps(pkt) + "</p>"
				self.wfile.write(cur_page)
				return

			## Get the latest observation from local client
			elif self.path.startswith('/latest'):
				info = get_latest()
				pkt = wrapPKT(info)

				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.send_header('Params', json.dumps(pkt))
				self.end_headers()

				cur_page = "<h1>The packet sent to other clients for anomaly localization is: </h1>"
				cur_page = cur_page + "<p>" + json.dumps(pkt) + "</p>"
				self.wfile.write(cur_page)
				return

			else:
				return

		except IOError as e :     
			print e
			self.send_error(404,'File Not Found: %s' % self.path)

	def do_POST(self):
		self.send_response(200)
		self.end_headers()
		self.wfile.write("<HTML><HEAD></HEAD><BODY>POST OK.<BR><BR>");
		self.wfile.write( "File uploaded under name: " + os.path.split(fullname)[1] );
		self.wfile.write(  '<BR><A HREF=%s>back</A>' % ( UPLOAD_PAGE, )  )
		self.wfile.write("</BODY></HTML>");

#==========================================================================================
# Wrap info dict obtained from reading qoe.db to a packet to send over http
#==========================================================================================
def wrapPKT(info):
	if not info:
		pkt = {}
	else:
		srv = info['srv']
		srv_qoe = info['qoe']
		srv_name = info['srvName']
		vidID = info['video']
		srv_route_str = get_route_str(srv, all_hops)

		## Return the anomaly info for cooperative anomaly localization
		pkt = dict()
		pkt['qoe'] = str(srv_qoe)
		pkt['route'] = srv_route_str
		pkt['video'] = vidID
		pkt['srv'] = srv
		pkt['srvName'] = srv_name

	return pkt

#==========================================================================================
# Main Function of A Cooperative Agent
#==========================================================================================
def main(argv):
	### Get client name and attache to the closest cache agent
	client_name = getMyName()
	cache_agent = attach_cache_agent()

	## Connect client to its cache agent and update centralized manager
	print "Client ", client_name, " is connecting to cache agent : ", cache_agent['name']
	connect_cache_agent(client_name, cache_agent['name'], cache_agent['ip'])
	update_cache_agent(client_name, cache_agent['name'])
	create_db()

	## Start listening as a server on PORT
	server = HTTPServer(('', PORT), MyHandler)
	print 'started listening on port : ', str(PORT), ' .... '
	server.serve_forever()

if __name__ == '__main__':
    main(sys.argv)
