import wx
import os
import sys, inspect

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
from Printer.printer import PrinterDlg
from reprap import RepRap
from log import Logger
from HTTPServer import RepRapServer
	


BUTTONDIM = (48, 48)
PBUTTONDIM = (96, 96)


class MyFrame(wx.Frame):
	def __init__(self):
		self.t = 0
		self.seq = 0
		self.exportedStlFile = None
		self.exportedGcFile = None
		self.modified = False
		wx.Frame.__init__(self, None, wx.ID_ANY, "RepRap Toolbox", size=(300, 300))
		self.Show()
		
		self.dlgSlic3r = None
		self.dlgViewStl = None
		self.dlgPlater = None
		self.dlgGEdit = None
		
		self.settings = Settings(cmdFolder)
		self.images = Images(os.path.join(cmdFolder, "images"))
		
		self.Bind(wx.EVT_CLOSE, self.onClose)
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

		(self.tDesignButtons,
			self.tDesignIds,
			self.tDesignCommands,
			self.tDesignOrder) = self.createSectionButtons("design", self.doDesignButton)
		(self.tMeshButtons,
			self.tMeshIds,
			self.tMeshCommands,
			self.tMeshOrder) = self.createSectionButtons("mesh", self.doMeshButton)
		(self.tSliceButtons,
			self.tSliceIds,
			self.tSliceCommands,
			self.tSliceOrder) = self.createSectionButtons("slicer", self.doSliceButton)
		(self.tGCodeButtons,
			self.tGCodeIds,
			self.tGCodeCommands,
			self.tGCodeOrder) = self.createSectionButtons("gcode", self.doGCodeButton)
		
		szHFrame = wx.BoxSizer(wx.HORIZONTAL)
		szVFrame = wx.BoxSizer(wx.VERTICAL)
		szVFrame.AddSpacer((20, 20))
		
		szButtonRow = wx.BoxSizer(wx.HORIZONTAL)
		
		box = wx.StaticBox(self, wx.ID_ANY, " Design Tools ")
		bvsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bhsizer = wx.BoxSizer(wx.HORIZONTAL)
		bhsizer.AddSpacer((10, 10))
		for n in self.tDesignOrder:
			bhsizer.Add(self.tDesignButtons[n])
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
		for n in self.tMeshOrder:
			bhsizer.Add(self.tMeshButtons[n])
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
		for n in self.tSliceOrder:
			bhsizer.Add(self.tSliceButtons[n])
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
		for n in self.tGCodeOrder:
			bhsizer.Add(self.tGCodeButtons[n])
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
		bvsizer.AddSpacer((10, 10))
		bvsizer.Add(bhsizer)
		bvsizer.AddSpacer((10, 10))
		szButtonRow.Add(bvsizer)
		
		szVFrame.Add(szButtonRow)
		szVFrame.AddSpacer((30, 30))
		
		box = wx.StaticBox(self, wx.ID_ANY, " STL File ")
		bstlvsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bstlsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.tcStlFile = wx.TextCtrl(self, wx.ID_ANY, "", size=(400, -1))
		bstlsizer.AddSpacer((20, 20))
		bstlsizer.Add(self.tcStlFile)
		bstlsizer.AddSpacer((20, 20))
		bstlvsizer.AddSpacer((20, 20))
		bstlvsizer.Add(bstlsizer)
		bstlvsizer.AddSpacer((20, 20))
		szVFrame.Add(bstlvsizer)
		szVFrame.AddSpacer((20, 20))
		
		box = wx.StaticBox(self, wx.ID_ANY, " G Code File ")
		bgcvsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bgcsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.tcGcFile = wx.TextCtrl(self, wx.ID_ANY, "", size=(400, -1))
		bgcsizer.AddSpacer((20, 20))
		bgcsizer.Add(self.tcGcFile)
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
		
		for p in self.settings.printers:
			pinfo = self.settings.getSection(p)
			if not ("port" in pinfo.keys() and "baud" in pinfo.keys() and "firmware" in pinfo.keys()):
				print "Invalid configuration for printer %s" % p
				continue
			
			b = wx.Button(self, wx.ID_ANY, p, size=PBUTTONDIM)
			self.bId[p] = b.GetId()
			b.SetToolTipString("control panel for %s printer" % p)
			self.Bind(wx.EVT_BUTTON, self.doPrinter, b)
			b.Enable(False)
			self.bPrinter[p] = b
			self.wPrinter[p] = None
			self.reprap[p] = RepRap(self, p, pinfo["port"], pinfo["baud"], pinfo["firmware"])
		
		box = wx.StaticBox(self, wx.ID_ANY, " Printers ")
		bvsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bhsizer = wx.BoxSizer(wx.HORIZONTAL)
		bhsizer.AddSpacer((10, 10))
		
		for p in sorted(self.settings.printers):
			bhsizer.Add(self.bPrinter[p])
			bhsizer.AddSpacer((10, 10))
		
		bvsizer.AddSpacer((10, 10))
		bvsizer.Add(bhsizer)
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

		
	def createSectionButtons(self, section, handler):
		buttons = {}
		bids = {}
		sectionInfo = self.settings.getSection(section)
		cmds = {}
		order = []
		if sectionInfo is not None:
			for n in sectionInfo.keys():
				if n == "order":
					order = sectionInfo[n].split(",")
				else:
					v = sectionInfo[n].split(",")
					if len(v) >= 2:
						cmd = v[0]
						helptext = v[1]
					elif len(v) == 1:
						cmd = v[0]
						helptext = ""
					else:
						print "invalid entry for (%s)" % n
						cmd == None
					if cmd is not None:
						cmds[n] = cmd
						b = wx.BitmapButton(self, wx.ID_ANY, self.images.getByName(n), size=BUTTONDIM)
						b.SetToolTipString(helptext)
						buttons[n] = b
						bids[n] = b.GetId()
						self.Bind(wx.EVT_BUTTON, handler, b)
					
		if len(order) != len(buttons.keys()):
			print "number of items in %s order list (%d) != number of tools (%d).  Using alpha order" % (section, len(order), len(buttons.keys()))
			order = sorted(buttons.keys())
			
		return buttons, bids, cmds, order

		
	def reportConnection(self, flag, pName):
		if not flag:
			if self.wPrinter[pName] is not None:
				self.wPrinter[pName].terminate()
				self.wPrinter[pName] = None
		self.bPrinter[pName].Enable(flag)
		
	def registerPrinterStatusReporter(self, printerName, cb):
		self.statusReportCB[printerName] = cb
		
	def getStatusReport(self):
		report = {}
		for p in self.statusReportCB.keys():
			if self.statusReportCB[p] is not None:
				report[p] = self.statusReportCB[p].getStatusReport()
		print "========================="
		print report
		print "========================="
		return report
		
	def onClose(self, evt):
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
					
		self.settings.tbposition = self.GetPosition()
		self.settings.logposition = self.logger.GetPosition()
		self.settings.save()
						
		for p in self.reprap.keys():
			self.reprap[p].terminate()
			
		try:
			self.dlgSlic3r.Destroy()
		except:
			pass
			
		try:
			self.dlgViewStl.Destroy()
		except:
			pass
			
		try:
			self.dlgPlater.Destroy()
		except:
			pass
			
		try:
			self.dlgGEdit.Destroy()
		except:
			pass
		
		if self.settings.port != 0:
			self.httpServer.close()

		self.logger.Destroy()		
		self.Destroy()

	def doViewStl(self, evt):
		dlg = StlViewDlg(self)
		dlg.Show()
		self.bStlView.Enable(False);
		self.dlgViewStl = dlg
	
	def viewStlClosed(self):
		self.bStlView.Enable(True);
		self.dlgViewStl = None
	
	def doPlater(self, evt):
		dlg = PlaterDlg(self)
		self.bPlater.Enable(False);
		dlg.Show()
		self.dlgPlater = dlg
	
	def platerClosed(self):
		self.bPlater.Enable(True);
		self.dlgPlater = None
		
	def doGEdit(self, evt):
		dlg = GEditDlg(self)
		self.bGEdit.Enable(False)
		dlg.Show()
		self.dlgGEdit = dlg
	
	def GEditClosed(self):
		self.bGEdit.Enable(True)
		self.dlgGEdir = None
		
	def doSlic3r(self, evt):
		dlg = Slic3rDlg(self)
		self.bSlic3r.Enable(False)
		dlg.Show()
		self.dlgSlic3r = dlg
	
	def Slic3rClosed(self):
		self.bSlic3r.Enable(True)
		self.dlgSlic3r = None
		
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
		
		self.wPrinter[pName] = PrinterDlg(self, pName, self.reprap[pName])
		self.bPrinter[pName].Enable(False)
	
	def PrinterClosed(self, pName):
		self.bPrinter[pName].Enable()
		self.wPrinter[pName] = None
		
	def doDesignButton(self, evt):
		bid = evt.GetId()
		for n in self.tDesignIds.keys():
			if bid == self.tDesignIds[n]:
				print "Pressed button for (%s) invoking command (%s)" % (n, self.tDesignCommands[n])
				args = shlex.split(str(self.tDesignCommands[n]))
				try:
					subprocess.Popen(args, shell=False, stdin=None, stdout=None, stderr=None, close_fds=True)
				except:
					print "Exception occurred trying to spawn tool process"
				return
		
	def doMeshButton(self, evt):
		bid = evt.GetId()
		for n in self.tMeshIds.keys():
			if bid == self.tMeshIds[n]:
				print "Pressed button for (%s) invoking command (%s)" % (n, self.tMeshCommands[n])
				return
		
	def doSliceButton(self, evt):
		bid = evt.GetId()
		for n in self.tSliceIds.keys():
			if bid == self.tSliceIds[n]:
				print "Pressed button for (%s) invoking command (%s)" % (n, self.tSliceCommands[n])
				return
		
	def doGCodeButton(self, evt):
		bid = evt.GetId()
		for n in self.tGCodeIds.keys():
			if bid == self.tGCodeIds[n]:
				print "Pressed button for (%s) invoking command (%s)" % (n, self.tGCodeCommands[n])
				return
		
	def exportStlFile(self, fn):
		self.exportedStlFile = fn
		if fn is None:
			self.tcStlFile.SetValue("")
		else:
			self.tcStlFile.SetValue(fn)
		
	def exportGcFile(self, fn):
		self.exportedGcFile = fn
		if fn is None:
			self.tcGcFile.SetValue("")
		else:
			self.tcGcFile.SetValue(fn)
		
	def importStlFile(self):
		return self.exportedStlFile
	
	def importGcFile(self):
		return self.exportedGcFile
	
	def onLogHideShow(self, evt):
		self.logger.toggleVisibility()
		
	def onLogClear(self, evt):
		self.logger.doClear()
		
	def onLogSave(self, evt):
		self.logger.doSave()
	
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

