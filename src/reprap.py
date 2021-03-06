from serial import Serial
import thread
import Queue
import time
import re
import wx.lib.newevent
from sys import platform as _platform
if _platform == "linux" or _platform == "linux2":
	import termios  # @UnresolvedImport

TRACE = False

(RepRapEvent, EVT_REPRAP_UPDATE) = wx.lib.newevent.NewEvent()
(SDCardEvent, EVT_SD_CARD) = wx.lib.newevent.NewEvent()
(PrtMonEvent, EVT_PRINT_MONITOR) = wx.lib.newevent.NewEvent()

from reprapenums import RepRapEventEnum, RepRapCmdEnum, RepRapLogEnum
from sdenums import SdEventEnum

MAX_EXTRUDERS = 1

CACHE_SIZE = 50

TEMPINTERVAL = 1
POSITIONINTERVAL = 1

# printer commands that are permissible while actively printing
allow_while_printing_base = [ "M0", "M1", "M20", "M21", "M22", "M23", "M25", "M27", "M29", "M30", "M31", "M42", "M82", "M83", "M85", "M92",
					"M104", "M105", "M106", "M114", "M115", "M117", "M119", "M140",
					"M200", "M201", "M202", "M203", "M204", "M205", "M206", "M207", "M208", "M209", "M240"]

class MsgCache:
	def __init__(self, size):
		self.cacheSize = size
		self.reinit()
		
	def reinit(self):
		self.cache = []
		self.lastKey = None
		
	def addMsg(self, key, msg):
		if self.lastKey is not None and key != self.lastKey+1:
			self.reinit()
			
		self.lastKey = key
		self.cache.append(msg)
		d = self.cacheSize - len(self.cache)
		if d < 0:
			self.cache = self.cache[-d:]
			
	def getMsg(self, key):
		l = len(self.cache)
		if key > self.lastKey or key <= self.lastKey - l:
			return None
		
		i = l - (self.lastKey - key) - 1
		if i < 0 or i >= self.cacheSize:
			return None
		
		return self.cache[i]

class SendThread:
	def __init__(self, win, printer, firmware, priQ, mainQ):
		self.win = win
		self.printer = printer
		self.firmware = firmware
		self.priQ = priQ
		self.mainQ = mainQ
		
		self.logLevel = RepRapLogEnum.LOG_NONE
		
		self.isPrinting = False
		self.isRunning = False
		self.endOfLife = False
		self.online = True
		self.printIndex = 0
		self.sequence = 0
		self.okWait = False
		self.checksum = True
		self.resendFrom = None
		self.resends = 0
		self.sentCache = MsgCache(CACHE_SIZE)
		thread.start_new_thread(self.Run, ())
		
	def setLogLevel(self, level):
		self.logLevel = level
		
	def kill(self):
		self.isRunning = False

	def isKilled(self):
		return self.endOfLife
		
	def endWait(self):
		self.okWait = False
	
	def setResendFrom(self, n):
		self.resendFrom = n
	
	def getPrintIndex(self):
		return self.printIndex-1
		
	def setCheckSum(self, flag):
		self.checksum = flag
		
	def resetCounters(self):
		self.resends = 0
		
	def getCounters(self):
		return self.resends
			
	def _checksum(self,command):
		return reduce(lambda x,y:x^y, map(ord,command))
	
	def reportConnection(self, connected, prtport):
		self.online = connected
		self.prtport = prtport
		if not connected and self.isPrinting:
			self.killPrint()

	def Run(self):
		self.isRunning = True
		while self.isRunning:
			if self.isPrinting:
				if not self.priQ.empty():
					try:
						(cmd, string) = self.priQ.get(True, 0.01)
						self.processCmd(cmd, string, False, False, True)
					except Queue.Empty:
						pass
					
				elif self.resendFrom is not None:
					string = self.sentCache.getMsg(self.resendFrom)
					if string is None:
						self.resendFrom = None
					else:
						self.resends += 1
						self.resendFrom += 1
						self.processCmd(RepRapCmdEnum.CMD_GCODE, string, False, True, False)
					
				elif not self.okWait:
					if not self.mainQ.empty():
						try:
							(cmd, string) = self.mainQ.get(True, 0.01)
							self.processCmd(cmd, string, True, True, False)

						except Queue.Empty:
							pass
					else:
						time.sleep(0.001)
				else:
					time.sleep(0.001)

			else:
				try:
					(cmd, string) = self.priQ.get(True, 0.01)
					self.processCmd(cmd, string, False, False, True)
				except Queue.Empty:
					time.sleep(0.01)
		self.endOfLife = True
		self.printer = None
				
	def processCmd(self, cmd, string, calcCS, setOK, PriQ):
		if cmd == RepRapCmdEnum.CMD_GCODE:
			if calcCS:
				self.printIndex += 1
				
				try:
					verb = string.split()[0]
				except:
					verb = ""
				
				if self.checksum:
					prefix = "N" + str(self.sequence) + " " + string
					string = prefix + "*" + str(self._checksum(prefix))
					if verb != "M110":
						self.sentCache.addMsg(self.sequence, string)
					self.sequence += 1
				
			if setOK: self.okWait = True
			if TRACE:
				print "==>", self.okWait, string
				
			if self.logLevel == RepRapLogEnum.LOG_ALL or (self.logLevel == RepRapLogEnum.LOG_CMD and PriQ):
				evt = RepRapEvent(event = RepRapEventEnum.PRINT_SENDGCODE, msg = string, primary=PriQ, immediate=False)
				wx.PostEvent(self.win, evt)
				
			try:
				self.prtport.write(str(string+"\n"))
			except:
				evt = RepRapEvent(event = RepRapEventEnum.PRINT_ERROR, msg="Unable to write to printer")
				wx.PostEvent(self.win, evt)
				self.killPrint()
			
		elif cmd == RepRapCmdEnum.CMD_STARTPRINT:
			string = "M110"
			if self.checksum:
				prefix = "N-1 " + string
				string = prefix + "*" + str(self._checksum(prefix))
				
			self.okWait = True

			try:
				self.prtport.write(str(string+"\n"))
			except:
				evt = RepRapEvent(event = RepRapEventEnum.PRINT_ERROR, msg="Unable to write to printer")
				wx.PostEvent(self.win, evt)
				self.killPrint()
				
			if TRACE:
				print "==>", self.okWait, string
			self.printIndex = 0
			self.sequence = 0
			self.sentCache.reinit()
			self.resendFrom = None
			self.isPrinting = True
			evt = RepRapEvent(event = RepRapEventEnum.PRINT_STARTED)
			wx.PostEvent(self.win, evt)
			
		elif cmd == RepRapCmdEnum.CMD_RESUMEPRINT:
			self.sentCache.reinit()
			self.resendFrom = None
			self.isPrinting = True
			evt = RepRapEvent(event = RepRapEventEnum.PRINT_RESUMED)
			wx.PostEvent(self.win, evt)
			
		elif cmd == RepRapCmdEnum.CMD_STOPPRINT:
			self.isPrinting = False
			self.sentCache.reinit()
			self.resendFrom = None
			evt = RepRapEvent(event = RepRapEventEnum.PRINT_STOPPED)
			wx.PostEvent(self.win, evt)
			
		elif cmd == RepRapCmdEnum.CMD_ENDOFPRINT:
			evt = RepRapEvent(event = RepRapEventEnum.PRINT_COMPLETE)
			self.sentCache.reinit()
			self.resendFrom = None
			wx.PostEvent(self.win, evt)
			
		elif cmd == RepRapCmdEnum.CMD_DRAINQUEUE:
			self.drainQueue()
			evt = RepRapEvent(event = RepRapEventEnum.QUEUE_DRAINED)
			wx.PostEvent(self.win, evt)
			
	def killPrint(self):
		self.isPrinting = False
		self.sentCache.reinit()
		self.resendFrom = None
		self.drainQueue()
			
	def drainQueue(self):
		self.sentCache.reinit()
		self.resendFrom = None
		while True:
			try:
				if self.mainQ.get(False)[0] == RepRapCmdEnum.CMD_ENDOFPRINT:
					break
			except Queue.Empty:
				break

	

class ListenThread:
	def __init__(self, win, printer, port, baud, firmware):
		self.win = win
		self.printer = printer
		self.port = port
		self.baud = baud
		self.firmware = firmware
		
		self.isRunning = False
		self.endOfLife = False
		self.connected = False
		self.eatOK = 0
		self.resendRequests = 0

		if firmware == "MARLIN":
			self.resend = "resend:"
			self.resendre = re.compile("resend: *([0-9]+)")
		elif firmware == "TEACUP":
			self.resend = "rs"
			self.resendre = re.compile("rs *N([0-9]+)")
		else:
			print "Unknown firmware: ", self.firmware
			self.resend = "resend:"
			self.resendre = re.compile("resend: *([0-9]+)")
	
		thread.start_new_thread(self.Run, ())
		
	def resetPort(self):
		if _platform == "linux" or _platform == "linux2":
			fp = open(self.port, "r")
			new = termios.tcgetattr(fp)
			new[2] = new[2] | ~termios.CREAD
			termios.tcsetattr(fp, termios.TCSANOW, new)
			fp.close()
			self.printerPort.setDTR(1)
			time.sleep(2)
			self.printerPort.setDTR(0)
			self.connected = False
		
	def kill(self):
		self.isRunning = False

	def isKilled(self):
		return self.endOfLife
		
	def resetCounters(self):
		self.resendRequests = 0
		
	def getCounters(self):
		return self.resendRequests
	
	def setEatOK(self):
		self.eatOK += 1
		
	def Run(self):
		self.isRunning = True
		while self.isRunning:
			if not self.connected:
				self.connected = self.connect()
				
			if not self.connected:
				time.sleep(2)
				continue
			
			try:
				line=self.printerPort.readline()
			except:
				evt = RepRapEvent(event = RepRapEventEnum.PRINT_ERROR, msg="Unable to read from printer")
				wx.PostEvent(self.win, evt)
				self.disconnect()
				continue

			if(len(line)>1):
				if TRACE:
					print "<==", line
				llow = line.strip().lower()
				
				if llow.startswith(self.resend):
					m = self.resendre.search(llow)
					if m:
						t = m.groups()
						if len(t) >= 1:
							try:
								n = int(t[0])
							except:
								n = None
								
						if n:
							self.resendRequests += 1
							self.printer.setResendFrom(n)
				
				if llow.startswith("ok"):
					if self.eatOK > 0:
						if TRACE:
							print "EATEN"
						self.eatOK -= 1
					else:
						self.printer.endWait()
						
					if llow == "ok":
						continue
						
				if line.startswith("echo:"):
					line = line[5:]

				evt = RepRapEvent(event=RepRapEventEnum.RECEIVED_MSG, msg = line.rstrip(), state = 1)
				wx.PostEvent(self.win, evt)

		self.endOfLife = True
		
	def connect(self):
		try:
			self.printerPort = Serial(self.port, self.baud, timeout=2)
			self.connected = True
			evt = RepRapEvent(event=RepRapEventEnum.CONNECTED, prtport=self.printerPort)
			wx.PostEvent(self.win, evt)
			return True
		except:
			self.connected = False
			return False
	
	def disconnect(self):
		self.connected = False
		evt = RepRapEvent(event=RepRapEventEnum.DISCONNECTED)
		wx.PostEvent(self.win, evt)

class RepRapParser:
	def __init__(self, reprap):
		self.reprap = reprap
		self.trpt1re = re.compile("ok *T: *([0-9\.]+) */ *([0-9\.]+) *B: *([0-9\.]+) */ *([0-9\.]+)")
		#self.trpt1bre = re.compile("ok *T: *([0-9\.]+) *B: *([0-9\.]+)")
		self.toolre = re.compile(".*?T([0-2]): *([0-9\.]+) */ *([0-9\.]+)")
		self.trpt2re = re.compile(" *T:([0-9\.]+) *E:([0-9\.]+) *B:([0-9\.]+)")
		self.trpt3re = re.compile(" *T:([0-9\.]+) *E:([0-9\.]+) *W:.*")
		self.trpt4re = re.compile(" *T: *([0-9\.]+) */ *([0-9\.]+) *B: *([0-9\.]+) */ *([0-9\.]+)")
		self.locrptre = re.compile("^ *X:([0-9\.\-]+) *Y:([0-9\.\-]+) *Z:([0-9\.\-]+) *E:([0-9\.\-]+) *Count")
		self.speedrptre = re.compile("Fan speed:([0-9]+) Feed Multiply:([0-9]+) Extrude Multiply:([0-9]+)")
		self.toolchgre = re.compile("Active tool is now T([0-9])")
		
		self.sdre = re.compile("SD printing byte *([0-9]+) *\/ *([0-9]+)")
		self.heaters = {}
		
		self.sd = None
		self.sdfiles = []
		self.insideListing = False
		
		self.tempHandler = None
		self.speedHandler = None
		self.toolHandler = None
		self.sdEventHandler = None
	
		self.firmware = None
		
	def setTempHandler(self, handler):
		self.tempHandler = handler

	def setSpeedHandler(self, handler):
		self.speedHandler = handler

	def setToolHandler(self, handler):
		self.toolHandler = handler
		
	def setSdEventHandler(self, hobj):
		self.sdEventHandler = hobj
		
	def sendSdEvent(self, evt):
		if self.sdEventHandler is None:
			return
		
		self.sdEventHandler.sdEvent(evt)
		
	def startFirmwareCollection(self, fw):
		self.firmware = fw

	def endFirmwareCollection(self):
		self.firmware = None

	def parseMsg(self, msg):
		if 'M92' in msg:
			X = self.parseG(msg, 'X')
			Y = self.parseG(msg, 'Y')
			Z = self.parseG(msg, 'Z')
			E = self.parseG(msg, 'E')
			if self.firmware is not None:
				self.firmware.m92(X, Y, Z, E)
			return False
		
		if 'M201' in msg:
			X = self.parseG(msg, 'X')
			Y = self.parseG(msg, 'Y')
			Z = self.parseG(msg, 'Z')
			E = self.parseG(msg, 'E')
			if self.firmware is not None:
				self.firmware.m201(X, Y, Z, E)
			return False
		
		if 'M203' in msg:
			X = self.parseG(msg, 'X')
			Y = self.parseG(msg, 'Y')
			Z = self.parseG(msg, 'Z')
			E = self.parseG(msg, 'E')
			if self.firmware is not None:
				self.firmware.m203(X, Y, Z, E)
			return False
		
		if 'M204' in msg:
			P = self.parseG(msg, 'P')
			R = self.parseG(msg, 'R')
			T = self.parseG(msg, 'T')
			if self.firmware is not None:
				self.firmware.m204(P, R, T)
			return False
		
		if 'M205' in msg:
			S = self.parseG(msg, 'S')
			T = self.parseG(msg, 'T')
			B = self.parseG(msg, 'B')
			X = self.parseG(msg, 'X')
			Z = self.parseG(msg, 'Z')
			E = self.parseG(msg, 'E')
			if self.firmware is not None:
				self.firmware.m205(S, T, B, X, Z, E)
			return False
		
		if 'M206' in msg:
			X = self.parseG(msg, 'X')
			Y = self.parseG(msg, 'Y')
			Z = self.parseG(msg, 'Z')
			if self.firmware is not None:
				self.firmware.m206(X, Y, Z)
			return False
		
		if 'M301' in msg:
			P = self.parseG(msg, 'P')
			I = self.parseG(msg, 'I')
			D = self.parseG(msg, 'D')
			if self.firmware is not None:
				self.firmware.m301(P, I, D)
			return False
		
		if 'M851' in msg:
			Z = self.parseG(msg, 'Z')
			if self.firmware is not None:
				self.firmware.m851(Z)
			return False
		
		if "SD card ok" in msg:
			evt = SDCardEvent(event = SdEventEnum.SD_CARD_OK)
			self.sendSdEvent(evt)
			return False
		
		if "SD init fail" in msg:
			evt = SDCardEvent(event = SdEventEnum.SD_CARD_FAIL)
			self.sendSdEvent(evt)
			return False
				
		if "Begin file list" in msg:
			self.insideListing = True
			self.sdfiles = []
			return False
		
		if "End file list" in msg:
			self.insideListing = False
			evt = SDCardEvent(event = SdEventEnum.SD_CARD_LIST, data=self.sdfiles)
			self.sendSdEvent(evt)
			return False

		if self.insideListing:
			self.sdfiles.append(msg.strip())
			return False
		
		#if "SD printing byte" in msg:
			#m = self.sdre.search(msg)
			#t = m.groups()
			#if len(t) != 2: return
			#gpos = int(t[0])
			#gmax = int(t[1])
			#evt = PrtMonEvent(event=SD_PRINT_POSITION, pos=gpos, max=gmax)
			#wx.PostEvent(self.printmon, evt)
			#if self.printmon.M27pending:
				#self.printmon.M27pending = False
				#return True
			#else:
				#return False
		#	
		#if "Done printing file" in msg:
			#evt = PrtMonEvent(event=SD_PRINT_COMPLETE)
			#wx.PostEvent(self.printmon, evt)
			#return False
		
		if "busy: processing" in msg:
			return True
		
		if "enqueueing \"" in msg:
			return True
		
		m = self.locrptre.search(msg)
		if m:
			return True

		m = self.trpt1re.search(msg)
		if m:
			gotHE = [False for i in range(MAX_EXTRUDERS)]
			HEtemp = [0 for i in range(MAX_EXTRUDERS)]
			HEtarget = [0 for i in range(MAX_EXTRUDERS)]
			t = m.groups()
			if len(t) >= 1:
				HEtemp[0] = float(t[0])
				gotHE[0] = True
			if len(t) >= 2:
				HEtarget[0] = float(t[1])
				gotHE[0] = True
			if len(t) >= 3:
				self.setBedTemp(float(t[2]))
			if len(t) >= 4:
				self.setBedTarget(float(t[3]))
				
			m = self.toolre.findall(msg)
			if m:
				for t in m:
					tool = int(t[0])
					if tool >= 0 and tool < MAX_EXTRUDERS:
						HEtemp[tool] = float(t[1])
						HEtarget[tool] = float(t[2])
						gotHE[tool] = True

			for i in range(MAX_EXTRUDERS):
				if gotHE[i]:
					self.setHETemp(i, HEtemp[i])
					self.setHETarget(i, HEtarget[i])
	
			if self.reprap.M105pending:
				self.reprap.M105pending = False
				return True
			return False

		m = self.trpt2re.search(msg)
		if m:
			t = m.groups()
			tool = None
			gotHeTemp = False
			if len(t) >= 1:
				gotHeTemp = True
				HeTemp = float(t[0])
			if len(t) >= 2:
				tool = int(t[1])
			if len(t) >= 3:
				self.setBedTemp(float(t[2]))
				
			if gotHeTemp:
				self.setHETemp(tool, HeTemp)
			return False
		
		m = self.trpt3re.search(msg)
		if m:
			t = m.groups()
			tool = None
			gotHeTemp = False
			if len(t) >= 1:
				gotHeTemp = True
				HeTemp = float(t[0])
			if len(t) >= 2:
				tool = int(t[1])

			if gotHeTemp:
				self.setHETemp(tool, HeTemp)
			return False
		
		m = self.trpt4re.search(msg)
		if m:
			t = m.groups()
			tool = None
			if len(t) >= 1:
				self.setHETemp(tool, float(t[0]))
			if len(t) >= 2:
				self.setHETarget(tool, float(t[1]))
			if len(t) >= 3:
				self.setBedTemp(float(t[2]))
			if len(t) >= 4:
				self.setBedTarget(float(t[3]))

			return False
		
		m = self.speedrptre.search(msg)
		if m:
			fan = None
			feed = None
			flow = None
			t = m.groups()
			if len(t) >= 1:
				fan = float(t[0])
			if len(t) >= 2:
				feed = float(t[1])
			if len(t) >= 3:
				flow = float(t[2])
				
			if self.speedHandler is not None:
				self.speedHandler(fan, feed, flow)
			return False
		
		m = self.toolchgre.search(msg)
		if m:
			tool = None
			t = m.groups()
			if len(t) >= 1:
				tool = int(t[0])
				
			if tool is not None and self.toolHandler is not None:
				self.toolHandler(tool)
			return False
	
		return False

	def setHETarget(self, tool, val):
		if self.tempHandler is not None:
			self.tempHandler("target", "HE", tool, val)
	
	def setHETemp(self, tool, val):
		if self.tempHandler is not None:
			self.tempHandler("actual", "HE", tool, val)
	
	def setBedTarget(self, val):
		if self.tempHandler is not None:
			self.tempHandler("target", "Bed", None, val)
	
	def setBedTemp(self, val):
		if self.tempHandler is not None:
			self.tempHandler("actual", "Bed", None, val)
	
	def parseG(self, s, v):
		l = s.split()
		for p in l:
			if p.startswith(v):
				try:
					return float(p[1:])
				except:
					return None
		return None

class RepRap:
	def __init__(self, win, pname, port, baud, firmware):
		self.win = win
		self.log = self.win.log
		self.sender = None
		self.ready = False
		self.printerName = pname
		self.allowWhilePrinting = allow_while_printing_base[:]
		self.setFirmware(firmware)

		self.proxyWin = wx.Window(win, wx.ID_ANY)

		self.parser = RepRapParser(self)
		
		self.online = False
		self.printing = False
		self.forceGCode = False
		self.restarting = False
		self.restartData = None
		self.resetting = False

		self.timer = None
		self.cycle = 0
		self.suspendM105 = False
		self.M105pending = False
		
		self.priQ = Queue.Queue(0)
		self.mainQ = Queue.Queue(0)
		self.prtport = None
		self.positionHandler = None
		self.eventHandler = None
		self.sdEventHandler = None
		
		self.listener = ListenThread(self.proxyWin, self, port, baud, firmware)

		self.proxyWin.Bind(EVT_REPRAP_UPDATE, self.reprapEvent)
		
		self.sender = SendThread(self.proxyWin, self, firmware, self.priQ, self.mainQ)
		self.sender.setCheckSum(True)
		self.sender.reportConnection(self.online, self.prtport)
		self.ready = True
		
	def setLogLevel(self, level):
		self.sender.setLogLevel(level)
		
	def reset(self):
		self.resetting = True
		self.suspendTempProbe(True)
		self.clearPrint()
		self.listener.resetPort()
	
	def registerTempHandler(self, handler):
		self.parser.setTempHandler(handler)
		
	def registerSpeedHandler(self, handler):
		self.parser.setSpeedHandler(handler)
		
	def registerToolHandler(self, handler):
		self.parser.setToolHandler(handler)
		
	def registerPositionHandler(self, handler):
		self.positionHandler = handler
		
	def registerEventHandler(self, handler):
		self.eventHandler = handler
		
	def registerSdEventHandler(self, hobj):
		self.parser.setSdEventHandler(hobj)
		
	def startFirmwareCollection(self, fw):
		self.parser.startFirmwareCollection(fw)
		
	def endFirmwareCollection(self):
		self.parser.endFirmwareCollection()
		
	def startSDDelete(self):
		self.parser.startSDDelete()
		self.sendNow("M20")

	def terminate(self):
		try:
			self.timer.Stop()
		except:
			pass

		senderKilled = False
		try:
			self.sender.kill()
		except:
			senderKilled = True

		listenerKilled = False
		try:
			self.listener.kill()
		except:
			listenerKilled = True

		while not (senderKilled and listenerKilled):
			if not senderKilled:
				senderKilled = self.sender.isKilled()
			if not listenerKilled:
				listenerKilled = self.listener.isKilled()
			time.sleep(0.1)
		
	def getPrinterName(self):
		return self.printerName
			
	def setFirmware(self, fw):
		self.firmware = fw
		if fw in ["TEACUP" ]:
			self.addToAllowedCommands("M130")
			self.addToAllowedCommands("M131")
			self.addToAllowedCommands("M132")
			self.addToAllowedCommands("M133")
			self.addToAllowedCommands("M134")
			self.addToAllowedCommands("M136")
		elif fw in [ "MARLIN" ]:
			self.addToAllowedCommands("M107")
			self.addToAllowedCommands("M220")
			self.addToAllowedCommands("M221")
			self.addToAllowedCommands("M301")
			self.addToAllowedCommands("M302")
			self.addToAllowedCommands("M303")
			self.addToAllowedCommands("M500")
			self.addToAllowedCommands("M501")
			self.addToAllowedCommands("M502")
			self.addToAllowedCommands("M503")

	def addToAllowedCommands(self, cmd):
		self.allowWhilePrinting.append(cmd)

	def endWait(self):
		if self.sender is not None:
			self.sender.endWait()
		
	def setResendFrom(self, n):
		if self.sender is not None:
			self.sender.setResendFrom(n)

	def getPrintPosition(self):
		if self.sender and self.sender.isPrinting:
			return self.sender.getPrintIndex()
		else:
			return None
		
	def startPrint(self, data):
		self.sender.resetCounters()
		self.listener.resetCounters()
		self._sendCmd(RepRapCmdEnum.CMD_STARTPRINT)
		for l in data:
			if ";" in l:
				ls = l.split(";")[0].rstrip()
			else:
				ls = l.rstrip()
			if ls != "":
				self._send(ls)

		self._sendCmd(RepRapCmdEnum.CMD_ENDOFPRINT, priority=False)			
		self.printing = True
		self.paused = False
		
	def pausePrint(self):
		self._sendCmd(RepRapCmdEnum.CMD_STOPPRINT)
		self.printing = False
		self.paused = True
		
	def resumePrint(self):
		self._sendCmd(RepRapCmdEnum.CMD_RESUMEPRINT)
		self.printing = True
		self.paused = False
		
	def getCounters(self):
		return self.sender.getCounters(), self.listener.getCounters()
		
	def restartPrint(self, data):
		self.sender.resetCounters()
		self.listener.resetCounters()
		self.restarting = True
		self.restartData = data
		self._sendCmd(RepRapCmdEnum.CMD_DRAINQUEUE)
		
	def clearPrint(self):
		self._sendCmd(RepRapCmdEnum.CMD_DRAINQUEUE)
		
	def reprapEvent(self, evt):
		if evt.event == RepRapEventEnum.QUEUE_DRAINED:
			if self.restarting:
				self.startPrint(self.restartData)
				self.printing = True
				self.paused = False
				self.restarting = False
				self.restartData = None
			else:
				self.printing = False
				self.paused = False
		elif evt.event == RepRapEventEnum.CONNECTED:
			self.online = True
			self.prtport = evt.prtport
			if self.ready:
				self.sender.reportConnection(True, self.prtport)
			wx.CallLater(1000, self.startTimer)
			if not self.resetting:
				self.win.reportConnection(True, self.printerName)
			else:
				self.resetting = False

		elif evt.event == RepRapEventEnum.DISCONNECTED:
			self.online = False
			self.prtport = None
			if self.ready:
				self.sender.reportConnection(False, None)
			self.stopTimer()
			if not self.resetting:
				self.win.reportConnection(False, self.printerName)

		elif evt.event == RepRapEventEnum.RECEIVED_MSG:
			if TRACE:
				print "==> received message (%s)" % evt.msg
			if not self.parser.parseMsg(evt.msg):
				self.log(evt.msg.rstrip())
		else:
			if self.eventHandler is not None:
				if TRACE:
					print "passing event to handler ", evt.event
					try:
						print evt.msg
					except:
						pass
				self.eventHandler(evt)
			else:
				if TRACE:
					print "no handler yet for ", evt.event
					try:
						print evt.msg
					except:
						pass

	def startTimer(self):
		self.cycle = 0
		self.M105pending = False
		self.suspendM105 = False
		self.timer = wx.Timer(self.proxyWin)
		self.proxyWin.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
		self.timer.Start(1000)

	def stopTimer(self):
		if not self.timer is None:
			self.timer.Stop()
			self.timer = None

	def OnTimer(self, evt):
		self.cycle += 1

		if self.cycle % TEMPINTERVAL == 0:
			if self.suspendM105:
				self.M105pending = False
			elif not self.M105pending:
				self.M105pending = True
				self.sendNow("M105", True)

		if self.cycle % POSITIONINTERVAL == 0:
				n = self.getPrintPosition()
				if n is not None and self.positionHandler is not None:
					self.positionHandler(n)

	def suspendTempProbe(self, flag=True):
		self.suspendM105 = flag
		if flag:
			self.m105pending = False
		
	def printStopped(self):
		self.printing = False
		self.paused = True
		
	def printComplete(self):
		self.printing = False
		self.paused = False
		
	def isPrinting(self):
		return self.printing
				
	def sendNow(self, cmd, eatOK = False):
		verb = cmd.split()[0]
		if not self.online:
			self.log("Printer %s is off-line" % self.printerName)
			return False
		
		elif self.printing and verb not in self.allowWhilePrinting:
			if self.forceGCode:
				if eatOK:
					self.listener.setEatOK()
				self.log("Command (%s) forced" % cmd)
				return self._send(cmd, priority=True)
			else:
				self.log("Command not allowed while printing")
				return False
		else:
			if eatOK:
				self.listener.setEatOK()
			return self._send(cmd, priority=True)
				
	def send(self, cmd):
		return self._send(cmd)

	def _send(self, command, priority=False):
		if not self.prtport:
			return False
		
		if priority:		
			self.priQ.put((RepRapCmdEnum.CMD_GCODE, command))
		else:
			self.mainQ.put((RepRapCmdEnum.CMD_GCODE, command))
			
		return True
	
	def _sendCmd(self, cmd, priority=True):
		if priority:
			self.priQ.put((cmd, ""))
		else:
			self.mainQ.put((cmd, ""))
