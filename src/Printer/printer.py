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

BUTTONDIM = (48, 48)

class PrinterDlg(wx.Frame):
	def __init__(self, parent, printerName, reprap):
		wx.Frame.__init__(self, None, wx.ID_ANY, printerName, size=(100, 100))
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.parent = parent
		self.log = parent.log
		self.printerName = printerName
		self.reprap = reprap
		self.settings = PrtSettings(cmdFolder, printerName)
		self.images = Images(os.path.join(cmdFolder, "images"))
		
		self.graphDlg = None
		self.pmonDlg = None
		
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
		
		box = wx.StaticBox(self, wx.ID_ANY, " Buttons ")
		btnvsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
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

		btnvsizer.AddSpacer((10, 10))
		btnvsizer.Add(btnhsizer)
		btnvsizer.AddSpacer((10, 10))
		
		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(10, 10)
		hsz.Add(btnvsizer)
		
		szWindow.Add(hsz)
		szWindow.AddSpacer((10, 10))
		
		self.SetSizer(szWindow)
		
		self.Show()
		self.Fit()
		
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
		self.bPrintMon.Enable(False)
		
	def closePrintMon(self):
		self.pmonDlg = None
		self.bPrintMon.Enable(True)
		
	def onEngageZ(self, evt):
		print "engage z"
		if self.graphDlg is not None:
			self.settings.tempposition = self.graphDlg.GetPosition()
			print "set remembered temp graph position to ", self.settings.tempposition
		self.zEngaged = not self.zEngaged
		if self.zEngaged:
			self.bEngageZ.SetBitmap(self.images.pngDisengagez)
		else:
			self.bEngageZ.SetBitmap(self.images.pngEngagez)
		
	def onRunMacro(self, evt):
		print "run macro"
		
	def onFirmware(self, evt):
		print "firmware"
		
