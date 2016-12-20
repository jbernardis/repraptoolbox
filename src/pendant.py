from serial import Serial
import thread
import time
from sys import platform as _platform
if _platform == "linux" or _platform == "linux2":
	import termios  # @UnresolvedImport

pendantHomes = {
	'home': "G28",
	'homex': "G28 X0",
	'homey': "G28 Y0",
	'homez': "G28 Z0",
	}

pendantMoves = {
	'movex1': "X0.1",
	's-movex1': "X0.1",
	'movex2': "X1",
	's-movex2': "X1",
	'movex3': "X10",
	's-movex3': "X100",
	'movex-1': "X-0.1",
	's-movex-1': "X-0.1",
	'movex-2': "X-1",
	'smovex-2': "X-1",
	'movex-3': "X-10",
	's-movex-3': "X-100",
	'movey1': "Y0.1",
	's-movey1': "Y0.1",
	'movey2': "Y1",
	's-movey2': "Y1",
	'movey3': "Y10",
	's-movey3': "Y100",
	'movey-1': "Y-0.1",
	's-movey-1': "Y-0.1",
	'movey-2': "Y-1",
	's-movey-2': "Y-1",
	'movey-3': "Y-10",
	's-movey-3': "Y-100",
	'movez1': "Z0.1",
	's-movez1': "Z0.1",
	'movez2': "Z1",
	's-movez2': "Z1",
	'movez3': "Z10",
	's-movez3': "Z10",
	'movez-1': "Z-0.1",
	's-movez-1': "Z-0.1",
	'movez-2': "Z-1",
	's-movez-2': "Z-1",
	'movez-3': "Z-10",
	's-movez-3': "Z-10",
	}

def pendantCommand(cmd, printer, log):
	c = cmd.lower()
	if c in pendantMoves.keys():
		axis = pendantMoves[c]
			
		if axis.startswith("Z"):
			speed = "F%s" % str(printer.getZSpeed())
		else:
			speed = "F%s" % str(printer.getXYSpeed())
			
		s = []
		s.append("G91")
		s.append("G1 %s %s" % (axis, speed))
		s.append("G90")
		return s
			
	elif c in pendantHomes.keys():
		return [pendantHomes[c]]
		
	elif c == "extrude":
		dst = printer.getEDistance()
		sp = printer.getESpeed()
		
		s = []
		s.append("G91")
		s.append("G1 E%.3f F%.3f" % (dst, sp))
		s.append("G90")
		return s
		
	elif c == "retract":
		dst = printer.getEDistance()
		sp = printer.getESpeed()
		
		s = []
		s.append("G91")
		s.append("G1 E-%.3f F%.3f" % (dst, sp))
		s.append("G90")
		return s
		
	elif c.startswith("temp"):
		target = c[4:7]
		try:
			temp = int(c[7])
			if temp < 0 or temp > 2:
				temp = None
		except:
			temp = None

		if temp is not None:				
			if target == "bed":
				return printer.getBedCommand(temp)
			
			elif target.startswith("he"):
				try:
					tool = int(target[2])
					if tool < 0:
						tool = None
				except:
					tool = None
				if tool is not None:
					return printer.getHECommand(tool, temp)
						
				else:
					log("Pendant temp command has invalid tool number: " + cmd)
					return None
			else:
				log("Pendant temp command has invalid target: " + cmd)
				return None
		else:
			log("Pendant temp command has invalid temp index: " + cmd)
			return None
	else:
		print "unexpected pendant command: (%s)" % c
		return None  # command not handled

class Pendant:
	def __init__(self, cbConn, cbCmd, port, baud=9600):
		self.cbConn = cbConn
		self.cbCmd = cbCmd
		self.port = port
		self.baud = baud
		thread.start_new_thread(self.Run, ())
		
	def kill(self):
		self.isRunning = False
		self.disconnect()
		
	def isKilled(self):
		return not self.isRunning
	
	def Run(self):
		self.isRunning = True
		while self.isRunning:
			self.connect()
			if self.pendant is not None:
				self.cbConn(True)
			while self.pendant is not None:
				try:
					line=self.pendant.readline()
					if(len(line)>1):
						self.cbCmd(line.strip())
						
					time.sleep(1);
					
				except:
					self.cbConn(False)
					self.disconnect()
					line = ""

	def connect(self):
		try:
			self.resetPort()
			self.pendant = Serial(self.port, self.baud, timeout=2)
		except:
			self.pendant = None
		
	def resetPort(self):
		if _platform == "linux" or _platform == "linux2":
			fp = open(self.port, "r")
			new = termios.tcgetattr(fp)
			new[2] = new[2] | ~termios.CREAD
			termios.tcsetattr(fp, termios.TCSANOW, new)
			fp.close()

	def disconnect(self):
		try:
			self.pendant.close()
		except:
			pass
		self.pendant = None

