import wx
import os
import sys, inspect

from STLViewer.viewdlg import StlViewDlg
from Plater.plater import PlaterDlg
from GEdit.gedit import GEditDlg
from Slic3r.Slic3r import Slic3rDlg
from Printer.printer import PrinterDlg
from reprap import RepRap

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
if cmdFolder not in sys.path:
	sys.path.insert(0, cmdFolder)


BUTTONDIM = (48, 48)


class MyFrame(wx.Frame):
	def __init__(self):
		self.t = 0
		self.seq = 0
		self.exportedStlFile = None
		self.exportedGcFile = None
		self.modified = False
		wx.Frame.__init__(self, None, -1, "STL View", size=(300, 300))
		self.Show()
		
		self.Bind(wx.EVT_CLOSE, self.onClose)
		
		self.bStlView = wx.Button(self, wx.ID_ANY, "VSTL", size=BUTTONDIM)
		self.bStlView.SetToolTipString("View an STL file")
		self.Bind(wx.EVT_BUTTON, self.doViewStl, self.bStlView)
		
		self.bPlater = wx.Button(self, wx.ID_ANY, "PLTR", size=BUTTONDIM)
		self.bPlater.SetToolTipString("Arrange STL objects on a plate")
		self.Bind(wx.EVT_BUTTON, self.doPlater, self.bPlater)
		
		self.bSlic3r = wx.Button(self, wx.ID_ANY, "SLC3R", size=BUTTONDIM)
		self.bSlic3r.SetToolTipString("Invoke slic3r to slice a G Code file")
		self.Bind(wx.EVT_BUTTON, self.doSlic3r, self.bSlic3r)
		
		self.bGEdit = wx.Button(self, wx.ID_ANY, "GEDT", size=BUTTONDIM)
		self.bGEdit.SetToolTipString("Analyze/edit a G Code file")
		self.Bind(wx.EVT_BUTTON, self.doGEdit, self.bGEdit)
		
		
		szFrame = wx.BoxSizer(wx.HORIZONTAL)
		szFrame.Add(self.bStlView)
		szFrame.Add(self.bPlater)
		szFrame.Add(self.bSlic3r)
		szFrame.Add(self.bGEdit)
		
		self.reprap = {}
		self.bPrinter = {}
		self.wPrinter = {}
		self.bId = {}

		b = wx.Button(self, wx.ID_ANY, "PRISM", size=BUTTONDIM)
		self.bId["prism"] = b.GetId()
		b.SetToolTipString("prism printer")
		self.Bind(wx.EVT_BUTTON, self.doPrinter, b)
		b.Enable(False)
		self.bPrinter["prism"] = b
		self.wPrinter["prism"] = None
		self.reprap["prism"] = RepRap(self, "prism", "/dev/tty-prism", 115200, "MARLIN")
		
		b = wx.Button(self, wx.ID_ANY, "CUBOID", size=BUTTONDIM)
		self.bId["cuboid"] = b.GetId()
		b.SetToolTipString("cuboid printer")
		self.Bind(wx.EVT_BUTTON, self.doPrinter, b)
		b.Enable(False)
		self.bPrinter["cuboid"] = b
		self.wPrinter["cuboid"] = None
		self.reprap["cuboid"] = RepRap(self, "cuboid", "/dev/tty-cuboid", 115200, "MARLIN")
		
		szFrame.Add(self.bPrism)
		
		self.SetSizer(szFrame)
		self.Layout()
		self.Fit()
		
	def reportConnection(self, flag, pName):
		self.bPrinters[pName].Enable(flag)
		if not flag:
			if self.wPrinters[pName] is not None:
				self.wPrinters[pName].terminate()
				self.wPrinters[pName] = None
		
	def onClose(self, evt):
		for p in self.printers:
			p.terminate()
		self.Destroy()

	def doViewStl(self, evt):
		dlg = StlViewDlg(self)
		dlg.Show()
		#dlg.Destroy()
		
	def doPlater(self, evt):
		dlg = PlaterDlg(self)
		self.bPlater.Enable(False);
		dlg.Show()
		
	def platerClosed(self):
		self.bPlater.Enable(True);
		
	def doGEdit(self, evt):
		dlg = GEditDlg(self)
		self.bGEdit.Enable(False);
		dlg.Show()
		
	def GEditClosed(self):
		self.bGEdit.Enable(True);
		
	def doSlic3r(self, evt):
		dlg = Slic3rDlg(self)
		self.bSlic3r.Enable(False);
		dlg.Show()
		
	def Slic3rClosed(self):
		self.bSlic3r.Enable(True);
		
	def doPrinter(self, evt):
		bid = evt.GetId()
		pName = None
		for p in self.bId.keys():
			if self.bId[p] == bid:
				pName = p
				break
			
		if pName is None:
			print "cant determine which button was pressed"
			return
		
		self.wPrinter[pName] = PrinterDlg(self, pName, self.reprap[pName])
		self.bPrinter[pName].Enable(False)

	def PrinterClosed(self, pName):
		self.bPrinter[pName].Enable()
		self.wPrinter[pName] = None
		
	def exportStlFile(self, fn):
		print "STL export: (%s)" % fn
		self.exportedStlFile = fn
		
	def exportGcFile(self, fn):
		print "GC export: (%s)" % fn
		self.exportedGcFile = fn
		
	def importStlFile(self):
		print "STL import: (%s)" % self.exportedStlFile
		return self.exportedStlFile
	
	def importGcFile(self):
		print "GC import: (%s)" % self.exportedGcFile
		return self.exportedGcFile

			
class App(wx.App):
	def OnInit(self):
		self.frame = MyFrame()
		self.frame.Show()
		self.SetTopWindow(self.frame)
		return True

app = App(False)
app.MainLoop()

