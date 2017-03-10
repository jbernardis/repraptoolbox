#import wx
import wx.lib.newevent
import os
import inspect
import thread

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))

from images import Images
from filelist import FileList	
from userdata import UserData
from stltool import stl, emitstl
from stlframe import StlFrame
from settings import Settings
from stlview import StlViewer, VIEW_MODE_LOAD, VIEW_MODE_LOOK_HERE
from mirrordlg import MirrorDlg
from rotatedlg import RotateDlg
from translatedlg import TranslateDlg
from scaledlg import ScaleDlg
from gridparamsdlg import GridParamsDlg

BUTTONDIM = (48, 48)

class StlProxy:
	pass

cv = lambda x,y: ((x[0] == y[0]) or (x[0] == y[1]) or (x[0] == y[2]) or
				  (x[1] == y[0]) or (x[1] == y[1]) or (x[1] == y[2]) or
				  (x[2] == y[0]) or (x[2] == y[1]) or (x[2] == y[2]))

(SplitEvent, EVT_SPLIT_UPDATE) = wx.lib.newevent.NewEvent()
SPLIT_NEXT_OBJECT = 1
SPLIT_LAST_OBJECT = 2

class SplitThread:
	def __init__(self, win, obj):
		self.win = win
		self.obj = obj
		self.ofl = [f for f in self.obj.facets]
		self.running = False

	def Start(self):
		self.running = True
		thread.start_new_thread(self.Run, ())

	def Run(self):
		while self.running:
			nf = self.nextObject()
			if len(self.ofl) == 0:
				evt = SplitEvent(state = SPLIT_LAST_OBJECT, facets=nf)
				self.running = False
			else:
				evt = SplitEvent(state = SPLIT_NEXT_OBJECT, facets=nf)
			wx.PostEvent(self.win, evt)	
		
	def nextObject(self):
		nf = [self.ofl.pop(0)]
		fx = 0
		while fx < len(nf):
			nmatchf = []
			for of in self.ofl:
				if cv(nf[fx][1], of[1]):
					nf.append(of)
				else:
					nmatchf.append(of)
			self.ofl = nmatchf
			fx += 1
		
		return nf

class PlaterDlg(wx.Frame):
	def __init__(self, parent):
		wx.Frame.__init__(self, None, wx.ID_ANY, 'Plater', size=(600, 600))
		self.parent = parent
		self.log = self.parent.log
		self.t = 0
		self.seq = 0
		self.modified = False
		self.settings = Settings(cmdFolder)
		self.Show()
		ico = wx.Icon(os.path.join(cmdFolder, "images", "platerico.png"), wx.BITMAP_TYPE_PNG)
		self.SetIcon(ico)
		
		self.savedfile = None
		
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.Bind(EVT_SPLIT_UPDATE, self.splitUpdate)
		
		self.images = Images(os.path.join(cmdFolder, "images"))
		
		self.stlCanvas = StlFrame(self, self.settings)
		
		self.bAdd = wx.BitmapButton(self, wx.ID_ANY, self.images.pngAdd, size=BUTTONDIM)
		self.bAdd.SetToolTipString("Add an STL file to the plate")
		self.Bind(wx.EVT_BUTTON, self.doAdd, self.bAdd)
		
		self.bClone = wx.BitmapButton(self, wx.ID_ANY, self.images.pngClone, size=BUTTONDIM)
		self.bClone.SetToolTipString("Add a copy of the selected object")
		self.Bind(wx.EVT_BUTTON, self.doClone, self.bClone)
		self.bClone.Enable(False)
		
		self.bDel = wx.BitmapButton(self, wx.ID_ANY, self.images.pngDel, size=BUTTONDIM)
		self.bDel.SetToolTipString("Delete the selected object from the plate")
		self.Bind(wx.EVT_BUTTON, self.doDel, self.bDel)
		self.bDel.Enable(False)
		
		self.bDelall = wx.BitmapButton(self, wx.ID_ANY, self.images.pngDelall, size=BUTTONDIM)
		self.bDelall.SetToolTipString("Delete ALL objects from the plate")
		self.Bind(wx.EVT_BUTTON, self.doDelall, self.bDelall)
		self.bDelall.Enable(False)
		
		self.bArrange = wx.BitmapButton(self, wx.ID_ANY, self.images.pngArrange, size=BUTTONDIM)
		self.bArrange.SetToolTipString("Arrange the objects on the plate")
		self.Bind(wx.EVT_BUTTON, self.doArrange, self.bArrange)
		self.bArrange.Enable(False)
		
		self.bCenter = wx.BitmapButton(self, wx.ID_ANY, self.images.pngCenter, size=BUTTONDIM)
		self.bCenter.SetToolTipString("Center the plate")
		self.Bind(wx.EVT_BUTTON, self.doCenter, self.bCenter)
		self.bCenter.Enable(False)
		
		self.bGrid = wx.BitmapButton(self, wx.ID_ANY, self.images.pngGrid, size=BUTTONDIM)
		self.bGrid.SetToolTipString("Create a grid of the selected object")
		self.Bind(wx.EVT_BUTTON, self.doGrid, self.bGrid)
		self.bGrid.Enable(False)
		
		self.bMirror = wx.BitmapButton(self, wx.ID_ANY, self.images.pngMirror, size=BUTTONDIM)
		self.bMirror.SetToolTipString("Mirror the selected object")
		self.Bind(wx.EVT_BUTTON, self.doMirror, self.bMirror)
		self.bMirror.Enable(False)
		
		self.bRotate = wx.BitmapButton(self, wx.ID_ANY, self.images.pngRotate, size=BUTTONDIM)
		self.bRotate.SetToolTipString("Rotate the selected object")
		self.Bind(wx.EVT_BUTTON, self.doRotate, self.bRotate)
		self.bRotate.Enable(False)
		
		self.bTranslate = wx.BitmapButton(self, wx.ID_ANY, self.images.pngTranslate, size=BUTTONDIM)
		self.bTranslate.SetToolTipString("Translate the selected object")
		self.Bind(wx.EVT_BUTTON, self.doTranslate, self.bTranslate)
		self.bTranslate.Enable(False)
		
		self.bScale = wx.BitmapButton(self, wx.ID_ANY, self.images.pngScale, size=BUTTONDIM)
		self.bScale.SetToolTipString("Scale the selected object")
		self.Bind(wx.EVT_BUTTON, self.doScale, self.bScale)
		self.bScale.Enable(False)
		
		self.bSplit = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSplit, size=BUTTONDIM)
		self.bSplit.SetToolTipString("Split the selected object")
		self.Bind(wx.EVT_BUTTON, self.doSplit, self.bSplit)
		self.bSplit.Enable(False)
		
		self.bSaveAs = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFilesaveas, size=BUTTONDIM)
		self.bSaveAs.SetToolTipString("Save the plate to an STL file")
		self.Bind(wx.EVT_BUTTON, self.doSaveAs, self.bSaveAs)
		self.bSaveAs.Enable(False)
		
		self.bExport = wx.BitmapButton(self, wx.ID_ANY, self.images.pngExport, size=BUTTONDIM)
		self.bExport.SetToolTipString("Export the plate to the toolbox")
		self.Bind(wx.EVT_BUTTON, self.doExport, self.bExport)
		self.bExport.Enable(False)
		
		self.bView = wx.BitmapButton(self, wx.ID_ANY, self.images.pngView, size=BUTTONDIM)
		self.bView.SetToolTipString("View the currently selected object")
		self.Bind(wx.EVT_BUTTON, self.doView, self.bView)
		self.bView.Enable(False)
		
		self.bViewPlate = wx.BitmapButton(self, wx.ID_ANY, self.images.pngViewplate, size=BUTTONDIM)
		self.bViewPlate.SetToolTipString("View the entire plate")
		self.Bind(wx.EVT_BUTTON, self.doViewPlate, self.bViewPlate)
		self.bViewPlate.Enable(False)
		
		self.cbPreview = wx.CheckBox(self, wx.ID_ANY, "3D Preview")
		self.cbPreview.SetValue(self.settings.preview)
		self.Bind(wx.EVT_CHECKBOX, self.onCbPreview, self.cbPreview)
		
		self.cbCenterOnArrange = wx.CheckBox(self, wx.ID_ANY, "Center Plate After Arrange")
		self.cbCenterOnArrange.SetValue(self.settings.centeronarrange)
		self.Bind(wx.EVT_CHECKBOX, self.onCbCenterOnArrange, self.cbCenterOnArrange)
		
		self.cbAutoExport = wx.CheckBox(self, wx.ID_ANY, "Automatically export when saving")
		self.cbAutoExport.SetValue(self.settings.autoexport)
		self.Bind(wx.EVT_CHECKBOX, self.onCbAutoExport, self.cbAutoExport)
		
		self.cbAutoEnqueue = wx.CheckBox(self, wx.ID_ANY, "Automatically enqueue the file when exporting")
		self.cbAutoEnqueue.SetValue(self.settings.autoenqueue)
		self.Bind(wx.EVT_CHECKBOX, self.onCbAutoEnqueue, self.cbAutoEnqueue)
		
		self.strategyList = ['column', 'row', 'spiral']
		self.rbStrategy = wx.RadioBox(
				self, -1, "Arrange Strategy", wx.DefaultPosition, wx.DefaultSize,
				self.strategyList, 1, wx.RA_SPECIFY_COLS
				)
		
		self.Bind(wx.EVT_RADIOBOX, self.onStrategy, self.rbStrategy)
		self.rbStrategy.SetToolTipString("Choose the strategy for auto-arrange")
		if not self.settings.arrangestrategy in self.strategyList:
			self.settings.arrangestrategy = self.strategyList[0]
		self.rbStrategy.SetStringSelection(self.settings.arrangestrategy)
		
		self.scMargin = wx.SpinCtrl(self, wx.ID_ANY, "Arrange Margin", size=(40, -1))
		self.scMargin.SetRange(1,5)
		self.scMargin.SetValue(self.settings.arrangemargin)
		self.scMargin.SetToolTipString("Choose the distance between objects")
		self.Bind(wx.EVT_SPINCTRL, self.onScMargin, self.scMargin)

		
		szFrame = wx.BoxSizer(wx.HORIZONTAL)
		szLeft = wx.BoxSizer(wx.VERTICAL)
		
		szCanvas = wx.BoxSizer(wx.VERTICAL)
		szCanvas.AddSpacer((10, 20))
		szCanvas.Add(self.stlCanvas)
		szCanvas.AddSpacer((10, 10))
		
		szLeft.Add(szCanvas)
		szRight = wx.BoxSizer(wx.VERTICAL)
		
		self.files = FileList(self)
		self.Bind(wx.EVT_LISTBOX, self.doFileSelect, self.files)
		szRight.AddSpacer((10, 20))
		szRight.Add(self.files)
		szRight.AddSpacer((10, 10))
		
		szBtn = wx.BoxSizer(wx.VERTICAL)
		szBtnLn1 = wx.BoxSizer(wx.HORIZONTAL)
		szBtnLn2 = wx.BoxSizer(wx.HORIZONTAL)
		szBtnLn3 = wx.BoxSizer(wx.HORIZONTAL)
		szOptions = wx.BoxSizer(wx.HORIZONTAL)
		szOptionsL = wx.BoxSizer(wx.VERTICAL)
		szOptionsR = wx.BoxSizer(wx.VERTICAL)
		
		szBtnLn1.Add(self.bAdd)
		szBtnLn1.Add(self.bDel)
		szBtnLn1.Add(self.bDelall)
		szBtnLn1.AddSpacer(BUTTONDIM)
		szBtnLn1.Add(self.bView)
		szBtnLn1.Add(self.bViewPlate)
		szBtnLn1.AddSpacer(BUTTONDIM)
		
		szBtnLn2.Add(self.bArrange)
		szBtnLn2.Add(self.bCenter)
		szBtnLn2.AddSpacer(BUTTONDIM)
		szBtnLn2.Add(self.bClone)
		szBtnLn2.Add(self.bGrid)
		szBtnLn2.AddSpacer(BUTTONDIM)
		szBtnLn2.Add(self.bSplit)
		szBtnLn2.AddSpacer(BUTTONDIM)
		
		szBtnLn3.Add(self.bMirror)
		szBtnLn3.Add(self.bRotate)
		szBtnLn3.Add(self.bTranslate)
		szBtnLn3.Add(self.bScale)
		szBtnLn3.AddSpacer(BUTTONDIM)
		szBtnLn3.Add(self.bSaveAs)
		szBtnLn3.Add(self.bExport)
		
		szBtn.Add(szBtnLn1)
		szBtn.Add(szBtnLn2)
		szBtn.Add(szBtnLn3)
		
		szRight.Add(szBtn, 1, wx.ALIGN_CENTER_HORIZONTAL)
		szRight.AddSpacer((5, 5))
		
		szOptionsL.Add(self.cbPreview)
		szOptionsL.AddSpacer((5, 5))
		szOptionsL.Add(self.cbCenterOnArrange)
		szOptionsL.AddSpacer((5, 10))
		szOptionsL.Add(self.cbAutoExport)
		szOptionsL.AddSpacer((5, 5))
		szOptionsL.Add(self.cbAutoEnqueue)

		szOptionsR.Add(self.rbStrategy)
		szOptionsR.AddSpacer((5, 5))
		szMargin = wx.BoxSizer(wx.HORIZONTAL)
		szMargin.Add(wx.StaticText(self, wx.ID_ANY, "Arrange margin:"))
		szMargin.AddSpacer((5,5))
		szMargin.Add(self.scMargin)
		szOptionsR.Add(szMargin)
		
		szOptions.AddSpacer((10, 10))
		szOptions.Add(szOptionsL)
		szOptions.AddSpacer((30, 10))
		szOptions.Add(szOptionsR)
		szOptions.AddSpacer((10, 10))
		
		szRight.Add(szOptions, 1, wx.ALIGN_CENTER_HORIZONTAL)
		#szRight.AddSpacer((10, 10))

		szFrame.AddSpacer((20, 10))		
		szFrame.Add(szLeft)
		szFrame.AddSpacer((20, 10))		
		szFrame.Add(szRight)
		szFrame.AddSpacer((20, 10))		
		
		self.SetSizer(szFrame)
		self.Layout()
		self.Fit()
		
	def enableButtons(self):
		v = (self.files.countFiles() > 0)
		ud = self.files.getSelection()
		
		self.bAdd.Enable(True)
		self.bClone.Enable(v and not ud is None)
		self.bGrid.Enable(v and not ud is None)
		self.bDel.Enable(v and not ud is None)
		self.bView.Enable(v and not ud is None)
		self.bMirror.Enable(v and not ud is None)
		self.bRotate.Enable(v and not ud is None)
		self.bTranslate.Enable(v and not ud is None)
		self.bScale.Enable(v and not ud is None)
		self.bSplit.Enable(v and not ud is None)
		self.bDelall.Enable(v)
		self.bArrange.Enable(v)
		self.bCenter.Enable(v)
		self.bSaveAs.Enable(v)
		self.bExport.Enable(v and not self.settings.autoexport and self.savedfile is not None)
		self.bViewPlate.Enable(v)
		
	def disableButtons(self):
		self.bAdd.Enable(False)
		self.bClone.Enable(False)
		self.bGrid.Enable(False)
		self.bDel.Enable(False)
		self.bView.Enable(False)
		self.bMirror.Enable(False)
		self.bRotate.Enable(False)
		self.bTranslate.Enable(False)
		self.bScale.Enable(False)
		self.bSplit.Enable(False)
		self.bDelall.Enable(False)
		self.bArrange.Enable(False)
		self.bCenter.Enable(False)
		self.bSaveAs.Enable(False)
		self.bExport.Enable(False)
		self.bViewPlate.Enable(False)
		
	def onScMargin(self, evt):
		self.settings.arrangemargin = self.scMargin.GetValue()

	def onCbPreview(self, evt):
		self.settings.preview = self.cbPreview.GetValue()
		
	def onStrategy(self, evt):
		self.settings.arrangestrategy = self.strategyList[evt.GetInt()]

	def onCbCenterOnArrange(self, evt):
		self.settings.centeronarrange = self.cbCenterOnArrange.GetValue()

	def doAdd(self, evt):
		wildcard = "STL (*.stl)|*.stl;*.STL|"	 \
			"All files (*.*)|*.*"
			
		while True:
			dlg = wx.FileDialog(
				self, message="Choose an STL file",
				defaultDir=self.settings.lastdirectory, 
				defaultFile="",
				wildcard=wildcard,
				style=wx.OPEN)
	
			rc = dlg.ShowModal()
			if rc == wx.ID_OK:
				path = dlg.GetPath().encode('ascii','ignore')
			dlg.Destroy()
			if rc != wx.ID_OK:
				return
			
			self.settings.lastdirectory = os.path.dirname(path)
			
			if self.settings.preview:
				dlg = StlViewer(self, path, path, VIEW_MODE_LOAD, self.images, self.settings)
				rc = dlg.ShowModal()
				dlg.Destroy()
			
			if not self.settings.preview or rc == wx.ID_OK:
				stlFile = stl(filename = path)
				ud = UserData(path, stlFile, self.seq)
				self.files.addFile(ud)
				self.stlCanvas.addHull(stlFile, self.seq)
				self.seq += 1
				self.modified = True
				self.enableButtons()
				return
			
	def setFilesSelection(self, seq):
		self.files.setSelection(seq)
		self.enableButtons()
		
	def setHullSelection(self, seq):
		self.stlCanvas.setSelection(seq)
		self.enableButtons()
		
	def doClone(self, evt):
		self.clone()
		
	def clone(self):
		self.stlCanvas.commitDeltas(None)
		ud = self.files.getSelection()
		if ud is None:
			return None
		
		mySeq = self.seq
		self.seq += 1
		udNew = ud.clone(mySeq)
		
		self.files.addFile(udNew)
		self.stlCanvas.addHull(udNew.getStlObj(), mySeq)
			
		self.modified = True
		self.enableButtons()
		return mySeq
		
	def doDel(self, evt):
		fx = self.files.getSelectionIndex()
		if fx == wx.NOT_FOUND:
			return
		
		ud = self.files.getUserDataByIndex(fx)
		if not ud is None:
			self.stlCanvas.delHull(ud.getSeqNbr())
			
		self.files.delFileByIndex(fx)
		if self.files.countFiles() > 0:
			self.modified = True
		else:
			self.modified = False
			self.seq = 0

		self.enableButtons()
		
	def doDelall(self, evt):
		dlg = wx.MessageDialog(self,
			"This will delete ALL items.\nAre you sure you want to do this?",
			"Confirm Delete All",
			wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		rc = dlg.ShowModal()
		dlg.Destroy()
		if rc == wx.ID_YES:
			self.modified = False
			self.files.delAll()
			self.stlCanvas.delAllHulls()
			self.seq = 0
			self.enableButtons()
		
	def doArrange(self, evt):
		self.stlCanvas.arrange()
		self.modified = True
		
	def findUserDataBySeq(self, seq):
		return self.files.findUserDataBySeq(seq)
		
	def doMirror(self, evt):
		dlg = MirrorDlg(self, self.stlCanvas, self.images, wx.GetMousePosition())
		dlg.ShowModal()
		dlg.Destroy()
			
	def doRotate(self, evt):
		dlg = RotateDlg(self, self.stlCanvas, self.images, wx.GetMousePosition())
		dlg.ShowModal()
		dlg.Destroy()
			
	def doTranslate(self, evt):
		dlg = TranslateDlg(self, self.stlCanvas, self.images, wx.GetMousePosition())
		dlg.ShowModal()
		dlg.Destroy()
			
	def doScale(self, evt):
		dlg = ScaleDlg(self, self.stlCanvas, self.images, wx.GetMousePosition())
		dlg.ShowModal()
		dlg.Destroy()
		
	def doCenter(self, evt):
		self.stlCanvas.centerPlate()
		self.modified = True
		
	def doGrid(self, evt):
		ud = self.files.getSelection()
		if ud is None:
			return
		
		masterSeq = ud.getSeqNbr()
		dlg = GridParamsDlg(self, self.images, wx.GetMousePosition())
		rc = dlg.ShowModal()
		if rc == wx.ID_OK:
			rows, cols = dlg.getValues()
			
		dlg.Destroy()
		if rc != wx.ID_OK:
			return
		
		copies = rows * cols - 1
		if copies == 1:
			return
		
		self.modified = True
		
		seqNbrs = [masterSeq]
		for i in range(copies):
			seqNbrs.append(self.clone())
			
		self.stlCanvas.gridArrange(seqNbrs, rows, cols)
		
	def doSplit(self, evt):
		ud = self.files.getSelection()
		if ud is None:
			return
	
		self.disableButtons()	
		obj = ud.getStlObj()
		self.part = 0
		self.partfn = ud.getFn()
		self.splitter = SplitThread(self, obj)
		self.splitter.Start()
		
	def splitUpdate(self, evt):
		finished = False
		if evt.state == SPLIT_LAST_OBJECT:
			finished = True
			if self.part == 0:
				dlg = wx.MessageDialog(self,
					"Object consists of a single mesh",
					"Cannot Split",
					wx.OK | wx.ICON_EXCLAMATION)
				dlg.ShowModal()
				dlg.Destroy()
				self.splitter = None
				self.enableButtons()
				return
			
		nf = evt.facets
		if self.part == 0:
			ud = self.files.getSelection()
			ud.getStlObj().setFacets(nf)
			ud.setPart(self.part)
			self.files.refreshFilesList(ud.getSeqNbr())
			self.stlCanvas.refreshHull(ud.getSeqNbr())
		else:
			nobj = stl(filename=None)
			nobj.setFacets(nf)
			ud = UserData(self.partfn, nobj, self.seq)
			ud.setPart(self.part)
			self.files.addFile(ud)
			self.stlCanvas.addHull(nobj, self.seq)
			self.seq += 1
			
		self.part += 1
		
		if finished:
			self.modified = True
			self.splitter = None
			self.enableButtons()
		else:
			self.disableButtons()
			
	def onCbAutoEnqueue(self, evt):
		self.settings.autoenqueue = self.cbAutoEnqueue.GetValue()
		
	def onCbAutoExport(self, evt):
		self.settings.autoexport = self.cbAutoExport.GetValue()
		self.bExport.Enable(not self.settings.autoExport and self.savedfile is not None)

	def doExport(self, evt):
		self.parent.exportStlFile(self.savedfile, self.settings.autoenqueue)
		
	def doSaveAs(self, evt):
		wildcard = "STL (*.stl)|*.stl;*.STL"
		dlg = wx.FileDialog(
			self, message="Save file as ...", defaultDir=self.settings.lastdirectory, 
			defaultFile="", wildcard=wildcard, style=wx.SAVE | wx.FD_OVERWRITE_PROMPT
			)
		
		rc = dlg.ShowModal()
		if rc == wx.ID_OK:
			path = dlg.GetPath().encode('ascii','ignore')
			if os.path.splitext(path)[1].lower() != ".stl":
				path += ".stl"
			
		dlg.Destroy()
		if rc != wx.ID_OK:
			return
		
		self.stlCanvas.commitDeltas(None)
		objs = self.files.getStlObjects()
		facets = []
		for o in objs:
			facets.extend(o.facets)
			
		self.savedfile = path
		
		emitstl(path, facets=facets, objname="PlaterObject", binary=False)
		self.modified = False
		
		dlg = wx.MessageDialog(self,
			"File '%s' written" % path,
			"Save",
			wx.OK | wx.ICON_INFORMATION)
		
		if self.settings.autoexport:
			self.parent.exportStlFile(self.savedfile)

		dlg.ShowModal()
		dlg.Destroy()
		self.enableButtons()

	def doView(self, evt):
		self.viewObject()
		
	def viewObject(self):
		self.stlCanvas.commitDeltas(None)
		ud = self.files.getSelection()
		dlg = StlViewer(self, ud.getStlObj(), ud.getName(), VIEW_MODE_LOOK_HERE, self.images, self.settings)
		dlg.ShowModal()
		dlg.Destroy()
		
	def doViewPlate(self, evt):
		self.stlCanvas.commitDeltas(None)
		objs = self.files.getStlObjects()
		
		plateStl = StlProxy()
		plateStl.facets = []
		for o in objs:
			plateStl.facets.extend(o.facets)
		dlg = StlViewer(self, plateStl, "Plate", VIEW_MODE_LOOK_HERE, self.images, self.settings)
		dlg.ShowModal()
		dlg.Destroy()

		
	def doFileSelect(self, evt):
		self.enableButtons()
			
	def onClose(self, evt):
		self.settings.save()
		if self.modified:
			dlg = wx.MessageDialog(self,
				"You have unsaved changes.\nAre you sure you want to exit?",
				"Confirm Exit With Pending Changes",
				wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			rc = dlg.ShowModal()
			dlg.Destroy()
			if rc == wx.ID_YES:
				self.parent.platerClosed()
		else:
			self.parent.platerClosed()

