'''
Created on Oct 28, 2016

@author: Jeff
'''
import os, sys, inspect

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
if cmdFolder not in sys.path:
	sys.path.insert(0, cmdFolder)

import wx

from settings import Settings 
from images import Images
from manualctl import ManualCtl
from heaters import Heaters
from tempgraph import TempDlg

BUTTONDIM = (48, 48)

class PrinterDlg(wx.Dialog):
	def __init__(self, parent, printerName, reprap):
		wx.Dialog.__init__(self, None, title=printerName, size=(100, 100))
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.parent = parent
		self.printerName = printerName
		self.reprap = reprap
		self.settings = Settings(cmdFolder, printerName)
		self.images = Images(os.path.join(cmdFolder, "images"))
		
		self.moveAxis = ManualCtl(self, reprap, printerName)				
		szWindow = wx.BoxSizer(wx.VERTICAL)
		szWindow.Add(self.moveAxis)
		
		szHeaters = wx.BoxSizer(wx.VERTICAL)
		self.heaters = Heaters(self, self.reprap, printerName)
		szHeaters.Add(self.heaters)
		szWindow.AddSpacer((10, 10))
		
		szWindow.Add(szHeaters, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		szWindow.AddSpacer((20, 20))
		
		self.bGraph = wx.Button(self, wx.ID_ANY, "Graph")
		self.Bind(wx.EVT_BUTTON, self.onGraph, self.bGraph)
		szWindow.Add(self.bGraph)
		
		self.SetSizer(szWindow)
		
		self.Show()
		self.Fit()
		
		self.reprap.registerTempHandler(self.tempHandler)
		
	def tempHandler(self, actualOrTarget, hName, tool, value):
		print "in printerdlg th: ", actualOrTarget, hName, tool, value
		self.heaters.tempHandler(actualOrTarget, hName, tool, value)
		try:
			self.graphDlg.tempHandler(actualOrTarget, hName, tool, value)
		except AttributeError:
			pass
		
	def onClose(self, evt):
		self.reprap.registerTempHandler(None)
		self.settings.save()
		self.parent.PrinterClosed()
		self.Destroy()
		
	def onGraph(self, evt):
		self.graphDlg = TempDlg(self, self.settings.nextruders, self.printerName)
		
	def closeGraph(self):
		self.graphDlg = None
		
class RepRap:
	def __init__(self):
		pass
	
	def sendNow(self, cmd):
		print "Send Now (%s)" % cmd
		
	def registerTempHandler(self, handler):
		pass

class App(wx.App):
	def OnInit(self):
		prtr = RepRap()
		self.dlg = PrinterDlg(self, "prism", prtr)
		return True
		
	def PrinterClosed(self):
		pass
	def exportStlFile(self, fn):
		pass
	def exportGcFile(self, fn):
		pass
	def importStlFile(self):
		return None
	def importGcFile(self):
		return None

			
if __name__ == '__main__':
	app = App(False)
	app.MainLoop()
