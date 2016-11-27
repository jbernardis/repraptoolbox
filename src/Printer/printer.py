'''
Created on Oct 28, 2016

@author: Jeff
'''
import os, sys, inspect

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
		
		self.moveAxis = ManualCtl(self, reprap, printerName)				
		szWindow = wx.BoxSizer(wx.VERTICAL)
		szWindow.Add(self.moveAxis)
		
		szHeaters = wx.BoxSizer(wx.VERTICAL)
		self.heaters = Heaters(self, self.reprap, printerName)
		szHeaters.Add(self.heaters)
		szWindow.AddSpacer((10, 10))
		
		szWindow.Add(szHeaters, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		szWindow.AddSpacer((20, 20))
		
		self.bGraph = wx.BitmapButton(self, wx.ID_ANY, self.images.pngGraph, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onGraph, self.bGraph)
		self.bGraph.SetToolTipString("Show Temperature monitoring grapg")
		szWindow.Add(self.bGraph)
		
		self.bPrintMon = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPrintmon, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onPrintMon, self.bPrintMon)
		self.bPrintMon.SetToolTipString("Show dialog box to monitor printing a G Code file")
		szWindow.Add(self.bPrintMon)
		
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
