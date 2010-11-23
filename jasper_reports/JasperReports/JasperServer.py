import os
import glob
import time
import socket
import subprocess
import xmlrpclib

class JasperServer:
	def __init__(self, port=8090):
		self.port = port
		self.pidfile = None
		url = 'http://localhost:%d' % port
		self.proxy = xmlrpclib.ServerProxy( url, allow_none = True )

	def path(self):
		return os.path.abspath(os.path.dirname(__file__))

	def setPidFile(self, pidfile):
		self.pidfile = pidfile

	def start(self):
		env = {}
		env.update( os.environ )
		if os.name == 'nt':
			sep = ';'
		else:
			sep = ':'
		libs = os.path.join( self.path(), '..', 'java', 'lib', '*.jar' )
		env['CLASSPATH'] = os.path.join( self.path(), '..', 'java' + sep ) + sep.join( glob.glob( libs ) ) + sep + os.path.join( self.path(), '..', 'custom_reports' )
		cwd = os.path.join( self.path(), '..', 'java' )
		process = subprocess.Popen(['java', 'com.nantic.jasperreports.JasperServer', unicode(self.port)], env=env, cwd=cwd)
		if self.pidfile:
			f = open( self.pidfile, 'w')
			try:
				f.write( str( process.pid ) ) 
			finally:
				f.close()

	def execute(self, *args):
		try: 
			self.proxy.Report.execute( *args )
		except (xmlrpclib.ProtocolError, socket.error), e:
			print "FIRST TRY DIDN'T WORK: ", str(e), str(e.args)
			self.start()
			for x in xrange(40):
				time.sleep(1)
				try:
					print "TRYING"
					return self.proxy.Report.execute( *args )
				except (xmlrpclib.ProtocolError, socket.error), e:
					print "EXCEPTION: ", str(e), str(e.args)
					pass

