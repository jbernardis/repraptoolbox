import wx
import re
import os
import time

gcRegex = re.compile("[-]?\d+[.]?\d*")

from cnc import CNC
from reprap import PRINT_COMPLETE, PRINT_STOPPED, PRINT_AUTOSTOPPED, PRINT_STARTED, PRINT_RESUMED
from gcframe import GcFrame
from properties import PropertiesDlg
from propenums import PropertyEnum


BUTTONDIM = (48, 48)

class PrintState:
	idle = 0
	printing = 1
	paused = 2

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
		self.log = self.parent.log
		self.reprap = reprap
		self.settings = self.parent.settings
		self.images = self.parent.images
		self.state = PrintState.idle
		self.gcodeLoaded = False
		self.gcodeFile = None
		self.printerName = prtName
		
		self.currentLayer = 0
		
		self.gObj = None
		
		title = self.buildTitle()
		wx.Frame.__init__(self, wparent, wx.ID_ANY, title=title)
		self.Show()
		
		self.gcf = GcFrame(self, self.gObj, self.settings)
		
		ht = self.gcf.GetSize().Get()[1]
		
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
		
		szGcf = wx.BoxSizer(wx.HORIZONTAL)
		szGcf.AddSpacer((10, 10))
		szGcf.Add(self.gcf)
		szGcf.AddSpacer((10, 10))
		szGcf.Add(self.slLayers)
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
		
		self.reprap.registerPositionHandler(self.updatePrintPosition)
		self.reprap.registerEventHandler(self.reprapEvent)

	def buildTitle(self):		
		t = "%s print monitor" % self.printerName
		
		if self.gcodeLoaded:
			t += " - %s" % self.gcodeFile
			
		return t
	
	def isPrinting(self):
		return self.state == PrintState.printing
				
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
		self.currentLayer = v
		
	def onImport(self, evt):
		fn = self.parent.importGcFile()
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
		else:
			lmax = self.gObj.layerCount()-1
			self.slLayers.Enable(True)
			
		self.slLayers.SetRange(0, lmax)
		self.slLayers.SetPageSize(int(lmax/10))
		
		self.gcf.loadModel(self.gObj)
		
		self.currentLayer = 0
		self.slLayers.SetValue(0)
		
		self.state = PrintState.idle
		self.enableButtonsByState()
		t = self.buildTitle()
		self.SetTitle(t)
		
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

		self.gcode = map(gnormal, gc)		
		self.gObj = self.buildModel()
		self.gcodeLoaded = True
		self.gcodeFile = fn
		self.propDlg.setProperty(PropertyEnum.fileName, fn)
	
	def updatePrintPosition(self, position):
		if self.state == PrintState.printing:
			self.propDlg.setProperty(PropertyEnum.position, "%d" % position)
			self.gcf.setPrintPosition(position)
		
	def reprapEvent(self, evt):
		if evt.event == PRINT_COMPLETE:
			self.state = PrintState.idle
			self.gcf.setPrintPosition(-1)
			self.enableButtonsByState()
		elif evt.event == PRINT_STOPPED:
			print "print stopped"
		elif evt.event == PRINT_AUTOSTOPPED:
			print "print auto-stopped"
		elif evt.event == PRINT_STARTED:
			print "print started"
		elif evt.event == PRINT_RESUMED:
			print "print resumed"
		else:
			print "unknown reprap event: ", evt.event
		
	def buildModel(self):
		cnc = CNC()
		
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
			
			cnc.execute(p[0], params, ln)
			
		gobj = cnc.getGObject()
		gobj.setMaxLine(ln)
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
			if self.gcodeLoaded:
				self.bPrint.Enable(True)
				self.bPrint.setPrint()
				self.bPause.Enable(False)
				self.bPause.setPause()
			else:
				self.bPrint.Enable(False)
				self.bPause.Enable(False)
		elif self.state == PrintState.printing:
			self.bImport.Enable(False)
			self.bOpen.Enable(False)
			self.bPrint.Enable(False)
			self.bPrint.setPrint()
			self.bPause.Enable(True);
			self.bPause.setPause()
		elif self.state == PrintState.paused:
			self.bImport.Enable(True)
			self.bOpen.Enable(True)
			self.bPrint.Enable(True)
			self.bPrint.setRestart()
			self.bPause.Enable(True);
			self.bPause.setResume()
		else:
			print "Exception: unknown print state: ", self.state
			
	def onPrint(self, evt):
		oldState = self.state
		self.state = PrintState.printing
		self.enableButtonsByState()
	
		self.printPos = 0
		self.startTime = time.time()
		self.endTime = None
		if oldState == PrintState.paused:
			action = "restarted"
			self.reprap.restartPrint(self.gcode)
		else:
			action = "started"
			self.reprap.startPrint(self.gcode)
		print "Print %s at %s" % (action, time.strftime('%H:%M:%S', time.localtime(self.startTime)))

	def onPause(self, evt):
		if self.state == PrintState.paused:
			self.state = PrintState.printing
			self.enableButtonsByState()
			self.reprap.resumePrint()
		else:
			self.state = PrintState.paused
			self.enableButtonsByState()
			self.reprap.pausePrint()
