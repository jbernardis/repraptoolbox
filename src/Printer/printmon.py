import wx
import re
import os
import time
import inspect

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))

gcRegex = re.compile("[-]?\d+[.]?\d*")

from cnc import CNC
from reprapenums import RepRapEventEnum 
from gcframe import GcFrame
from properties import PropertiesDlg
from propenums import PropertyEnum
from printstateenum import PrintState
from tools import formatElapsed
from gcsuffix import parseGCSuffix
from sdcard import SDCard

BUTTONDIM = (48, 48)
BUTTONDIMWIDE = (96, 48)
	
RECORD_TIMES = True

class PrintButton(wx.BitmapButton):
	def __init__(self, parent, images):
		self.imgPrint = images.pngPrint
		self.imgRestart = images.pngRestart
		
		wx.BitmapButton.__init__(self, parent, wx.ID_ANY, self.imgPrint, size=BUTTONDIM)
		self.setPrint()
		
	def setPrint(self):
		self.SetBitmap(self.imgPrint)
		self.SetToolTipString("Start printing")
		
	def setRestart(self):
		self.SetBitmap(self.imgRestart)
		self.SetToolTipString("Restart print from the beginning")

class PauseButton(wx.BitmapButton):
	def __init__(self, parent, images):
		wx.BitmapButton.__init__(self, parent, wx.ID_ANY, images.pngPause, size=BUTTONDIM)
		self.setPause()
		
	def setPause(self):
		self.SetToolTipString("Pause printing")
		
	def setResume(self):
		self.SetToolTipString("Resume print from the paused point")

class PrintMonitorDlg(wx.Frame):
	def __init__(self, parent, wparent, reprap, prtName):
		self.parent = parent
		self.wparent = wparent
		self.log = self.parent.log
		self.reprap = reprap
		self.settings = self.parent.settings
		self.images = self.parent.images
		self.state = PrintState.idle
		self.oldState = None
		self.gcodeLoaded = False
		self.gcodeFile = None
		self.printerName = prtName
		self.layerMap = []
		
		self.currentLayer = 0
		self.maxTool = 0
		self.eUsed = [0.0, 0.0, 0.0, 0.0]
		self.totalTime = 0
		self.totalTimeStr = ""
		self.layerTimes = []
		self.layerTimeStr = []
		self.layerRange = (0, 0)

		
		self.gObj = None
		self.printLayer = 0
		self.printPosition = None
		
		title = self.buildTitle()
		wx.Frame.__init__(self, wparent, wx.ID_ANY, title=title)
		self.Show()
		ico = wx.Icon(os.path.join(cmdFolder, "images", "printmon.png"), wx.BITMAP_TYPE_PNG)
		self.SetIcon(ico)
			
		if self.settings.hassdcard:
			self.sdcard = SDCard(self.parent, self, self.reprap, self.log)
		else:
			self.sdcard = None

		self.gcf = GcFrame(self, self.gObj, self.settings)
		
		ht = self.gcf.GetSize().Get()[1] - BUTTONDIM[1]*2 - 20
		
		self.slLayers = wx.Slider(
			self, wx.ID_ANY, 0, 0, 1000, size=(-1, ht), 
			style=wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS | wx.SL_INVERSE)
		self.Bind(wx.EVT_SCROLL, self.onLayerScroll, self.slLayers)
		self.slLayers.Enable(False)
		
		self.cbShowMoves = wx.CheckBox(self, wx.ID_ANY, "Show moves")
		self.cbShowMoves.SetValue(self.settings.showmoves)
		self.Bind(wx.EVT_CHECKBOX, self.onShowMoves, self.cbShowMoves)

		self.cbShowPrevious = wx.CheckBox(self, wx.ID_ANY, "Show previous layer")
		self.cbShowPrevious.SetValue(self.settings.showprevious)
		self.Bind(wx.EVT_CHECKBOX, self.onShowPrevious, self.cbShowPrevious)

		self.cbSyncPrint = wx.CheckBox(self, wx.ID_ANY, "Sync with print")
		self.cbSyncPrint.SetValue(True)
		self.Bind(wx.EVT_CHECKBOX, self.onSyncPrint, self.cbSyncPrint)
		
		self.bImport = wx.BitmapButton(self, wx.ID_ANY, self.images.pngImport, size=BUTTONDIM)
		self.bImport.SetToolTipString("Import G Code file from toolbox")
		self.Bind(wx.EVT_BUTTON, self.onImport, self.bImport)
		
		self.bOpen = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFileopen, size=BUTTONDIM)
		self.bOpen.SetToolTipString("Open a G Code file")
		self.Bind(wx.EVT_BUTTON, self.onOpenFile, self.bOpen)
		
		self.Bind(wx.EVT_CLOSE, self.onClose)
		
		self.bPrint = PrintButton(self, self.images)
		self.bPrint.Enable(False)
		self.Bind(wx.EVT_BUTTON, self.onPrint, self.bPrint)
		
		self.bPause = PauseButton(self, self.images)
		self.bPause.Enable(False)
		self.Bind(wx.EVT_BUTTON, self.onPause, self.bPause)
		
		self.bSdPrintTo = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSdprintto, size=(BUTTONDIMWIDE))
		self.bSdPrintTo.Enable(False)
		self.Bind(wx.EVT_BUTTON, self.onSdPrintTo, self.bSdPrintTo)
		
		self.bSdPrintFrom = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSdprintfrom, size=(BUTTONDIMWIDE))
		self.bSdPrintFrom.Enable(False)
		self.Bind(wx.EVT_BUTTON, self.onSdPrintFrom, self.bSdPrintFrom)
		
		self.bSdDelete = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSddelete, size=(BUTTONDIM))
		self.bSdDelete.Enable(False)
		self.Bind(wx.EVT_BUTTON, self.onSdDelete, self.bSdDelete)
		
		self.bUp = wx.BitmapButton(self, wx.ID_ANY, self.images.pngUp, size=BUTTONDIM)
		self.bUp.SetToolTipString("Move up one layer")
		self.Bind(wx.EVT_BUTTON, self.onUp, self.bUp)
		self.bUp.Enable(False)
		
		self.bDown = wx.BitmapButton(self, wx.ID_ANY, self.images.pngDown, size=BUTTONDIM)
		self.bDown.SetToolTipString("Move down one layer")
		self.Bind(wx.EVT_BUTTON, self.onDown, self.bDown)
		self.bDown.Enable(False)
		
		szGcf = wx.BoxSizer(wx.HORIZONTAL)
		szGcf.AddSpacer((10, 10))
		szGcf.Add(self.gcf)
		szGcf.AddSpacer((10, 10))

		szNav = wx.BoxSizer(wx.VERTICAL)
		szNav.Add(self.bUp, 1, wx.ALIGN_CENTER_HORIZONTAL, 1)
		szNav.AddSpacer((10, 10))
		szNav.Add(self.slLayers)
		szNav.AddSpacer((10, 10))
		szNav.Add(self.bDown, 1, wx.ALIGN_CENTER_HORIZONTAL, 1)

		szGcf.Add(szNav)
		szGcf.AddSpacer((10, 10))
		
		szOpts = wx.BoxSizer(wx.HORIZONTAL)
		szOpts.AddSpacer((10, 10))
		szOpts.Add(self.cbShowMoves)
		szOpts.AddSpacer((10, 10))
		szOpts.Add(self.cbShowPrevious)
		szOpts.AddSpacer((10, 10))
		szOpts.Add(self.cbSyncPrint)
		szOpts.AddSpacer((10, 10))
		
		szBtn = wx.BoxSizer(wx.HORIZONTAL)
		szBtn.AddSpacer((10, 10))
		szBtn.Add(self.bImport)
		szBtn.AddSpacer((10, 10))
		szBtn.Add(self.bOpen)
		szBtn.AddSpacer((20, 20))
		szBtn.Add(self.bPrint)
		szBtn.AddSpacer((10, 10))
		szBtn.Add(self.bPause)
		if self.sdcard:
			szBtn.AddSpacer((20, 10))
			szBtn.Add(self.bSdPrintTo)
			szBtn.AddSpacer((10, 10))
			szBtn.Add(self.bSdPrintFrom)
			szBtn.AddSpacer((10, 10))
			szBtn.Add(self.bSdDelete)
			
		szBtn.AddSpacer((10, 10))
		
		szDlg = wx.BoxSizer(wx.VERTICAL)
		szDlg.AddSpacer((10, 10))
		szDlg.Add(szGcf)
		szDlg.AddSpacer((10, 10))
		szDlg.Add(szOpts)
		szDlg.AddSpacer((10, 10))
		szDlg.Add(szBtn)
		szDlg.AddSpacer((10, 10))
		
		self.SetSizer(szDlg)
		self.Fit()
		self.Layout()	
		
		self.propDlg = PropertiesDlg(self, wparent, self.printerName)
		self.propDlg.Show()
		if not self.settings.propposition is None:
			self.propDlg.SetPosition(self.settings.propposition)
	
		self.enableButtonsByState()	
		self.reprap.registerPositionHandler(self.updatePrintPosition)
		self.reprap.registerEventHandler(self.reprapEvent)
		self.reprap.registerSdEventHandler(self.sdcard)
		self.wparent.registerPrinterStatusReporter(self.printerName, self)
		
	def getStatusReport(self):
		r = self.propDlg.getStatusReport()
		r["PrintStatus"] = PrintState.label[self.state]
		return r

	def buildTitle(self):		
		t = "%s print monitor" % self.printerName
		
		if self.gcodeLoaded:
			if len(self.gcodeFile) > 45:
				t += " - %s" % os.path.basename(self.gcodeFile)
			else:
				t += " - %s" % self.gcodeFile
			
		return t
	
	def rememberPositions(self):
		self.settings.propposition = self.propDlg.GetPosition()
	
	def isPrinting(self):
		return self.state in [PrintState.printing, PrintState.sdprintingto, PrintState.sdprintingfrom]
				
	def onClose(self, evt):
		if self.isPrinting():
			dlg = wx.MessageDialog(self, 'Cannot exit with printing active',
					   "Printer is active",
					   wx.OK | wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()
			return
		self.terminate()

	def terminate(self):
		self.reprap.registerPositionHandler(None)
		self.reprap.registerEventHandler(None)
		self.wparent.registerPrinterStatusReporter(self.printerName, None)
		self.parent.closePrintMon()
		self.propDlg.Destroy()
		self.Destroy()
		
	def onShowMoves(self, evt):
		v = self.cbShowMoves.GetValue()
		self.settings.showmoves = v
		self.gcf.setShowMoves(v)
	
	def onShowPrevious(self, evt):
		v = self.cbShowPrevious.GetValue()
		self.settings.showprevious = v
		self.gcf.setShowPrevious(v)
	
	def onSyncPrint(self, evt):
		v = self.cbSyncPrint.GetValue()
		self.gcf.setSyncWithPrint(v)
		
	def onLayerScroll(self, evt):
		v = self.slLayers.GetValue()
		if v == self.currentLayer:
			return
		
		self.gcf.setLayer(v)
		self.changeLayer(v)
		
	def onUp(self, evt):
		lmax = self.slLayers.GetRange()[1]
		if self.currentLayer >= lmax:
			return
		
		v = self.currentLayer + 1
		self.gcf.setLayer(v)
		self.changeLayer(v)
	
	def onDown(self, evt):
		if self.currentLayer <= 0:
			return
		
		v = self.currentLayer - 1
		self.gcf.setLayer(v)
		self.changeLayer(v)
		
	def onImport(self, evt):
		fn = self.wparent.importGcFile()
		if fn is None:
			return
		
		self.loadGFile(fn)
		
	def onOpenFile(self, evt):
		wildcard = "GCode (*.gcode)|*.gcode|"	 \
			"All files (*.*)|*.*"
			
		dlg = wx.FileDialog(
			self, message="Choose a GCode file",
			defaultDir=self.settings.lastdirectory, 
			defaultFile="",
			wildcard=wildcard,
			style=wx.OPEN)

		rc = dlg.ShowModal()
		if rc == wx.ID_OK:
			path = dlg.GetPath().encode('ascii','ignore')
		dlg.Destroy()
		if rc != wx.ID_OK:
			return
		
		self.loadGFile(path)
		
	def loadGFile(self, path):
		self.settings.lastdirectory = os.path.dirname(path)
		
		self.loadGCode(path)
		
		if self.gObj is None:
			lmax = 1
			self.slLayers.Enable(False)
			self.bUp.Enable(False)
			self.bDown.Enable(False)
		else:
			lmax = self.gObj.layerCount()-1
			self.slLayers.Enable(True)
			self.bUp.Enable(True)
			self.bDown.Enable(True)
			
		self.slLayers.SetRange(0, lmax)
		self.slLayers.SetPageSize(int(lmax/10))
		
		self.gcf.loadModel(self.gObj)
		self.changeLayer(0)
		
		self.state = PrintState.idle
		self.oldState = None
		self.enableButtonsByState()
		t = self.buildTitle()
		self.SetTitle(t)
		self.propDlg.setPrintStatus(PrintState.idle)
		
	def loadGCode(self, fn):
		def gnormal(s):
			if ";" in s:
				return s.split(";")[0].rstrip()
			else:
				return s.rstrip()
			
		self.gcodeFile = None
		self.gcodeLoaded = False
		self.gcode = []
		self.gObj = None
		self.maxLine = 0
		self.totalTime = 0
		self.totalTimeStr = ""
		self.layerTimes = []
		self.layerTimeStr = []
		self.propDlg.clearAllProperties()
		self.reprap.clearPrint()
		if fn is None:
			return
		
		try:
			gc = list(open(fn))
		except:
			self.log("Error opening file %s" % fn)
			self.gcode = []
			self.gObj = None
			self.gcodeLoaded = False
			return

		self.gcode = [s for s in map(gnormal, gc) if s.strip() != ""]	
		self.gObj = self.buildModel()
		self.maxLine = self.gObj.getMaxLine()
		self.eUsed = self.gObj.getFilament()
		
		self.gcodeLoaded = True
		self.gcodeFile = pfn = fn
		if len(pfn) > 45:
			pfn = os.path.basename(fn)
		self.propDlg.setProperty(PropertyEnum.fileName, pfn)
		ftime = time.strftime('%y/%m/%d-%H:%M:%S', time.localtime(os.path.getmtime(fn))) 
		self.propDlg.setProperty(PropertyEnum.sliceTime, ftime)
		self.propDlg.setProperty(PropertyEnum.printEstimate, self.totalTimeStr)
		
		if self.settings.nextruders < self.maxTool+1:
			self.log("G Code file uses more tools (%d) than printer is equipped with (%d)" % (self.maxTool+1, self.settings.nextruders))
			
		slCfg, filSiz, tempsHE, tempsBed = parseGCSuffix(gc)
		
		if tempsBed == "??":
			tBed = 0
		else:
			try:
				tBed = int(tempsBed)
			except:
				tBed = 0
		
		if tempsHE == "??":
			tHe = [0] * self.settings.nextruders
		else:
			try:
				x = [int(x) for x in re.split(", *", tempsHE)] + [0]*self.settings.nextruders
				tHe = x[:self.settings.nextruders]
			except:
				tHe = [0] * self.settings.nextruders
		
		self.parent.registerGCodeTemps(tHe, tBed)
				
		self.propDlg.setProperty(PropertyEnum.slicerCfg, slCfg)	
		self.propDlg.setProperty(PropertyEnum.filamentSize, filSiz)	
		self.propDlg.setProperty(PropertyEnum.temperatures, "HE:%s  BED:%s" % (tempsHE, tempsBed))
		
	def updatePrintPosition(self, position):
		self.printLayer = self.getLayerByPosition(position)
		self.printPosition = position
		if self.state in [PrintState.printing, PrintState.sdprintingto]:
			posString = "%d/%d" % (position, self.maxLine)
			if self.maxLine != 0:
				pct = float(position) / float(self.maxLine) * 100.0
				posString += " (%.1f%%)" % pct
			self.propDlg.setProperty(PropertyEnum.position, posString)
			self.gcf.setPrintPosition(position)
			lx = self.gcf.getCurrentLayer()
			if lx != self.currentLayer:
				self.changeLayer(lx)
			
			layersSplit = self.sumLayerTimes(self.printLayer)
			layerSplit  = self.partialPrintingLayer()
			
			self.elapsed = time.time() - self.startTime
			expected = layersSplit[0] + layerSplit[0]
			elapsedStr = "%s (expected: %s)" % (formatElapsed(self.elapsed), formatElapsed(expected))
			self.propDlg.setProperty(PropertyEnum.elapsed, elapsedStr)
			
			self.remaining = layersSplit[1] + layerSplit[1]
			self.propDlg.setProperty(PropertyEnum.remaining, formatElapsed(self.remaining))
			#TODO - probably don't need all the various time estimates when printing TO CD
			# BUT IT MAY BREAK LOGIC BELOW (update time until) that rely on these values
			
			newEta = time.time() + self.remaining
			revisedStr = time.strftime('%H:%M:%S', time.localtime(newEta))
			tdiff = newEta - self.origEta
			if tdiff < 0:
				revisedStr += "  (%s ahead of estimate)" % formatElapsed(-tdiff)
			elif tdiff > 0:
				revisedStr += "  (%s behind estimate)" % formatElapsed(tdiff)
			self.propDlg.setProperty(PropertyEnum.revisedEta, revisedStr)
			self.updateTimeUntil()
			
		elif self.state == PrintState.sdprintingfrom:
			#TODO Need to convey print position when printing from SD card
			pass

	def getLayerByPosition(self, pos):
		for lx in range(len(self.layerMap)):
			if self.layerMap[lx][0] <= pos and pos <= self.layerMap[lx][1]:
				return lx
			
		return 0
			
	def partialPrintingLayer(self):
		f, l = self.gObj.getGCodeLines(self.printLayer)
		if f <= self.printPosition and self.printPosition <= l:
			done = self.printPosition - f
			todo = l - self.printPosition + 1
			total = l - f + 1
			
			lt = self.layerTimes[self.printLayer]
			pctDone = float(done) / float(total)
			pctToDo = float(todo) / float(total)
			return (pctDone*lt, pctToDo*lt)
		else:
			return (0.0, 0.0)

	def sumLayerTimes(self, lx):
		tBefore = sum(self.layerTimes[:lx])
		tAfter = sum(self.layerTimes[lx+1:])
		return (tBefore, tAfter)
	
	def sumLayerRangeTime(self, slx, elx):
		return sum(self.layerTimes[slx:elx])
			
	def changeLayer(self, lx):
		self.currentLayer = lx
		self.slLayers.SetValue(lx)
		ht = self.gObj.getLayerHeight(lx)
		if ht is None:
			self.propDlg.setProperty(PropertyEnum.layerNum, "%d / %d" % (lx, self.gObj.layerCount()))
		else:
			self.propDlg.setProperty(PropertyEnum.layerNum, "%d / %d (%.2f mm) " % (lx, self.gObj.layerCount(), ht))
			
		f, l = self.gObj.getGCodeLines(lx)
		if f is None:
			self.propDlg.setProperty(PropertyEnum.gCodeRange, "")
			self.layerRange = (0, 0)
		else:
			self.propDlg.setProperty(PropertyEnum.gCodeRange, "%d - %d" % (f, l))
			self.layerRange = (f, l)
			
		x0, y0, xn, yn = self.gObj.getLayerMinMaxXY(lx)
		if x0 is None:
			self.propDlg.setProperty(PropertyEnum.minMaxXY, "")
		else:
			self.propDlg.setProperty(PropertyEnum.minMaxXY, "(%.2f, %.2f) - (%.2f, %.2f)" % (x0, y0, xn, yn))
			
		le, prior, after = self.gObj.getLayerFilament(lx)
		
		s = []
		for i in range(self.settings.nextruders):
			s.append("%.2f/%.2f    <: %.2f    >: %.2f" % (le[i], self.eUsed[i], prior[i], after[i]))
			
		self.propDlg.setProperty(PropertyEnum.filamentUsed, s)
		
		self.propDlg.setProperty(PropertyEnum.layerPrintTime, "%s / %s" % (self.layerTimeStr[lx], self.totalTimeStr))
	
		self.updateTimeUntil()
		
	def updateTimeUntil(self):	
		if self.currentLayer <= self.printLayer:
			self.propDlg.setProperty(PropertyEnum.timeUntil, "")
		elif self.printPosition is None:
			t = sum(self.layerTimes[:self.currentLayer])
			self.propDlg.setProperty(PropertyEnum.timeUntil, formatElapsed(t))
		else:
			t = sum(self.layerTimes[self.printLayer+1:self.currentLayer]) + self.partialPrintingLayer()[1]
			self.propDlg.setProperty(PropertyEnum.timeUntil, formatElapsed(t))

		
	def reprapEvent(self, evt):
		if evt.event == RepRapEventEnum.PRINT_COMPLETE:
			# TODO - do I need special consideration here for print FROM SD
			if self.state == PrintState.sdprintingto:
				self.reprap.sendNow("M29 %s" % self.sdTargetFile)
				self.suspendTempProbe(False)
				self.setSDTargetFile(None)
			self.state = PrintState.idle
			self.oldState = None
			self.propDlg.setPrintStatus(PrintState.idle)
			self.gcf.setPrintPosition(-1)
			self.printPosition = None
			self.printLayer = 0
			self.enableButtonsByState()
			self.elapsed = time.time() - self.startTime
			cmpTime = time.time()
			expCmpTime = self.origEta - self.startTime
			cmpTimeStr = time.strftime('%H:%M:%S', time.localtime(cmpTime))
			self.log("Print completed at %s" % (cmpTimeStr))
			self.log("Total print time of %s - expected print time %s" %
					(formatElapsed(self.elapsed), formatElapsed(expCmpTime)))
			self.reprap.printComplete()
		elif evt.event == RepRapEventEnum.PRINT_STOPPED:
			self.oldState = self.state
			self.state = PrintState.paused
			self.propDlg.setPrintStatus(PrintState.paused)
			self.enableButtonsByState()
			self.reprap.printStopped()
		elif evt.event == RepRapEventEnum.PRINT_STARTED:
			pass
		elif evt.event == RepRapEventEnum.PRINT_RESUMED:
			pass
		elif evt.event == RepRapEventEnum.PRINT_ERROR:
			self.log("Error communicating with printer")
		elif evt.event == RepRapEventEnum.PRINT_SENDGCODE:
			self.log(evt.msg)
		else:
			print "unknown reprap event: ", evt.event
				
	def buildModel(self):
		cnc = CNC(self.settings.acceleration)
		if RECORD_TIMES:
			print "recording g code times in /tmp/gcodeTimes"
			fp = open("/tmp/gcodeTimes", "w")
		
		ln = -1
		for gl in self.gcode:
			ln += 1
			
			p = re.split("\\s+", gl, 1)
			
			params = {}
			if not (p[0].strip() in ["M117", "m117"]):
				if len(p) >= 2:
					self.paramStr = p[1]
					
					if "X" in self.paramStr:
						params["X"] = self._get_float("X")
						
					if "Y" in self.paramStr:
						params["Y"] = self._get_float("Y")
			
					if "Z" in self.paramStr:
						params["Z"] = self._get_float("Z")
			
					if "E" in self.paramStr:
						params["E"] = self._get_float("E")
			
					if "F" in self.paramStr:
						params["F"] = self._get_float("F")
			
					if "S" in self.paramStr:
						params["S"] = self._get_float("S")
			
					if "P" in self.paramStr:
						params["P"] = self._get_float("P")
			
			t = cnc.execute(p[0], params, ln)
			if RECORD_TIMES:
				fp.write("(%s) (%.3f)\n" % (gl, t))
			
		if RECORD_TIMES:
			fp.close()
			
		gobj = cnc.getGObject()
		gobj.setMaxLine(ln)
		self.maxTool = cnc.getMaxTool()
		self.totalTime, self.layerTimes = cnc.getTimes()
		self.layerMap = []				
		for lx in range(len(gobj)):
			self.layerMap.append(gobj.getGCodeLines(lx))

		self.totalTimeStr = formatElapsed(self.totalTime)
		self.layerTimeStr = [formatElapsed(s) for s in self.layerTimes]
		return gobj
				
	def _get_float(self,which):
		try:
			return float(gcRegex.findall(self.paramStr.split(which)[1])[0])
		except:
			print "exception: ", self.paramStr
			
	def enableButtonsByState(self):
		if self.state == PrintState.idle:
			self.bImport.Enable(True)
			self.bOpen.Enable(True)
			if self.sdcard:
				self.bSdPrintTo.Enable(self.gcodeLoaded)
				self.bSdPrintFrom.Enable()
				self.bSdDelete.Enable()
				
			if self.gcodeLoaded:
				self.bPrint.Enable(True)
				self.bPrint.setPrint()
				self.bPause.Enable(False)
				self.bPause.setPause()
			else:
				self.bPrint.Enable(False)
				self.bPause.Enable(False)
		elif self.state in [PrintState.printing, PrintState.sdprintingto]:
			self.bImport.Enable(False)
			self.bOpen.Enable(False)
			self.bPrint.Enable(False)
			self.bPrint.setPrint()
			self.bPause.Enable(True);
			self.bPause.setPause()
			if self.sdcard:
				self.bSdPrintTo.Enable(False)
				self.bSdPrintFrom.Enable(False)
				self.bSdDelete.Enable(False)
		elif self.state == PrintState.sdprintingfrom:
			#TODO - what makes sense here
			pass
		elif self.state == PrintState.paused:
			self.bImport.Enable(True)
			self.bOpen.Enable(True)
			self.bPrint.Enable(True)
			self.bPrint.setRestart()
			self.bPause.Enable(True);
			self.bPause.setResume()
			if self.sdcard:
				self.bSdPrintTo.Enable(self.gcodeLoaded)
				self.bSdPrintFrom.Enable()
				self.bSdDelete.Enable()
			
	def emulatePrintButton(self):
		if self.state in [PrintState.printing, PrintState.sdprintingto, PrintState.sdprintingfrom]:
			self.log("Already printing")
		elif not self.bPrint.IsEnabled():
			self.log("Unable to print right now")
		else:
			self.onPrint(None)
			
	def reset(self):
		#TODO - cleanup if was sdprintingfrom
		self.state = PrintState.idle
		self.oldState = None
		self.suspendTempProbe(False)
		self.setSDTargetFile(None)
		self.propDlg.setPrintStatus(PrintState.idle)
		self.enableButtonsByState()
			
	def onPrint(self, evt):
		oldState = self.state
		self.state = PrintState.printing
		self.propDlg.setPrintStatus(PrintState.printing)
		self.enableButtonsByState()
	
		self.printPos = 0
		self.startTime = time.time()
		self.endTime = None
		self.origEta = self.startTime + self.totalTime
		self.elapsed = 0
		self.remaining = self.totalTime
		if oldState == PrintState.paused:
			action = "restarted"
			self.reprap.restartPrint(self.gcode)
		else:
			action = "started"
			self.reprap.startPrint(self.gcode)
		stime = time.strftime('%H:%M:%S', time.localtime(self.startTime))
		self.propDlg.setProperty(PropertyEnum.startTime, stime)
		self.propDlg.setProperty(PropertyEnum.origEta, 
					time.strftime('%H:%M:%S', time.localtime(self.origEta)))
		self.propDlg.setProperty(PropertyEnum.elapsed, formatElapsed(self.elapsed))
		self.propDlg.setProperty(PropertyEnum.remaining, formatElapsed(self.remaining))
		self.propDlg.setProperty(PropertyEnum.revisedEta, "")
		self.log("Print %s at %s" % (action, stime))



		
	def onSdPrintFrom(self, evt):
		print "sd print from"
				
	def doSDPrintFrom(self, evt):
		self.printing = False
		self.paused = False
		self.sdpaused = False
		self.sdprintingfrom = True
		self.sdStartTime = time.time()
		#self.infoPane.setSDStartTime(self.sdStartTime)
		self.state = PrintState.printing
		#self.propDlg.setPrintStatus(PrintState.printing)
		self.enableButtonsByState()
		self.sdcard.startPrintFromSD()
		
	def cancelSDPrintFrom(self):
		self.sdprintingfrom = False
		self.printing = False
		self.paused = False
		self.state = PrintState.idle
		#self.propDlg.setPrintStatus(PrintState.printing)
		self.enableButtonsByState()
		
	def resumeSDPrintFrom(self, fn):
		#self.clearModel()
		self.reprap.sendNow("M23 " + fn[1].lower())
		self.reprap.sendNow("M24")
		self.sdprintingfrom = True
		#self.M27Timer.Start(M27Interval, True)
		self.sdpaused = False
		#self.infoPane.setMode(MODE_FROM_SD)
		self.enableButtonsByState()



		
	def onSdPrintTo(self, evt):
		self.sdcard.startPrintToSD()
		
	def resumeSDPrintTo(self, tfn):
		self.setSDTargetFile(tfn[1].lower())
		self.reprap.suspendTempProbe(True)
		self.reprap.sendNow("M28 %s" % self.sdTargetFile)
		self.printPos = 0
		self.startTime = time.time()
		self.endTime = None
		self.reprap.startPrint(self.gcode)
		
		self.origEta = self.startTime + self.totalTime
		self.elapsed = 0
		self.remaining = self.totalTime
				
		self.state = PrintState.sdprintingto
				
		stime = time.strftime('%H:%M:%S', time.localtime(self.startTime))
		self.propDlg.setProperty(PropertyEnum.startTime, stime)
		self.propDlg.setProperty(PropertyEnum.origEta, 
					time.strftime('%H:%M:%S', time.localtime(self.origEta)))
		self.propDlg.setProperty(PropertyEnum.elapsed, formatElapsed(self.elapsed))
		self.propDlg.setProperty(PropertyEnum.remaining, formatElapsed(self.remaining))
		self.propDlg.setProperty(PropertyEnum.revisedEta, "")
		self.log("Print to SD: %s started at %s" % (self.sdTargetFile, stime))

		self.enableButtonsByState()
		
	def setSDTargetFile(self, tfn):
		self.sdTargetFile = tfn
		self.propDlg.setSDTargetFile(tfn)
		
	def onSdDelete(self, evt):
		self.sdcard.startDeleteFromSD()
		
	def emulatePauseButton(self):
		if not self.bPause.IsEnabled():
			self.log("Unable to pause right now")
		else:
			self.onPause(None)
	
	def onPause(self, evt):
		if self.state == PrintState.paused:
			self.state = self.oldState
			if self.state is None:
				self.state = PrintState.printing
			self.propDlg.setPrintStatus(self.state)
			self.enableButtonsByState()
			self.reprap.resumePrint()
		else:
			self.oldState = self.state
			self.state = PrintState.paused
			self.propDlg.setPrintStatus(PrintState.paused)
			self.enableButtonsByState()
			self.reprap.pausePrint()
