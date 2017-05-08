'''
Created on Oct 28, 2016

@author: Jeff
'''
import os, inspect

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))

import wx

from psettings import PrtSettings 
from images import Images
from manualctl import ManualCtl
from heaters import Heaters
from tempgraph import TempDlg
from printmon import PrintMonitorDlg
from macros import MacroDialog
from gcodeentry import GCodeEntry

BUTTONDIM = (48, 48)
MARGIN = 70

class EngageZDlg(wx.Dialog):
	def __init__(self, parent, reprap, images):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Z Axis Is Engaged", size=(MARGIN*2+BUTTONDIM[0], MARGIN*2+BUTTONDIM[1]))
		self.SetBackgroundColour("white")
		
		self.reprap = reprap
		
		self.zdir = True
		self.moveZAxis()
		
		self.moveTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onTimer, self.moveTimer)
		self.moveTimer.Start(10000)
		
		vsz = wx.BoxSizer(wx.VERTICAL)
		hsz = wx.BoxSizer(wx.HORIZONTAL)
		
		b = wx.BitmapButton(self, wx.ID_ANY, images.pngDisengagez, size=BUTTONDIM)
		b.SetToolTipString("Disengage Z axis and Exit")
		b.Bind(wx.EVT_BUTTON, self.onExit, b)
		
		hsz.AddSpacer((MARGIN, 20))
		hsz.Add(b)
		hsz.AddSpacer((MARGIN, 20))
		
		vsz.AddSpacer((20, MARGIN))
		vsz.Add(hsz)
		vsz.AddSpacer((20, MARGIN))
		
		self.SetSizer(vsz)
		self.Fit()
		
	def onTimer(self, evt):
		self.moveZAxis()
		
	def moveZAxis(self):
		self.reprap.sendNow("G91")
		if self.zdir:
			self.reprap.sendNow("G1 Z0.1 F300")
		else:
			self.reprap.sendNow("G1 Z-0.1 F300")
		self.reprap.sendNow("G90")
		self.zdir = not self.zdir
		
	def onExit(self, evt):
		self.moveTimer.Stop()
		if not self.zdir:
			self.moveZAxis() # leave it the way we found it
			
		self.EndModal(wx.ID_OK)
		
class PrinterDlg(wx.Frame):
	def __init__(self, parent, printerName, reprap):
		wx.Frame.__init__(self, None, wx.ID_ANY, "%s manual control" % printerName, size=(100, 100))
		self.Bind(wx.EVT_CLOSE, self.onClose)
		ico = wx.Icon(os.path.join(cmdFolder, "images", "printer.png"), wx.BITMAP_TYPE_PNG)
		self.SetIcon(ico)

		self.parent = parent
		self.history = parent.history
		self.log = parent.log
		self.printerName = printerName
		self.reprap = reprap
		self.settings = PrtSettings(cmdFolder, printerName)
		if self.settings.firmwaretype == "MARLIN":
			import firmwaremarlin as firmware
			self.firmware = firmware
			
		self.images = Images(os.path.join(cmdFolder, "images"))
		self.parentImages = self.parent.images
		
		self.pmonDlg = None
		self.macroDlg = None
		self.fwDlg = None
		
		self.graphDlg = TempDlg(self, self.parent, self.settings.nextruders, self.printerName)
		self.graphDlg.Hide()
		if not self.settings.tempposition is None:
			self.graphDlg.SetPosition(self.settings.tempposition)
		
		self.bedTemps = {"actual": "??", "target": "??"}
		self.heTemps = {}
		for i in range(self.settings.nextruders):
			self.heTemps["HE%d" % i] = {"actual": "??", "target": "??"}
		
		self.importMessage = "Import G Code file from G Code Queue"
		self.importFile = None
			
		self.moveAxis = ManualCtl(self, reprap, printerName)				
		szWindow = wx.BoxSizer(wx.VERTICAL)
		szWindow.Add(self.moveAxis)
		
		szHeaters = wx.BoxSizer(wx.VERTICAL)
		self.heaters = Heaters(self, self.reprap, printerName)
		szHeaters.Add(self.heaters)
		szWindow.AddSpacer((10, 10))
		
		szWindow.Add(szHeaters, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		szWindow.AddSpacer((20, 20))
		
		szWindow.Add(GCodeEntry(self), 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		szWindow.AddSpacer((20, 20))

		btnhsizer = wx.BoxSizer(wx.HORIZONTAL)
		btnhsizer.AddSpacer((10, 10))
		
		self.bGraph = wx.BitmapButton(self, wx.ID_ANY, self.images.pngGraph, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onGraph, self.bGraph)
		self.bGraph.SetToolTipString("Temperature graph dialog box")
		btnhsizer.Add(self.bGraph)
		btnhsizer.AddSpacer((10, 10))
		
		self.bPrintMon = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPrintmon, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onPrintMon, self.bPrintMon)
		self.bPrintMon.SetToolTipString("Print monitoring dialog box")
		btnhsizer.Add(self.bPrintMon)
		btnhsizer.AddSpacer((10, 10))
		
		self.bEngageZ = wx.BitmapButton(self, wx.ID_ANY, self.images.pngEngagez, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onEngageZ, self.bEngageZ)
		self.bEngageZ.SetToolTipString("Lock the Z axis")
		btnhsizer.Add(self.bEngageZ)
		btnhsizer.AddSpacer((10, 10))
		
		self.bFirmware = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFirmware, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onFirmware, self.bFirmware)
		self.bFirmware.SetToolTipString("Firmware settings")
		btnhsizer.Add(self.bFirmware)
		btnhsizer.AddSpacer((10, 10))
		
		self.bMacros = wx.BitmapButton(self, wx.ID_ANY, self.images.pngRunmacro, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onRunMacro, self.bMacros)
		self.bMacros.SetToolTipString("Run macros")
		btnhsizer.Add(self.bMacros)
		btnhsizer.AddSpacer((10, 10))
		
		self.bPendant = wx.BitmapButton(self, wx.ID_ANY, self.parentImages.pngPendantclear, size=BUTTONDIM, style = wx.NO_BORDER)
		self.bPendant.SetToolTipString("")
		self.bPendant.Enable(False)
		self.Bind(wx.EVT_BUTTON, self.onBPendant, self.bPendant)
		btnhsizer.Add(self.bPendant)
		btnhsizer.AddSpacer((50, 10))
		self.pendantAssigned = False

		self.bReset = wx.BitmapButton(self, wx.ID_ANY, self.images.pngReset, size=BUTTONDIM)
		self.bReset.SetToolTipString("Hard reset the printer port")
		self.Bind(wx.EVT_BUTTON, self.onBReset, self.bReset)
		btnhsizer.Add(self.bReset)
		btnhsizer.AddSpacer((90, 10))

		self.bRemember = wx.BitmapButton(self, wx.ID_ANY, self.images.pngRemember, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onRemember, self.bRemember)
		self.bRemember.SetToolTipString("Remember %s window positions" % self.printerName)
		btnhsizer.Add(self.bRemember)
		btnhsizer.AddSpacer((10, 10))

		szWindow.Add(btnhsizer)
		szWindow.AddSpacer((10, 10))
		
		self.SetSizer(szWindow)
		
		self.Show()
		self.Fit()
		if self.settings.ctrlposition is not None:
			self.SetPosition(self.settings.ctrlposition)
		
		self.reprap.registerTempHandler(self.tempHandler)
		self.parent.registerPrinterStatusReporter(self.printerName, self)

	def getStatusReport(self):
		if self.pmonDlg is None:
			r = {}
		else:
			r = self.pmonDlg.getStatusReport()
			
		t = {}
		t["bed"] = "%s/%s" % (self.bedTemps['actual'], self.bedTemps['target'])
		for i in range(self.settings.nextruders):
			hek = "HE%d" % i
			t["he%d" % i] = "%s/%s" % (self.heTemps[hek]['actual'], self.heTemps[hek]['target'])
			
		r["Temps"] = t
		
		return r
		
	def tempHandler(self, actualOrTarget, hName, tool, value):
		if hName == "Bed":
			self.bedTemps[actualOrTarget] = value
		else:
			if tool is None:
				k = "HE0"
			else:
				k = "HE%d" % tool
			self.heTemps[k][actualOrTarget] = value
			
		self.heaters.tempHandler(actualOrTarget, hName, tool, value)
		try:
			self.graphDlg.tempHandler(actualOrTarget, hName, tool, value)
		except AttributeError:
			pass
		
	def registerGCodeTemps(self, hes, bed):
		self.heaters.registerGCodeTemps(hes, bed)
		
	def onClose(self, evt):
		if self.pmonDlg and self.pmonDlg.isPrinting():
			dlg = wx.MessageDialog(self, 'Cannot exit with printing active',
					   "Printer is active",
					   wx.OK | wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()
			return
		
		self.terminate()
		
	def isPrinting(self):
		if self.pmonDlg is None:
			return False
		
		return self.pmonDlg.isPrinting()
	
	def setImportButton(self, msg):
		self.importMessage = msg
		if self.pmonDlg is not None:
			self.pmonDlg.setImportButton(self.importMessage)
	
	def setImportFile(self, fn):
		self.importFile = fn
		if self.pmonDlg is not None:
			self.pmonDlg.setImportFile(self.importFile)
	
	def onBReset(self, evt):
		dlg = wx.MessageDialog(self,
				"Are you sure you want to\nreset the %s connection?" % self.printerName,
				"Reset %s connection" % self.printerName,
				wx.YES_NO | wx.NO_DEFAULT | wx.ICON_HAND)
			
		rc = dlg.ShowModal()
		dlg.Destroy()

		if rc == wx.ID_YES:
			self.reprap.reset()
			if self.pmonDlg is not None:
				self.pmonDlg.reset()

	def terminate(self):
		if self.pmonDlg:
			self.pmonDlg.terminate()
		if self.graphDlg:
			self.graphDlg.terminate()
			
		self.reprap.registerTempHandler(None)
		self.settings.save()
		self.parent.PrinterClosed(self.printerName)
		self.Destroy()
		return True
		
	def onGraph(self, evt):
		if not self.graphDlg is None:
			if not self.graphDlg.IsShown():
				self.graphDlg.Show()
			self.graphDlg.Raise()
		
	def onPrintMon(self, evt):
		if self.pmonDlg is None:
			self.pmonDlg = PrintMonitorDlg(self, self.parent, self.reprap, self.printerName)
			self.pmonDlg.setImportButton(self.importMessage)
			self.pmonDlg.setImportFile(self.importFile)
			if not self.settings.monposition is None:
				self.pmonDlg.SetPosition(self.settings.monposition)
		else:
			self.pmonDlg.show()
		
	def closePrintMon(self):
		self.pmonDlg = None
		
	def onEngageZ(self, evt):
		dlg = EngageZDlg(self, self.reprap, self.images)
		dlg.ShowModal()
		dlg.Destroy()
	
	def onRunMacro(self, evt):
		if self.macroDlg is None:
			self.macroDlg = MacroDialog(self, self.parent, self.reprap, self.printerName)
		else:
			self.macroDlg.Show()
			self.macroDlg.Raise()
		
	def onMacroExit(self):
		self.macroDlg.Destroy()
		self.macroDlg = None
		
	def onFirmware(self, evt):
		if self.fwDlg is None:
			self.fwDlg = self.firmware.Firmware(self, self.reprap, self.printerName, self.settings, cmdFolder)
		else:
			self.fwDlg.show()
		
	def onFirmwareExit(self):
		self.fwDlg = None
		
	def onRemember(self, evt):
		self.settings.ctrlposition = self.GetPosition()
		if self.graphDlg is not None:
			self.settings.tempposition = self.graphDlg.GetPosition()
		if self.pmonDlg is not None:
			self.settings.monposition = self.pmonDlg.GetPosition()
			self.pmonDlg.rememberPositions()
			
	def addPendant(self):
		self.pendantAssigned = True
		self.updatePendantButton()
			
	def removePendant(self, connected):
		self.pendantAssigned = False
		self.updatePendantButton(connected)
		
	def onBPendant(self, evt):
		self.parent.assignPendant(self.printerName)
		
	def updatePendantButton(self, connected=True):
		if self.pendantAssigned:
			self.bPendant.SetBitmap(self.parentImages.pngPendanton)
			self.bPendant.SetBitmapDisabled(self.parentImages.pngPendanton)
			self.bPendant.SetToolTipString("%s has control of the pendant" % self.printerName)
			self.bPendant.Enable(False)

		elif connected:
			self.bPendant.SetBitmap(self.parentImages.pngPendantoff)
			self.bPendant.SetToolTipString("Seize control of the pendant")
			self.bPendant.Enable(True)

		else:
			self.bPendant.SetBitmap(self.parentImages.pngPendantclear)
			self.bPendant.SetBitmapDisabled(self.parentImages.pngPendantclear)
			self.bPendant.SetToolTipString("")
			self.bPendant.Enable(False)
		
	def doPendantCommand(self, cmd):
		if cmd.startswith("@"):
			self.metaCommand(cmd)
		else:
			self.reprap.sendNow(cmd)
			
	def metaCommand(self, cmd):
		if cmd == "@print":
			self.emulatePrintButton()
		elif cmd == "@pause":
			self.emulatePauseButton()
		else:
			self.log("Unimplemented meta command: %s" % cmd)
			
	def emulatePrintButton(self):
		if self.pmonDlg is None:
			self.log("Unable to start print - no file loaded")
		else:
			self.pmonDlg.emulatePrintButton()
	
	def emulatePauseButton(self):
		if self.pmonDlg is None:
			self.log("Unable to pause print - no file loaded")
		else:
			self.pmonDlg.emulatePauseButton()
		
	def getXYSpeed(self):
		return self.settings.xyspeed
	
	def getZSpeed(self):
		return self.settings.zspeed
	
	def getESpeed(self):
		return self.settings.espeed
	
	def getEDistance(self):
		return self.settings.edistance
	
	def getBedCommand(self, temp):
		bi = self.heaters.getBedInfo()
		if temp == 2:
			t = bi.highpreset
		elif temp == 1:
			t = bi.lowpreset
		else:
			t = 0
		return ["%s S%d" % (bi.setcmd, t)]
	
	def getHECommand(self, tool, temp):
		hi = self.heaters.getHEInfo(tool)
		if hi is None:
			return None
		
		if temp == 2:
			t = hi.highpreset
		elif temp == 1:
			t = hi.lowpreset
		else:
			t = 0
			
		if self.settings.nextruders == 1:
			return ["%s S%s" % (hi.setcmd, t)]
		else:
			return ["%s T %d S%s" % (hi.setcmd, tool, t)]

		
