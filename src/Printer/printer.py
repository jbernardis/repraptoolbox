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

BUTTONDIM = (48, 48)

class PrinterDlg(wx.Frame):
	def __init__(self, parent, printerName, reprap):
		wx.Frame.__init__(self, None, wx.ID_ANY, "%s manual control" % printerName, size=(100, 100))
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.parent = parent
		self.log = parent.log
		self.printerName = printerName
		self.reprap = reprap
		self.settings = PrtSettings(cmdFolder, printerName)
		self.images = Images(os.path.join(cmdFolder, "images"))
		
		self.graphDlg = None
		self.pmonDlg = None
		self.macroDlg = None
		
		self.zEngaged = False
		
		self.moveAxis = ManualCtl(self, reprap, printerName)				
		szWindow = wx.BoxSizer(wx.VERTICAL)
		szWindow.Add(self.moveAxis)
		
		szHeaters = wx.BoxSizer(wx.VERTICAL)
		self.heaters = Heaters(self, self.reprap, printerName)
		szHeaters.Add(self.heaters)
		szWindow.AddSpacer((10, 10))
		
		szWindow.Add(szHeaters, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		szWindow.AddSpacer((20, 20))

		btnhsizer = wx.BoxSizer(wx.HORIZONTAL)
		btnhsizer.AddSpacer((10, 10))
		
		self.bGraph = wx.BitmapButton(self, wx.ID_ANY, self.images.pngGraph, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onGraph, self.bGraph)
		self.bGraph.SetToolTipString("Show Temperature monitoring graph")
		btnhsizer.Add(self.bGraph)
		btnhsizer.AddSpacer((10, 10))
		
		self.bPrintMon = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPrintmon, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onPrintMon, self.bPrintMon)
		self.bPrintMon.SetToolTipString("Show dialog box to monitor printing a G Code file")
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
		
		self.bPendant = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPendantoff, size=BUTTONDIM, style = wx.NO_BORDER)
		self.bPendant.SetToolTipString("Connect/disconnect the pendant")
		self.Bind(wx.EVT_BUTTON, self.onBPendant, self.bPendant)
		btnhsizer.Add(self.bPendant)
		btnhsizer.AddSpacer((50, 10))
		self.pendantConnected = False

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
		
	def tempHandler(self, actualOrTarget, hName, tool, value):
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
	
	def onBReset(self, evt):
		print "ask if you are certain here"
		self.reprap.reset()

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
		self.graphDlg = TempDlg(self, self.parent, self.settings.nextruders, self.printerName)
		if not self.settings.tempposition is None:
			self.graphDlg.SetPosition(self.settings.tempposition)
		self.bGraph.Enable(False)
		
	def closeGraph(self):
		self.graphDlg = None
		self.bGraph.Enable(True)
		
	def onPrintMon(self, evt):
		self.pmonDlg = PrintMonitorDlg(self, self.parent, self.reprap, self.printerName)
		if not self.settings.monposition is None:
			self.pmonDlg.SetPosition(self.settings.monposition)
		self.bPrintMon.Enable(False)
		
	def closePrintMon(self):
		self.pmonDlg = None
		self.bPrintMon.Enable(True)
		
	def onEngageZ(self, evt):
		print "engage z"
		self.zEngaged = not self.zEngaged
		if self.zEngaged:
			self.bEngageZ.SetBitmap(self.images.pngDisengagez)
		else:
			self.bEngageZ.SetBitmap(self.images.pngEngagez)
		
	def onRunMacro(self, evt):
		self.macroDlg = MacroDialog(self, self.parent, self.reprap, self.printerName)
		self.bMacros.Enable(False)
		
	def onMacroExit(self):
		self.macroDlg.Destroy()
		self.macroDlg = None
		self.bMacros.Enable(True)
		
	def onFirmware(self, evt):
		print "firmware"
		
	def onRemember(self, evt):
		self.settings.ctrlposition = self.GetPosition()
		if self.graphDlg is not None:
			self.settings.tempposition = self.graphDlg.GetPosition()
		if self.pmonDlg is not None:
			self.settings.monposition = self.pmonDlg.GetPosition()
			self.pmonDlg.rememberPositions()
			
	def addPendant(self):
		self.pendantConnected = True
		self.updatePendantButton()
			
	def removePendant(self):
		self.pendantConnected = False
		self.updatePendantButton()
		
	def onBPendant(self, evt):
		self.parent.assignPendant(self.printerName)
		
	def updatePendantButton(self):
		if self.pendandConnected:
			self.bPendant.SetBitMap(self.images.pngPendanton)
		else:
			self.bPendant.SetBitMap(self.images.pngPendantoff)
		
	def doPendantCommand(self, cmd):
		self.reprap.sendNow(cmd)
		
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

		
