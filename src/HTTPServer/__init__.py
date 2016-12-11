import os
import wx.lib.newevent
import time
import urlparse
import select
import socket
from threading import Thread
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

def quote(s):
	return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def makeXML(d):
	xml = ''
	if type(d) is dict:
		for k in d.keys():
			if type(d[k]) is dict:
				xml+='<'+k+'>'+makeXML(d[k])+'</'+k+'>'
			elif type(d[k]) is list:
				for i in d[k]:
					xml += '<'+k+'>'+makeXML(i)+'</'+k+'>'
			else:
				xml+='<'+k+'>'+quote(str(d[k]))+'</'+k+'>'
		else:
			xml = quote(str(d))
	
	return xml

class Handler(BaseHTTPRequestHandler):
	def do_GET(self):
		app = self.server.getApp()
		v = app.queryStatus()

		self.send_response(200)
		self.send_header("Content-type", "text/xml")
		self.send_header("charset", 'ISO-8859-1')
		self.end_headers()
		self.wfile.write(makeXML(v))

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
	def serve_reprap(self):
		self.haltServer = False
		while self.haltServer == False:
			if select.select([self.socket], [], [], 1)[0]:
				self.handle_request()
				
	def setApp(self, app):
		self.app = app
		
	def getApp(self):
		return self.app
			
	def shut_down(self):
		self.haltServer = True

class RepRapServer:
	def __init__(self, app, port=0):
		self.app = app
		self.log = app.log
		self.port = port
		if self.port == 0:
			return

		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(('4.2.2.1', 123))
		self.ipaddr = s.getsockname()[0]
		
		self.server = ThreadingHTTPServer((self.ipaddr, self.port), Handler)
		self.server.setApp(self)
		Thread(target=self.server.serve_reprap).start()
		self.log("HTTP Server started on %s:%d" % (self.ipaddr, self.port))
		
	def queryStatus(self):
		return self.app.getStatusReport()
	
	def close(self):
		if self.port != 0:
			self.server.shut_down()

