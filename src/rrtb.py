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
	
from images import Images
from settings import Settings


BUTTONDIM = (48, 48)
PBUTTONDIM = (96, 96)


class MyFrame(wx.Frame):
	def __init__(self):
		self.t = 0
		self.seq = 0
		self.exportedStlFile = None
		self.exportedGcFile = None
		self.modified = False
		wx.Frame.__init__(self, None, -1, "RepRap Toolbox", size=(300, 300))
		self.Show()
		
		self.settings = Settings(cmdFolder)
		self.images = Images(os.path.join(cmdFolder, "images"))
		
		self.Bind(wx.EVT_CLOSE, self.onClose)
		
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
		
		szVFrame.Add(szButtonRow)
		szVFrame.AddSpacer((20, 20))
		
		self.reprap = {}
		self.bPrinter = {}
		self.wPrinter = {}
		self.bId = {}

		b = wx.Button(self, wx.ID_ANY, "PRISM", size=PBUTTONDIM)
		self.bId["prism"] = b.GetId()
		b.SetToolTipString("prism printer")
		self.Bind(wx.EVT_BUTTON, self.doPrinter, b)
		b.Enable(False)
		self.bPrinter["prism"] = b
		self.wPrinter["prism"] = None
		self.reprap["prism"] = RepRap(self, "prism", "/dev/tty-prism", 115200, "MARLIN")
		
		b = wx.Button(self, wx.ID_ANY, "CUBOID", size=PBUTTONDIM)
		self.bId["cuboid"] = b.GetId()
		b.SetToolTipString("cuboid printer")
		self.Bind(wx.EVT_BUTTON, self.doPrinter, b)
		b.Enable(False)
		self.bPrinter["cuboid"] = b
		self.wPrinter["cuboid"] = None
		self.reprap["cuboid"] = RepRap(self, "cuboid", "/dev/tty-cuboid", 115200, "MARLIN")
		
		box = wx.StaticBox(self, wx.ID_ANY, " Printers ")
		bvsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bhsizer = wx.BoxSizer(wx.HORIZONTAL)
		bhsizer.AddSpacer((10, 10))
		
		for b in sorted(self.bPrinter.keys()):
			bhsizer.Add(self.bPrinter[b])
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
		
	def createSectionButtons(self, section, handler):
		buttons = {}
		bids = {}
		cmds = self.settings.getSection(section)
		order = []
		if cmds is not None:
			for n in cmds.keys():
				print "processing (%s)" % n
				if n == "order":
					order = cmds[n].split(",")
				else:
					b = wx.BitmapButton(self, wx.ID_ANY, self.images.getByName(n), size=BUTTONDIM)
					buttons[n] = b
					bids[n] = b.GetId()
					self.Bind(wx.EVT_BUTTON, handler, b)
					
		if len(order) != len(buttons.keys()):
			print "number of items in %s order list (%d) != number of tools (%d).  Using alpha order" % (section, len(order), len(buttons.keys()))
			order = sorted(buttons.keys())
			
		return buttons, bids, cmds, order

		
	def reportConnection(self, flag, pName):
		self.bPrinter[pName].Enable(flag)
		if not flag:
			if self.wPrinter[pName] is not None:
				self.wPrinter[pName].terminate()
				self.wPrinter[pName] = None
		
	def onClose(self, evt):
		for p in self.reprap.keys():
			self.reprap[p].terminate()
		self.Destroy()

	def doViewStl(self, evt):
		dlg = StlViewDlg(self)
		dlg.Show()
	
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
		
	def exportGcFile(self, fn):
		self.exportedGcFile = fn
		
	def importStlFile(self):
		return self.exportedStlFile
	
	def importGcFile(self):
		return self.exportedGcFile

			
class App(wx.App):
	def OnInit(self):
		self.frame = MyFrame()
		self.frame.Show()
		self.SetTopWindow(self.frame)
		return True

app = App(False)
app.MainLoop()

