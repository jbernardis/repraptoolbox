import wx.lib.newevent
import os
import sys, inspect

try:
	from agw import gradientbutton as GB
except ImportError: # if it's not there locally, try the wxPython lib.
	import wx.lib.agw.gradientbutton as GB

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
if cmdFolder not in sys.path:
	sys.path.insert(0, cmdFolder)

import subprocess, shlex

from images import Images
from settings import Settings
from STLViewer.viewdlg import StlViewDlg
from Plater.plater import PlaterDlg
from GEdit.gedit import GEditDlg
from Slic3r.Slic3r import Slic3rDlg
from CuraEngine.CuraEngine import CuraEngineDlg
from Printer.printer import PrinterDlg
from reprap import RepRap
from log import Logger
from HTTPServer import RepRapServer
from History.history import History
from History.historydlg import HistoryDlg
from pendant import Pendant, pendantCommand
from SliceQueue.slicequeue import SliceQueue, SliceQueueDlg
from GCodeQueue.gcodequeue import GCodeQueue, GCodeQueueDlg

(PendantCmdEvent, EVT_PENDANT_COMMAND) = wx.lib.newevent.NewEvent()
(PendantConnEvent, EVT_PENDANT_CONNECT) = wx.lib.newevent.NewEvent()


BUTTONDIM = (48, 48)
BUTTONDIMWIDE = (96, 48)
PBUTTONDIM = (144, 72)

white = wx.Colour(255, 255, 255)
black = wx.Colour(0, 0, 0)
grey = wx.Colour(128, 128, 128)

class ToolButton:
	def __init__(self, btn, bid, cmd, shell):
		self.button = btn
		self.bid = bid
		self.command = cmd
		self.shell = shell
		
	def getButton(self):
		return self.button
	
	def getBid(self):
		return self.bid
	
	def getCommand(self):
		return self.command
	
	def needsShell(self):
		return self.shell

class MyFrame(wx.Frame):
	def __init__(self):
		self.t = 0
		self.seq = 0
		self.exportedStlFile = None
		self.exportedGcFile = None
		self.modified = False
		wx.Frame.__init__(self, None, wx.ID_ANY, "RepRap Toolbox", size=(300, 300))
		self.Show()
		ico = wx.Icon(os.path.join(cmdFolder, "images", "rrtbico.png"), wx.BITMAP_TYPE_PNG)
		self.SetIcon(ico)
		
		self.dlgSlic3r = None
		self.dlgCuraEngine = None
		self.dlgViewStl = None
		self.dlgPlater = None
		self.dlgGEdit = None
		self.dlgGcQueue = None
		self.dlgStlQueue = None
		self.dlgHistory = None
		
		self.sliceQueue = SliceQueue()
		self.gcodeQueue = GCodeQueue()
		
		self.history = History()
		
		self.pendantAssignment = None
		self.pendantConnected = False
		
		self.settings = Settings(cmdFolder)
		self.images = Images(os.path.join(cmdFolder, "images"))
		
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.Bind(EVT_PENDANT_COMMAND, self.pendantCommandHandler)
		self.Bind(EVT_PENDANT_CONNECT, self.pendantConnectionHandler)
		self.logger = Logger(self)
		
		self.statusReportCB = {}
		
		self.bStlView = wx.BitmapButton(self, wx.ID_ANY, self.images.pngStlview, size=BUTTONDIM)
		self.bStlView.SetToolTipString("View an STL file")
		self.Bind(wx.EVT_BUTTON, self.doViewStl, self.bStlView)
		
		self.bPlater = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPlater, size=BUTTONDIM)
		self.bPlater.SetToolTipString("Arrange STL objects on a plate")
		self.Bind(wx.EVT_BUTTON, self.doPlater, self.bPlater)
		
		self.bSlic3r = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSlic3r, size=BUTTONDIM)
		self.bSlic3r.SetToolTipString("Invoke slic3r to slice a G Code file")
		self.Bind(wx.EVT_BUTTON, self.doSlic3r, self.bSlic3r)
		
		self.bCuraEngine = wx.BitmapButton(self, wx.ID_ANY, self.images.pngCura, size=BUTTONDIM)
		self.bCuraEngine.SetToolTipString("Invoke Cura Engine to slice a G Code file")
		self.Bind(wx.EVT_BUTTON, self.doCuraEngine, self.bCuraEngine)
		
		self.bGEdit = wx.BitmapButton(self, wx.ID_ANY, self.images.pngGedit, size=BUTTONDIM)
		self.bGEdit.SetToolTipString("Analyze/edit a G Code file")
		self.Bind(wx.EVT_BUTTON, self.doGEdit, self.bGEdit)

		self.bLogHideShow = wx.BitmapButton(self, wx.ID_ANY, self.images.pngLoghideshow, size=BUTTONDIM)
		self.bLogHideShow.SetToolTipString("Toggle the log window off and on")
		self.Bind(wx.EVT_BUTTON, self.onLogHideShow, self.bLogHideShow)

		self.bLogClear = wx.BitmapButton(self, wx.ID_ANY, self.images.pngClearlog, size=BUTTONDIM)
		self.bLogClear.SetToolTipString("Erase the log contents")
		self.Bind(wx.EVT_BUTTON, self.onLogClear, self.bLogClear)

		self.bLogSave = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSavelog, size=BUTTONDIM)
		self.bLogSave.SetToolTipString("Save log contents to a file")
		self.Bind(wx.EVT_BUTTON, self.onLogSave, self.bLogSave)

		self.bStlQueue = wx.BitmapButton(self, wx.ID_ANY, self.images.pngStlqueue, size=BUTTONDIMWIDE)
		self.Bind(wx.EVT_BUTTON, self.onStlQueue, self.bStlQueue)

		self.bStlNext = wx.BitmapButton(self, wx.ID_ANY, self.images.pngNext, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onStlNext, self.bStlNext)
		
		self.bStlToQueue = wx.BitmapButton(self, wx.ID_ANY, self.images.pngAddqueue, size=BUTTONDIM)
		self.bStlToQueue.SetToolTipString("Add the current STL file to the slice queue")
		self.Bind(wx.EVT_BUTTON, self.onStlToQueue, self.bStlToQueue)
		self.bStlToQueue.Enable(False)

		self.bStlClear = wx.BitmapButton(self, wx.ID_ANY, self.images.pngClearlog, size=BUTTONDIM)
		self.bStlClear.SetToolTipString("Clear the current STL file name")
		self.Bind(wx.EVT_BUTTON, self.onStlClear, self.bStlClear)

		self.bGCodeQueue = wx.BitmapButton(self, wx.ID_ANY, self.images.pngGcodequeue, size=BUTTONDIMWIDE)
		self.Bind(wx.EVT_BUTTON, self.onGCodeQueue, self.bGCodeQueue)

		self.bGCodeNext = wx.BitmapButton(self, wx.ID_ANY, self.images.pngNext, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onGCodeNext, self.bGCodeNext)
		
		self.bGcToQueue = wx.BitmapButton(self, wx.ID_ANY, self.images.pngAddqueue, size=BUTTONDIM)
		self.bGcToQueue.SetToolTipString("Add the current G Code file to the print queue")
		self.Bind(wx.EVT_BUTTON, self.onGcToQueue, self.bGcToQueue)
		self.bGcToQueue.Enable(False)

		self.bGcClear = wx.BitmapButton(self, wx.ID_ANY, self.images.pngClearlog, size=BUTTONDIM)
		self.bGcClear.SetToolTipString("Clear the current G Code file name")
		self.Bind(wx.EVT_BUTTON, self.onGcClear, self.bGcClear)

		self.bHistory = wx.BitmapButton(self, wx.ID_ANY, self.images.pngHistory, size=BUTTONDIM)
		self.bHistory.SetToolTipString("Show the history dialog box")
		self.Bind(wx.EVT_BUTTON, self.onHistory, self.bHistory)

		self.designButtons = self.createSectionButtons("design", self.doDesignButton)
		self.meshButtons = self.createSectionButtons("mesh", self.doMeshButton)
		self.sliceButtons = self.createSectionButtons("slicer", self.doSliceButton)
		self.gCodeButtons = self.createSectionButtons("gcode", self.doGCodeButton)
		
		szHFrame = wx.BoxSizer(wx.HORIZONTAL)
		szVFrame = wx.BoxSizer(wx.VERTICAL)
		szVFrame.AddSpacer((20, 20))
		
		szButtonRow = wx.BoxSizer(wx.HORIZONTAL)
		
		box = wx.StaticBox(self, wx.ID_ANY, " Design Tools ")
		bvsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bhsizer = wx.BoxSizer(wx.HORIZONTAL)
		bhsizer.AddSpacer((10, 10))
		for b in self.designButtons:
			bhsizer.Add(b.getButton())
			bhsizer.AddSpacer((10, 10))
		
		bvsizer.AddSpacer((10, 10))
		bvsizer.Add(bhsizer)
		bvsizer.AddSpacer((10, 10))
		szButtonRow.Add(bvsizer)
		szButtonRow.AddSpacer((20, 20))
		
		box = wx.StaticBox(self, wx.ID_ANY, " STL/Mesh Tools ")
		bvsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bhsizer = wx.BoxSizer(wx.HORIZONTAL)
		bhsizer.AddSpacer((10, 10))
		bhsizer.Add(self.bStlView)
		bhsizer.AddSpacer((10, 10))
		bhsizer.Add(self.bPlater)
		bhsizer.AddSpacer((10, 10))
		for b in self.meshButtons:
			bhsizer.Add(b.getButton())
			bhsizer.AddSpacer((10, 10))
			
		bvsizer.AddSpacer((10, 10))
		bvsizer.Add(bhsizer)
		bvsizer.AddSpacer((10, 10))
		szButtonRow.Add(bvsizer)
		
		szVFrame.Add(szButtonRow)
		szVFrame.AddSpacer((20, 20))
		
		szButtonRow = wx.BoxSizer(wx.HORIZONTAL)
		
		box = wx.StaticBox(self, wx.ID_ANY, " Slicing Tools ")
		bvsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bhsizer = wx.BoxSizer(wx.HORIZONTAL)
		bhsizer.AddSpacer((10, 10))
		bhsizer.Add(self.bSlic3r)
		bhsizer.AddSpacer((10, 10))
		bhsizer.Add(self.bCuraEngine)
		bhsizer.AddSpacer((10, 10))
		for b in self.sliceButtons:
			bhsizer.Add(b.getButton())
			bhsizer.AddSpacer((10, 10))
		
		bvsizer.AddSpacer((10, 10))
		bvsizer.Add(bhsizer)
		bvsizer.AddSpacer((10, 10))
		szButtonRow.Add(bvsizer)
		szButtonRow.AddSpacer((20, 20))
		
		box = wx.StaticBox(self, wx.ID_ANY, " G Code Tools ")
		bvsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bhsizer = wx.BoxSizer(wx.HORIZONTAL)
		bhsizer.AddSpacer((10, 10))
		bhsizer.Add(self.bGEdit)
		bhsizer.AddSpacer((10, 10))
		for b in self.gCodeButtons:
			bhsizer.Add(b.getButton())
			bhsizer.AddSpacer((10, 10))

		bvsizer.AddSpacer((10, 10))
		bvsizer.Add(bhsizer)
		bvsizer.AddSpacer((10, 10))
		szButtonRow.Add(bvsizer)
		szButtonRow.AddSpacer((20, 20))
		
		box = wx.StaticBox(self, wx.ID_ANY, " Log ")
		bvsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bhsizer = wx.BoxSizer(wx.HORIZONTAL)
		bhsizer.AddSpacer((10, 10))
		bhsizer.Add(self.bLogHideShow)
		bhsizer.AddSpacer((10, 10))
		bhsizer.Add(self.bLogClear)
		bhsizer.AddSpacer((10, 10))
		bhsizer.Add(self.bLogSave)
		bhsizer.AddSpacer((10, 10))
		bvsizer.AddSpacer((10, 10))
		bvsizer.Add(bhsizer)
		bvsizer.AddSpacer((10, 10))
		szButtonRow.Add(bvsizer)
		
		szVFrame.Add(szButtonRow)
		szVFrame.AddSpacer((20, 20))
		
		szButtonRow = wx.BoxSizer(wx.HORIZONTAL)
		
		box = wx.StaticBox(self, wx.ID_ANY, " Queue Management ")
		bvsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bhsizer = wx.BoxSizer(wx.HORIZONTAL)
		bhsizer.AddSpacer((10, 10))
		bhsizer.Add(self.bStlQueue)
		bhsizer.AddSpacer((10, 10))
		bhsizer.Add(self.bStlNext)
		bhsizer.AddSpacer((20, 20))
		bhsizer.Add(self.bGCodeQueue)
		bhsizer.AddSpacer((10, 10))
		bhsizer.Add(self.bGCodeNext)
		bhsizer.AddSpacer((30, 10))
		bhsizer.Add(self.bHistory)
		bhsizer.AddSpacer((10, 10))
		bvsizer.AddSpacer((10, 10))
		bvsizer.Add(bhsizer)
		bvsizer.AddSpacer((10, 10))
		szButtonRow.Add(bvsizer)
		
		szVFrame.Add(szButtonRow)
		szVFrame.AddSpacer((20, 20))
		
		box = wx.StaticBox(self, wx.ID_ANY, " STL File ")
		bstlvsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bstlsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.tcStlFile = wx.TextCtrl(self, wx.ID_ANY, "", size=(400, -1), style=wx.TE_READONLY)
		bstlsizer.AddSpacer((20, 20))
		bstlsizer.Add(self.tcStlFile, 1, wx.TOP, 12)
		bstlsizer.AddSpacer((10, 10))
		bstlsizer.Add(self.bStlToQueue)
		bstlsizer.AddSpacer((10, 10))
		bstlsizer.Add(self.bStlClear)
		bstlsizer.AddSpacer((20, 20))
		bstlvsizer.AddSpacer((20, 20))
		bstlvsizer.Add(bstlsizer)
		bstlvsizer.AddSpacer((20, 20))
		szVFrame.Add(bstlvsizer)
		szVFrame.AddSpacer((20, 20))
		
		box = wx.StaticBox(self, wx.ID_ANY, " G Code File ")
		bgcvsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bgcsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.tcGcFile = wx.TextCtrl(self, wx.ID_ANY, "", size=(400, -1), style=wx.TE_READONLY)
		bgcsizer.AddSpacer((20, 20))
		bgcsizer.Add(self.tcGcFile, 1, wx.TOP, 12)
		bgcsizer.AddSpacer((10, 10))
		bgcsizer.Add(self.bGcToQueue)
		bgcsizer.AddSpacer((10, 10))
		bgcsizer.Add(self.bGcClear)
		bgcsizer.AddSpacer((20, 20))
		bgcvsizer.AddSpacer((20, 20))
		bgcvsizer.Add(bgcsizer)
		bgcvsizer.AddSpacer((20, 20))
		szVFrame.Add(bgcvsizer)
		szVFrame.AddSpacer((20, 20))

		
		self.reprap = {}
		self.bPrinter = {}
		self.wPrinter = {}
		self.bId = {}
		self.wPendant = {}
		
		for p in self.settings.printers:
			pinfo = self.settings.getSection(p)
			if not ("port" in pinfo.keys() and "baud" in pinfo.keys() and "firmware" in pinfo.keys()):
				print "Invalid configuration for printer %s" % p
				continue
			
			b = GB.GradientButton(self, wx.ID_ANY, self.images.pngPrinter, p,
				size=PBUTTONDIM, style=wx.BORDER)
			b.SetTopStartColour(white)
			b.SetTopEndColour(white)
			b.SetBottomStartColour(white)
			b.SetBottomEndColour(white)
			b.SetForegroundColour(grey)

			self.bId[p] = b.GetId()
			b.SetToolTipString("control panel for %s printer" % p)
			self.Bind(wx.EVT_BUTTON, self.doPrinter, b)
			b.Enable(False)
			self.bPrinter[p] = b
			self.wPrinter[p] = None
			self.reprap[p] = RepRap(self, p, pinfo["port"], pinfo["baud"], pinfo["firmware"])
			self.wPendant[p] = wx.StaticBitmap(self, wx.ID_ANY, self.images.pngPendantclear)

		
		box = wx.StaticBox(self, wx.ID_ANY, " Printers ")
		bvsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bhsizer = wx.BoxSizer(wx.HORIZONTAL)
		bhsizer.AddSpacer((10, 10))
		
		for p in sorted(self.settings.printers):
			bhsizer.Add(self.bPrinter[p])
			bhsizer.AddSpacer((10, 10))
			
		bmphsizer = wx.BoxSizer(wx.HORIZONTAL)
		bmphsizer.AddSpacer((66, 10))
		
		for p in sorted(self.settings.printers):
			bmphsizer.Add(self.wPendant[p])
			bmphsizer.AddSpacer((122, 10))
		
		bvsizer.AddSpacer((10, 10))
		bvsizer.Add(bhsizer)
		bvsizer.Add(bmphsizer)
		bvsizer.AddSpacer((10, 10))
		szVFrame.Add(bvsizer)
		szVFrame.AddSpacer((20, 20))
		
		szHFrame.AddSpacer((20, 20))
		szHFrame.Add(szVFrame)
		szHFrame.AddSpacer((20, 20))

		self.SetSizer(szHFrame)
		self.Layout()
		self.Fit()
		if self.settings.tbposition is not None:
			self.SetPosition(self.settings.tbposition)
			
		if self.settings.logposition is not None:
			self.logger.SetPosition(self.settings.logposition)
			
		if self.settings.port != 0:
			self.httpServer = RepRapServer(self, port=self.settings.port)
			
		self.pendant = Pendant(self.pendantConnection, self.pendantCommand, self.settings.pendantport, self.settings.pendantbaud)
		self.setSliceQLen()
		self.setGCodeQLen()
		
	def createSectionButtons(self, section, handler):
		buttons = []
		sectionInfo = self.settings.getSection(section)
		if sectionInfo is not None:
			if "order" in sectionInfo.keys():
				order = sectionInfo["order"].split(",")
			else:
				order = sectionInfo.keys()

			for n in order:
				if n not in sectionInfo.keys():
					print "key in order listing has no data line: %s" % n
					return []
				
				v = sectionInfo[n].split(",")
				if len(v) >= 3:
					cmd = v[0]
					helptext = v[1]
					if v[2].lower() == "true":
						shell = True
					else:
						shell = False
				elif len(v) == 2:
					cmd = v[0]
					helptext = v[1]
					shell = False
				elif len(v) == 1:
					cmd = v[0]
					helptext = ""
					shell = False
				else:
					print "invalid entry for (%s)" % n
					cmd = None
					
				if cmd is not None:
					b = wx.BitmapButton(self, wx.ID_ANY, self.images.getByName(n), size=BUTTONDIM)
					b.SetToolTipString(helptext)
					bid = b.GetId()
					self.Bind(wx.EVT_BUTTON, handler, b)
					buttons.append(ToolButton(b, bid, cmd, shell))
			
		return buttons
		
	def reportConnection(self, flag, pName):
		if not flag:
			if self.wPrinter[pName] is not None:
				self.wPrinter[pName].terminate()
				self.wPrinter[pName] = None
		self.enablePrinterButton(pName, flag)

	def enablePrinterButton(self, pName, flag):
		self.bPrinter[pName].Enable(flag)
		if flag:
			self.bPrinter[pName].SetForegroundColour(black)
		else:
			self.bPrinter[pName].SetForegroundColour(grey)
		
	def registerPrinterStatusReporter(self, printerName, cb):
		self.statusReportCB[printerName] = cb
		
	def getStatusReport(self):
		report = {}
		for p in self.statusReportCB.keys():
			if self.statusReportCB[p] is not None:
				report[p] = self.statusReportCB[p].getStatusReport()
		return {"status": report}
		
	def onClose(self, evt):
		self.sliceQueue.save()
		self.gcodeQueue.save()
		self.history.save()

		if self.dlgStlQueue is not None:
			if not self.dlgStlQueue.terminate():
				return
			self.dlgStlQueue.Destroy()
			self.dlgStlQueue = None
			
		if self.dlgGcQueue is not None:
			if not self.dlgGcQueue.terminate():
				return
			self.dlgGcQueue.Destroy()
			self.dlgGcQueue = None
			
		if self.dlgHistory is not None:
			self.dlgHistory.Destroy()
			self.dlgHistory = None
			
		for p in self.wPrinter.keys():
			if self.wPrinter[p] is not None:
				if self.wPrinter[p].isPrinting():
					dlg = wx.MessageDialog(self, 'Cannot exit with printing active',
							   "Printer %s is active" % p,
							   wx.OK | wx.ICON_INFORMATION)
					dlg.ShowModal()
					dlg.Destroy()
					return
				else:
					self.wPrinter[p].terminate()
					self.wPrinter[p] = None
					
		self.settings.tbposition = self.GetPosition()
		self.settings.logposition = self.logger.GetPosition()
						
		for p in self.reprap.keys():
			self.reprap[p].terminate()
			
		try:
			self.dlgSlic3r.terminate()
		except:
			pass
			
		try:
			self.dlgCuraEngine.terminate()
		except:
			pass
			
		if self.dlgViewStl is not None:
			self.settings.viewerposition = self.dlgViewStl.GetPosition()
			self.dlgViewStl.Destroy()
			
		if self.dlgPlater is not None:
			self.settings.platerposition = self.dlgPlater.GetPosition()
			self.dlgPlater.Destroy()
			
		if self.dlgGEdit is not None:
			self.settings.gcodeposition = self.dlgGEdit.GetPosition()
			self.dlgGEdit.Destroy()
		
		if self.settings.port != 0:
			self.httpServer.close()

		self.settings.save()

		self.logger.Destroy()
		self.pendant.kill()		
		self.Destroy()

	def doViewStl(self, evt):
		if self.dlgViewStl is None:
			dlg = StlViewDlg(self)
			dlg.Show()
			dlg.setImportFile(self.exportedStlFile)
			if self.settings.viewerposition is not None:
				dlg.SetPosition(self.settings.viewerposition)
			self.dlgViewStl = dlg
		else:
			self.dlgViewStl.Show()
			self.dlgViewStl.Raise()
	
	def viewStlClosed(self):
		self.settings.viewerposition = self.dlgViewStl.GetPosition()
		self.dlgViewStl.Destroy()
		self.dlgViewStl = None
	
	def doPlater(self, evt):
		if self.dlgPlater is None:
			dlg = PlaterDlg(self)
			dlg.Show()
			if self.settings.platerposition is not None:
				dlg.SetPosition(self.settings.platerposition)
			self.dlgPlater = dlg
		else:
			self.dlgPlater.Show()
			self.dlgPlater.Raise()
	
	def platerClosed(self):
		self.settings.platerposition = self.dlgPlater.GetPosition()
		self.dlgPlater.Destroy()
		self.dlgPlater = None
		
	def doGEdit(self, evt):
		if self.dlgGEdit is None:
			dlg = GEditDlg(self)
			dlg.Show()
			dlg.setImportFile(self.exportedGcFile)
			if self.settings.gcodeposition is not None:
				dlg.SetPosition(self.settings.gcodeposition)
			self.dlgGEdit = dlg
		else:
			self.dlgGEdit.Show()
			self.dlgGEdit.Raise()
	
	def GEditClosed(self):
		self.settings.gcodeposition = self.dlgGEdit.GetPosition()
		self.dlgGEdit.Destroy()
		self.dlgGEdit = None
		
	def doSlic3r(self, evt):
		if self.dlgSlic3r is None:
			dlg = Slic3rDlg(self)
			dlg.Show()
			self.dlgSlic3r = dlg
			self.setSliceQLen()
			self.dlgSlic3r.setImportFile(self.exportedStlFile)
		else:
			self.dlgSlic3r.Show()
			self.dlgSlic3r.Raise()
	
	def Slic3rClosed(self):
		self.dlgSlic3r = None
		
	def doCuraEngine(self, evt):
		if self.dlgCuraEngine is None:
			dlg = CuraEngineDlg(self)
			dlg.Show()
			self.dlgCuraEngine = dlg
			self.setSliceQLen()
			self.dlgCuraEngine.setImportFile(self.exportedStlFile)
		else:
			self.dlgCuraEngine.Show()
			self.dlgCuraEngine.Raise()
	
	def CuraEngineClosed(self):
		self.dlgCuraEngine = None
		
	def doPrinter(self, evt):
		bid = evt.GetId()
		pName = None
		for p in self.bId.keys():
			if self.bId[p] == bid:
				pName = p
				break
			
		if pName is None:
			print "can't determine which button was pressed"
			return

		if self.wPrinter[pName] is None:			
			self.wPrinter[pName] = PrinterDlg(self, pName, self.reprap[pName])
			self.assignPendantIf(pName)
			self.setGCodeQLen()
			self.wPrinter[pName].setImportFile(self.exportedGcFile)
		else:
			self.wPrinter[pName].Show()
			self.wPrinter[pName].Raise()
	
	def PrinterClosed(self, pName):
		self.wPrinter[pName] = None
		self.wPendant[pName].SetBitmap(self.images.pngPendantclear)
		self.assignPendant(None)

	# the next 2 methods are called from the pendant thread - we can't do anything there that 
	# works with wxpython, so we need to send an event to ourselves and do the processing
	# in the main thread				
	def pendantCommand(self, cmd):
		if cmd is not None: # or self.pendantAssignment is None:
			evt = PendantCmdEvent(cmd=cmd)
			wx.PostEvent(self, evt)

	def pendantConnection(self, flag):
		evt = PendantConnEvent(flag=flag)
		try:
			wx.PostEvent(self, evt)
		except:
			pass
		
	def pendantCommandHandler(self, evt):
		cl = pendantCommand(evt.cmd, self.wPrinter[self.pendantAssignment], self.log)
		for cmd in cl:
			self.wPrinter[self.pendantAssignment].doPendantCommand(cmd)
		
	def pendantConnectionHandler(self, evt):
		self.pendantConnected = evt.flag
		if evt.flag:
			self.log("Pendant connected")
		else:
			self.log("Pendant disconnected")
			
		for p in self.wPrinter.keys():
			if self.wPrinter[p] is not None:
				self.wPrinter[p].removePendant(self.pendantConnected)
			
		self.assignPendant(None)
		
	def assignPendantIf(self, pName):
		if self.pendantAssignment is None:
			self.assignPendant(pName)
		elif self.wPrinter[pName] is not None:
			self.wPrinter[pName].removePendant(self.pendantConnected)
		
	def assignPendant(self, pName):
		if not self.pendantConnected:
			self.pendantAssignment = None
			for p in self.wPrinter.keys():
				self.wPendant[p].SetBitmap(self.images.pngPendantclear)
				if self.wPrinter[p] is not None:
					self.wPrinter[p].removePendant(self.pendantConnected)
			return
		
		if self.pendantAssignment is not None and self.wPrinter[self.pendantAssignment] is not None:
			self.wPrinter[self.pendantAssignment].removePendant(self.pendantConnected)
			self.wPendant[self.pendantAssignment].SetBitmap(self.images.pngPendantclear)
		self.pendantAssignment = pName
		if self.pendantAssignment is None:
			for p in self.wPrinter.keys():
				if self.wPrinter[p] is not None:
					self.pendantAssignment = p
					
		if self.pendantAssignment is None:
			self.log("pendant is unassigned")

		else:
			self.log("pendant is assigned to: %s" % self.pendantAssignment)
			self.wPrinter[self.pendantAssignment].addPendant()
			self.wPendant[self.pendantAssignment].SetBitmap(self.images.pngPendanton)

		
	def doDesignButton(self, evt):
		self.doToolButton(evt, self.designButtons)
		
	def doMeshButton(self, evt):
		self.doToolButton(evt, self.meshButtons)
		
	def doSliceButton(self, evt):
		self.doToolButton(evt, self.sliceButtons)
		
	def doGCodeButton(self, evt):
		self.doToolButton(evt, self.gCodeButtons)
		
	def doToolButton(self, evt, buttons):
		bid = evt.GetId()
		for b in buttons:
			if bid == b.getBid():
				args = shlex.split(str(b.getCommand()))
				shell = b.needsShell()
				try:
					subprocess.Popen(args, shell=shell, stdin=None, stdout=None, stderr=None, close_fds=True)
				except:
					print "Exception occurred trying to spawn tool process"
				return
			
	def onStlClear(self, evt):
		self.exportStlFile(None)
		
	def exportStlFile(self, fn, exportFile=True, addToQueue=False):
		self.exportedStlFile = fn
		if fn is None:
			self.bStlToQueue.Enable(False)
			self.tcStlFile.SetValue("")
		else:
			if exportFile:
				self.bStlToQueue.Enable(True)
				self.tcStlFile.SetValue(fn)
			if addToQueue:
				self.sliceQueue.enQueuePath(fn)
				self.setSliceQLen()
			
		for s in [self.dlgCuraEngine, self.dlgSlic3r, self.dlgViewStl]:
			if s is not None:
				s.setImportFile(fn)
				
	def exportStlToQueue(self):
		if not self.exportedStlFile is None:
			self.sliceQueue.enQueuePath(self.exportedStlFile)
			self.setSliceQLen()

	def onGcClear(self, evt):
		self.exportGcFile(None)
		
	def exportGcFile(self, fn, exportFile=True, addToQueue=False):
		self.exportedGcFile = fn
		if fn is None:
			self.bGcToQueue.Enable(False)
			self.tcGcFile.SetValue("")
		else:
			if exportFile:
				self.bGcToQueue.Enable(True)
				self.tcGcFile.SetValue(fn)
			if addToQueue:
				self.gcodeQueue.enQueuePath(fn)
				self.setGCodeQLen()
			
		for pn in self.wPrinter.keys():
			p = self.wPrinter[pn]
			if p is not None:
				p.setImportFile(fn)
						
		if self.dlgGEdit is not None:
			self.dlgGEdit.setImportFile(fn)
				
	def exportGcToQueue(self):
		if not self.exportedGcFile is None:
			self.gcodeQueue.enQueuePath(self.exportedGcFile)
			self.setGCodeQLen()
		
	def importStlFile(self):
		return self.exportedStlFile
	
	def importStlFromQueue(self):
		fo = self.sliceQueue.deQueue()
		if fo is None:
			return None
		fn = fo.getFn()
		self.exportStlFile(fn)
		self.setSliceQLen()
		return fn
	
	def importGcFile(self):
		return self.exportedGcFile
	
	def importGcFromQueue(self):
		fo = self.gcodeQueue.deQueue()
		if fo is None:
			return None
		fn = fo.getFn()
		self.exportGcFile(fn)
		self.setGCodeQLen()
		return fn
	
	def onLogHideShow(self, evt):
		self.logger.toggleVisibility()
		
	def onLogClear(self, evt):
		self.logger.doClear()
		
	def onLogSave(self, evt):
		self.logger.doSave()
		
	def onStlQueue(self, evt):
		if self.dlgStlQueue is None:
			dlg = SliceQueueDlg(self, self.sliceQueue)
			dlg.Show()
			self.dlgStlQueue = dlg
		else:
			self.dlgStlQueue.Show()
			self.dlgStlQueue.Raise()

	def closeStlQueue(self, rc):
		if rc == wx.ID_OK:
			self.setSliceQLen()
		self.dlgStlQueue.Destroy();
		self.dlgStlQueue = None

	def displayStlFile(self, fn):
		if self.dlgViewStl is None:
			dlg = StlViewDlg(self)
			dlg.Show()
			if self.settings.viewerposition is not None:
				dlg.SetPosition(self.settings.viewerposition)
			self.dlgViewStl = dlg
		else:
			self.dlgViewStl.Show()
			self.dlgViewStl.Raise()
		self.dlgViewStl.loadStlFile(fn)
		
	def setSliceQLen(self):
		n = len(self.sliceQueue)
		text = "Manage the Slicing queue - %d files in queue" % n
		self.bStlQueue.SetToolTipString(text)
		
		if n > 0:
			nfn = os.path.basename(self.sliceQueue.peek().getFn())
			self.bStlNext.SetToolTipString("Remove the first file (%s) from the queue and make it current" % nfn)
			slMsg = "Import first file (%s) from Slice queue" % nfn
		else:
			self.bStlNext.SetToolTipString("")
			slMsg = None
			
		for s in [self.dlgCuraEngine, self.dlgSlic3r]:
			if s is not None:
				s.setImportButton(slMsg)
				
		self.bStlNext.Enable(n != 0)
		
	def onStlNext(self, evt):
		fn = self.sliceQueue.deQueue().getFn()
		self.exportStlFile(fn)
		self.setSliceQLen()
		
	def onStlToQueue(self, evt):
		self.exportStlToQueue()
		
	def onGCodeQueue(self, evt):
		if self.dlgGcQueue is None:
			dlg = GCodeQueueDlg(self, self.gcodeQueue)
			dlg.Show()
			self.dlgGcQueue = dlg
		else:
			self.dlgGcQueue.Show()
			self.dlgGcQueue.Raise()

	def closeGCodeQueue(self, rc):
		if rc == wx.ID_OK:
			self.setGCodeQLen()
		self.dlgGcQueue.Destroy();
		self.dlgGcQueue = None
		
	def displayGCodeFile(self, fn):
		if self.dlgGEdit is None:
			dlg = GEditDlg(self)
			dlg.Show()
			if self.settings.gcodeposition is not None:
				dlg.SetPosition(self.settings.gcodeposition)
			self.dlgGEdit = dlg
		else:
			self.dlgGEdit.Show()
			self.dlgGEdit.Raise()
		self.dlgGEdit.loadGFile(fn)
		
	def setGCodeQLen(self):
		n = len(self.gcodeQueue)
		text = "Manage the G Code queue - %d files in queue" % n
		self.bGCodeQueue.SetToolTipString(text)
		
		if n > 0:
			nfn = os.path.basename(self.gcodeQueue.peek().getFn())
			self.bGCodeNext.SetToolTipString("Remove the first file (%s) from the queue and make it current" % nfn)
			pmMsg = "Import first file (%s) from G Code queue" % nfn
		else:
			self.bGCodeNext.SetToolTipString("")
			pmMsg = None
			
		for pn in self.wPrinter.keys():
			p = self.wPrinter[pn]
			if p is not None:
				p.setImportButton(pmMsg)
				
		if self.dlgGEdit is not None:
			self.dlgGEdit.setImportButton(pmMsg)
				
		self.bGCodeNext.Enable(n != 0)
		
	def onGCodeNext(self, evt):
		fn = self.gcodeQueue.deQueue().getFn()
		self.exportGcFile(fn)
		self.setGCodeQLen()
		
	def onGcToQueue(self, evt):
		self.exportGcToQueue()
		
	def onHistory(self, evt):
		if self.dlgHistory is None:
			dlg = HistoryDlg(self, self.history)
			dlg.Show()
			self.dlgHistory = dlg
		else:
			self.dlgHistory.Show()
			self.dlgHistory.Raise()

	def closeHistory(self):
		self.dlgHistory.Destroy()
		self.dlgHistory = None
	
	def log(self, msg):
		self.logger.LogMessage(msg)
			
class App(wx.App):
	def OnInit(self):
		self.frame = MyFrame()
		#self.frame.Show()
		self.SetTopWindow(self.frame)
		return True

app = App(False)
app.MainLoop()
