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

BUTTONDIM = (48, 48)

class PrinterDlg(wx.Dialog):
	def __init__(self, parent, printerName, reprap):
		wx.Dialog.__init__(self, None, title=printerName, size=(100, 100))
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.parent = parent
		self.printerName = printerName
		self.settings = Settings(cmdFolder, printerName)
		self.images = Images(os.path.join(cmdFolder, "images"))
		
		self.moveAxis = ManualCtl(self, reprap)				
		self.sizerMove = wx.BoxSizer(wx.VERTICAL)
		self.sizerMove.Add(self.moveAxis)
		
		self.SetSizer(self.sizerMove)
		
		self.Show()
		self.Fit()
		
	def onClose(self, evt):
		self.settings.save()
		self.parent.PrinterClosed()
		self.Destroy()
		
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
