import wx
import os
import re
import time
import inspect

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))

from settings import Settings
from cnc import CNC
from gcframe import GcFrame
from gclistctrl import GcodeListCtrl
from shiftmodel import ShiftModelDlg
from modtemps import ModifyTempsDlg
from modspeed import ModifySpeedDlg
from editgcode import EditGCodeDlg
from filamentchange import FilamentChangeDlg
from savelayer import SaveLayerDlg
from images import Images
from tools import formatElapsed
from gcsuffix import parseGCSuffix, modifyGCSuffix
from properties import PropertiesDlg
from propenums import PropertyEnum

gcRegex = re.compile("[-]?\d+[.]?\d*")
BUTTONDIM = (48, 48)
TITLE_PREFIX = "G Code Analyze/Edit"
reX = re.compile("(.*[xX])([0-9\.]+)(.*)")
reY = re.compile("(.*[yY])([0-9\.]+)(.*)")
reZ = re.compile("(.*[zZ])([0-9\.]+)(.*)")
reS = re.compile("(.*[sS])([0-9\.]+)(.*)")
reF = re.compile("(.*[fF])([0-9\.]+)(.*)")
reE = re.compile("(.*[eE])([0-9\.]+)(.*)")


class GEditDlg(wx.Frame):
	def __init__(self, parent):
		self.parent = parent
		wx.Frame.__init__(self, None, wx.ID_ANY, TITLE_PREFIX, size=(600, 600))
		self.Show()
		ico = wx.Icon(os.path.join(cmdFolder, "images", "geditico.png"), wx.BITMAP_TYPE_PNG)
		self.SetIcon(ico)
		
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.settings = Settings(cmdFolder)
		self.propDlg = None
		
		self.log = self.parent.log
		
		self.images = Images(os.path.join(cmdFolder, "images"))
		
		self.shiftX = 0
		self.shiftY = 0
		self.modified = False
		self.filename = None
		self.importFileName = None
		
		self.gObj = self.loadGCode(self.filename)
		if self.gObj is not None:
			self.updateTitle()

		self.gcFrame = GcFrame(self, self.gObj, self.settings)
		self.stLayerText = wx.StaticText(self, wx.ID_ANY, "Layer Height:   0.00")

		ht = self.gcFrame.GetSize().Get()[1] - 2*BUTTONDIM[1] - 20
		
		if self.gObj is None:
			lmax = 1
		else:
			lmax = self.gObj.layerCount()-1
		
		self.slLayers = wx.Slider(
			self, wx.ID_ANY, 0, 0, 1000, size=(-1, ht), 
			style=wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS | wx.SL_INVERSE)
		self.Bind(wx.EVT_SCROLL, self.onLayerScroll, self.slLayers)
		if self.gObj is None:
			self.slLayers.Enable(False)
			
		self.lcGCode = GcodeListCtrl(self, self.gcode, self.images)
		self.lcGCode.setLineNumbers(self.settings.uselinenbrs)
		self.currentLayer = 0
		self.setLayerText()
		if self.gObj is not None:
			self.lcGCode.setLayerBounds(self.gObj.getGCodeLines(0))
			
		self.bShift = wx.BitmapButton(self, wx.ID_ANY, self.images.pngShift, size=BUTTONDIM)
		self.bShift.SetToolTipString("Move model in x/y direction")
		self.Bind(wx.EVT_BUTTON, self.doShiftModel, self.bShift)
		self.bShift.Enable(False)

		self.bModTemp = wx.BitmapButton(self, wx.ID_ANY, self.images.pngModtemp, size=BUTTONDIM)
		self.bModTemp.SetToolTipString("Modify Temperatures")
		self.Bind(wx.EVT_BUTTON, self.onModTemps, self.bModTemp)
		self.bModTemp.Enable(False)
				
		self.bModSpeed = wx.BitmapButton(self, wx.ID_ANY, self.images.pngModspeed, size=BUTTONDIM)
		self.bModSpeed.SetToolTipString("Modify Speed")
		self.Bind(wx.EVT_BUTTON, self.onModSpeed, self.bModSpeed)
		self.bModSpeed.Enable(False)
		
		self.bFilChange = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFilchange, size=BUTTONDIM)
		self.bFilChange.SetToolTipString("Insert G Code to assist with changing filament")
		self.Bind(wx.EVT_BUTTON, self.onFilChange, self.bFilChange)
		self.bFilChange.Enable(False)
		
		self.bEdit = wx.BitmapButton(self, wx.ID_ANY, self.images.pngEdit, size=BUTTONDIM)
		self.bEdit.SetToolTipString("Free edit G Code")
		self.Bind(wx.EVT_BUTTON, self.onEditGCode, self.bEdit)
		self.bEdit.Enable(False)
		
		self.bUp = wx.BitmapButton(self, wx.ID_ANY, self.images.pngUp, size=BUTTONDIM)
		self.bUp.SetToolTipString("Move up one layer")
		self.Bind(wx.EVT_BUTTON, self.onUp, self.bUp)
		self.bUp.Enable(False)
		
		self.bDown = wx.BitmapButton(self, wx.ID_ANY, self.images.pngDown, size=BUTTONDIM)
		self.bDown.SetToolTipString("Move down one layer")
		self.Bind(wx.EVT_BUTTON, self.onDown, self.bDown)
		self.bDown.Enable(False)
		
		self.bInfo = wx.BitmapButton(self, wx.ID_ANY, self.images.pngInfo, size=BUTTONDIM)
		self.bInfo.SetToolTipString("Information")
		self.Bind(wx.EVT_BUTTON, self.onInfo, self.bInfo)
		self.bInfo.Enable(False)
		
		self.bSaveLayers = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSavelayers, size=BUTTONDIM)
		self.bSaveLayers.SetToolTipString("Save specific layers to a file")
		self.Bind(wx.EVT_BUTTON, self.onSaveLayers, self.bSaveLayers)
		self.bSaveLayers.Enable(False)

		self.bOpen = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFileopen, size=BUTTONDIM)
		self.bOpen.SetToolTipString("Open a G Code file")
		self.Bind(wx.EVT_BUTTON, self.onOpen, self.bOpen)
		
		self.bImport = wx.BitmapButton(self, wx.ID_ANY, self.images.pngImport, size=BUTTONDIM)
		self.bImport.SetToolTipString("Import the current toolbox G Code file")
		self.Bind(wx.EVT_BUTTON, self.onImport, self.bImport)
		self.bImport.Enable(False)
		
		self.bExport = wx.BitmapButton(self, wx.ID_ANY, self.images.pngExport, size=BUTTONDIM)
		self.bExport.SetToolTipString("Export the current toolbox G Code file")
		self.Bind(wx.EVT_BUTTON, self.onExport, self.bExport)
		self.bExport.Enable(False)
		
		self.bEnqueue = wx.BitmapButton(self, wx.ID_ANY, self.images.pngAddqueue, size=BUTTONDIM)
		self.bEnqueue.SetToolTipString("Enqueue the current G Code file on the end of the G Code queue")
		self.Bind(wx.EVT_BUTTON, self.onEnqueue, self.bEnqueue)
		self.bEnqueue.Enable(False)
		
		self.bSave = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFilesave, size=BUTTONDIM)
		self.bSave.SetToolTipString("Save G Code to the current file")
		self.Bind(wx.EVT_BUTTON, self.onSave, self.bSave)
		self.bSave.Enable(False)
		
		self.bSaveAs = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFilesaveas, size=BUTTONDIM)
		self.bSaveAs.SetToolTipString("Save G Code to a different file")
		self.Bind(wx.EVT_BUTTON, self.onSaveAs, self.bSaveAs)
		self.bSaveAs.Enable(False)
		
		self.cbShowMoves = wx.CheckBox(self, wx.ID_ANY, "Show Moves")
		self.cbShowMoves.SetToolTipString("Show/Hide non-extrusion moves")
		self.cbShowMoves.SetValue(self.settings.showmoves)
		self.Bind(wx.EVT_CHECKBOX, self.onCbShowMoves, self.cbShowMoves)

		self.cbShowPrevious = wx.CheckBox(self, wx.ID_ANY, "Show Previous Layer")
		self.cbShowPrevious.SetToolTipString("Show/Hide the previous layer")
		self.cbShowPrevious.SetValue(self.settings.showprevious)
		self.Bind(wx.EVT_CHECKBOX, self.onCbShowPrevious, self.cbShowPrevious)

		self.cbLineNbrs = wx.CheckBox(self, wx.ID_ANY, "Line Numbers")
		self.cbLineNbrs.SetToolTipString("Use G Code line numbers")
		self.cbLineNbrs.SetValue(self.settings.uselinenbrs)
		self.Bind(wx.EVT_CHECKBOX, self.onCbLineNbrs, self.cbLineNbrs)
		
		self.bBracketStart = wx.BitmapButton(self, wx.ID_ANY, self.images.pngBracketopen, size=BUTTONDIM)
		self.bBracketStart.SetToolTipString("Mark the beginning of a block of G code")
		self.Bind(wx.EVT_BUTTON, self.onBracketStart, self.bBracketStart)
		self.bBracketStart.Enable(False)
		
		self.bBracketEnd = wx.BitmapButton(self, wx.ID_ANY, self.images.pngBracketclose, size=BUTTONDIM)
		self.bBracketEnd.SetToolTipString("Mark the end of a block of G code")
		self.Bind(wx.EVT_BUTTON, self.onBracketEnd, self.bBracketEnd)
		self.bBracketEnd.Enable(False)
		
		self.bBracketDel = wx.BitmapButton(self, wx.ID_ANY, self.images.pngBracketdel, size=BUTTONDIM)
		self.bBracketDel.SetToolTipString("Delete the marked block of G code")
		self.Bind(wx.EVT_BUTTON, self.onBracketDel, self.bBracketDel)
		self.bBracketDel.Enable(False)
		
			
		btnszr = wx.BoxSizer(wx.HORIZONTAL)
		btnszr.AddSpacer((20, 20))
		btnszr.Add(self.bShift)
		btnszr.AddSpacer((10, 10))
		btnszr.Add(self.bModTemp)
		btnszr.AddSpacer((10, 10))
		btnszr.Add(self.bModSpeed)
		btnszr.AddSpacer((10, 10))
		btnszr.Add(self.bFilChange)
		btnszr.AddSpacer((10, 10))
		btnszr.Add(self.bEdit)
		btnszr.AddSpacer((10, 10))
		btnszr.Add(self.bInfo)
		btnszr.AddSpacer((70, 10))
		
		optszr = wx.BoxSizer(wx.VERTICAL)
		optszr.AddSpacer((5,5))
		optszr.Add(self.cbShowMoves)
		optszr.AddSpacer((5,5))
		optszr.Add(self.cbShowPrevious)
		btnszr.Add(optszr)
		btnszr.AddSpacer((70, 10))
		btnszr.Add(self.bSaveLayers)
		btnszr.AddSpacer((95, 10))
		btnszr.Add(self.bOpen)
		btnszr.AddSpacer((10, 10))
		btnszr.Add(self.bImport)
		btnszr.AddSpacer((10, 10))
		btnszr.Add(self.bExport)
		btnszr.AddSpacer((10, 10))
		btnszr.Add(self.bEnqueue)
		btnszr.AddSpacer((10, 10))
		btnszr.Add(self.bSave)
		btnszr.AddSpacer((10, 10))
		btnszr.Add(self.bSaveAs)
		btnszr.AddSpacer((10, 10))

		hszr = wx.BoxSizer(wx.HORIZONTAL)
		hszr.AddSpacer((20,20))
		
		vszr = wx.BoxSizer(wx.VERTICAL)
		vszr.Add(self.gcFrame)
		vszr.Add(self.stLayerText, 1, wx.ALIGN_CENTER_HORIZONTAL, 1)
		hszr.Add(vszr)

		szNav = wx.BoxSizer(wx.VERTICAL)
		szNav.Add(self.bUp, 1, wx.ALIGN_CENTER_HORIZONTAL, 1)
		szNav.AddSpacer((10, 10))
		szNav.Add(self.slLayers)
		szNav.AddSpacer((10, 10))
		szNav.Add(self.bDown, 1, wx.ALIGN_CENTER_HORIZONTAL, 1)

		hszr.Add(szNav)
		hszr.AddSpacer((20,20))
		
		listszr = wx.BoxSizer(wx.VERTICAL)
		listszr.Add(self.lcGCode)
		listszr.AddSpacer((10,10))
		listszr.Add(self.cbLineNbrs, 1, wx.ALIGN_CENTER_HORIZONTAL, 1)
		
		brksz = wx.BoxSizer(wx.HORIZONTAL)
		brksz.Add(self.bBracketStart)
		brksz.AddSpacer((20, 20))
		brksz.Add(self.bBracketDel)
		brksz.AddSpacer((20, 20))
		brksz.Add(self.bBracketEnd)
		listszr.AddSpacer((10,10))
		listszr.Add(brksz, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		
		hszr.Add(listszr)
		hszr.AddSpacer((20,20))
		
		vszr = wx.BoxSizer(wx.VERTICAL)
		vszr.AddSpacer((20, 20))
		vszr.Add(btnszr)
		vszr.AddSpacer((10, 10))
		vszr.Add(hszr)
		vszr.AddSpacer((20, 20))
		
		
		self.SetSizer(vszr)
		self.Layout()
		self.Fit()
		
		self.slLayers.SetRange(0, lmax)
		self.slLayers.SetPageSize(int(lmax/10))
		
		if self.gObj is not None:
			self.enableButtons()
			
	def setImportFile(self, fn):
		self.importFileName = fn
		if fn is None:
			self.bImport.SetToolTipString("")
			self.bImport.Enable(False)
		else:
			self.bImport.SetToolTipString("Import G Code file (%s)" % fn)
			self.bImport.Enable(True)
			
	def onBracketStart(self, evt):
		b = self.lcGCode.setBracketStart()
		self.gcFrame.setBracket(b)
		self.enableBracketDel(b)

	def onBracketEnd(self, evt):
		b = self.lcGCode.setBracketEnd()
		self.gcFrame.setBracket(b)
		self.enableBracketDel(b)

	def enableBracketDel(self, b=None):
		if b is None:
			b = self.lcGCode.getBracket()
			
		if b[0] is None or b[1] is None:
			self.bBracketDel.Enable(False)
		else:
			self.bBracketDel.Enable(True)
		
	def onBracketDel(self, evt):
		b = self.lcGCode.getBracket()
		if b[0] is None or b[1] is None:
			return
		
		self.gcode = self.gcode[:b[0]] + self.gcode[b[1]+1:]
		self.setModified(True)
		self.gObj = self.buildModel()
		self.modGcSuffixTemps(self.gObj.getTemps())
		l = self.gcFrame.getCurrentLayer()
		self.gcFrame.loadModel(self.gObj, l, self.gcFrame.getZoom())
		lmax = self.gObj.layerCount()-1
		self.slLayers.SetRange(0, lmax)
		self.slLayers.SetPageSize(int(lmax/10))
		self.lcGCode.setGCode(self.gcode)
		self.lcGCode.setLayerBounds(self.gObj.getGCodeLines(l))
		self.bBracketDel.Enable(False)
		self.updateInfoDlg(self.currentLayer)
	
	def updateTitle(self):
		if self.filename is None:
			self.SetTitle("%s" % TITLE_PREFIX)
		else:
			txt = TITLE_PREFIX + " - "
			if self.modified:
				txt += "* "
			txt += self.filename
			self.SetTitle(txt)

			
	def setModified(self, flag=True):
		self.modified = flag
		self.updateTitle()
		
	def onExport(self, evt):
		if self.modified:
			dlg = wx.MessageDialog(self,
				"You have unsaved changes.\nAre you sure you want to export?",
				"Confirm Export With Pending Changes",
				wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			rc = dlg.ShowModal()
			dlg.Destroy()
			if rc != wx.ID_YES:
				return
		
		self.parent.exportGcFile(self.filename)
		
	def onEnqueue(self, evt):
		if self.modified:
			dlg = wx.MessageDialog(self,
				"You have unsaved changes.\nAre you sure you want to enqueue?",
				"Confirm Enqueue With Pending Changes",
				wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			rc = dlg.ShowModal()
			dlg.Destroy()
			if rc != wx.ID_YES:
				return
		
		self.parent.exportGcFile(self.filename, True)
		
	def onImport(self, evt):
		fn = self.parent.importGcFile()
		if fn is None:
			return
		
		self.loadGFile(fn)
		
	def onOpen(self, evt):
		if self.modified:
			dlg = wx.MessageDialog(self,
				"You have unsaved changes.\nAre you sure you want to open a different file?",
				"Confirm Open With Pending Changes",
				wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			rc = dlg.ShowModal()
			dlg.Destroy()
			if rc != wx.ID_YES:
				return

		self.gcodeFileDialog()
		
	def onInfo(self, evt):
		if self.propDlg is not None:
			return
		
		self.propDlg = PropertiesDlg(self, self, None, cb=self.onInfoClose)
		
		self.showFileProperties()
		self.showLayerProperties(self.currentLayer)
		self.propDlg.Show()
		
	def onInfoClose(self):
		self.propDlg = None
		
	def updateInfoDlg(self, lx):
		if self.propDlg is None:
			return
		
		self.showFileProperties()
		self.showLayerProperties(lx)
		
	def showFileProperties(self):
		slCfg, filSiz, tempsHE, tempsBed = parseGCSuffix(self.gcode)
		ftime = time.strftime('%y/%m/%d-%H:%M:%S', time.localtime(os.path.getmtime(self.filename)))
		if len(self.filename) > 50:
			self.propDlg.setProperty(PropertyEnum.fileName, os.path.basename(self.filename))
		else:
			self.propDlg.setProperty(PropertyEnum.fileName, self.filename)
		self.propDlg.setProperty(PropertyEnum.slicerCfg, slCfg)
		self.propDlg.setProperty(PropertyEnum.filamentSize, filSiz)
		self.propDlg.setProperty(PropertyEnum.temperatures, "HE:%s  BED:%s" % (tempsHE, tempsBed))
		self.propDlg.setProperty(PropertyEnum.sliceTime, ftime)
		self.propDlg.setProperty(PropertyEnum.printEstimate, self.totalTimeStr)
		
	def showLayerProperties(self, lx):
		if self.propDlg is None:
			return
		
		self.propDlg.setProperty(PropertyEnum.layerNum, "%d" % lx)
		x0, y0, xn, yn = self.gObj.getLayerMinMaxXY(lx)
		if x0 is None:
			self.propDlg.setProperty(PropertyEnum.minMaxXY, "")
		else:
			self.propDlg.setProperty(PropertyEnum.minMaxXY, "(%.2f, %.2f) - (%.2f, %.2f)" % (x0, y0, xn, yn))
		
		le, prior, after = self.gObj.getLayerFilament(lx)
		eUsed = self.gObj.getFilament()
		s = []
		for i in range(self.settings.nextruders):
			s.append("%.2f/%.2f    <: %.2f    >: %.2f" % (le[i], eUsed[i], prior[i], after[i]))
		self.propDlg.setProperty(PropertyEnum.filamentUsed, s)

		f, l = self.gObj.getGCodeLines(lx)
		if f is None:
			self.propDlg.setProperty(PropertyEnum.gCodeRange, "")
		else:
			self.propDlg.setProperty(PropertyEnum.gCodeRange, "%d - %d" % (f, l))
		
		self.propDlg.setProperty(PropertyEnum.layerPrintTime, self.layerTimeStr[lx])
		if lx == 0:
			self.propDlg.setProperty(PropertyEnum.timeUntil, "")
		else:
			t = sum(self.layerTimes[:lx])
			self.propDlg.setProperty(PropertyEnum.timeUntil, formatElapsed(t))
		
	def gcodeFileDialog(self):
		wildcard = "GCode (*.gcode)|*.gcode|"	 \
			"All files (*.*)|*.*"
			
		dlg = wx.FileDialog(
			self, message="Choose a GCode file",
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
		
		self.loadGFile(path)
		
	def loadGFile(self, path):
		self.settings.lastdirectory = os.path.dirname(path)
		
		self.gObj = self.loadGCode(path)
		if self.gObj is None:
			lmax = 1
			self.slLayers.Enable(False)
			self.bUp.Enable(False)
			self.bDown.Enable(False)
			self.filename = None
		else:
			lmax = self.gObj.layerCount()-1
			self.slLayers.Enable(True)
			self.bUp.Enable(True)
			self.bDown.Enable(True)
			self.filename = path
			
		self.updateTitle()
			
		self.slLayers.SetRange(0, lmax)
		self.slLayers.SetPageSize(int(lmax/10))
		
		self.gcFrame.loadModel(self.gObj)
		self.lcGCode.setGCode(self.gcode)
		self.currentLayer = 0
		self.setLayerText()
		self.slLayers.SetValue(0)
		self.updateInfoDlg(0)

		self.setModified(False)
		if self.gObj is not None:
			self.lcGCode.setLayerBounds(self.gObj.getGCodeLines(0))
			self.enableButtons()
		else:
			self.enableButtons(False)
			
	def enableButtons(self, flag=True, openButtons=False):
		self.bShift.Enable(flag)
		self.bModTemp.Enable(flag)
		self.bModSpeed.Enable(flag)
		self.bEdit.Enable(flag)
		self.bInfo.Enable(flag)
		self.bUp.Enable(flag)
		self.bDown.Enable(flag)
		self.bSaveLayers.Enable(flag)
		self.bSave.Enable(flag)
		self.bSaveAs.Enable(flag)
		self.bExport.Enable(flag)
		self.bEnqueue.Enable(flag)
		self.bFilChange.Enable(flag)
		self.bBracketStart.Enable(flag)
		self.bBracketEnd.Enable(flag)
		self.enableBracketDel()
		if openButtons:
			if flag and self.importFileName is not None:
				self.bImport.Enable(True)
			else:
				self.bImport.Enable(False)
			self.bOpen.Enable(flag)
			
	def doShiftModel(self, evt):
		dlg = ShiftModelDlg(self, self.gObj, self.settings.buildarea)
		dlg.CenterOnScreen()
		rc = dlg.ShowModal()
		dlg.Destroy()
		if rc == wx.ID_OK:
			self.applyShift()
			self.setModified()
		else:
			self.setShift(0, 0)
		
	def setShift(self, sx, sy):
		self.shiftX = sx
		self.shiftY = sy
		self.gcFrame.setShift(sx, sy)

	def applyShift(self):
		self.gcode = [self.applyAxisShift(self.applyAxisShift(l, 'y', self.shiftY), 'x', self.shiftX) for l in self.gcode]

		self.shiftX = 0
		self.shiftY = 0
		self.gObj = self.buildModel()
		self.gcFrame.loadModel(self.gObj, self.gcFrame.getCurrentLayer(), self.gcFrame.getZoom())
		self.lcGCode.setGCode(self.gcode)
		self.lcGCode.refreshList()
		self.updateInfoDlg(self.currentLayer)

	def applyAxisShift(self, s, axis, shift):
		if "m117" in s or "M117" in s:
			return s

		if axis == 'x':
			m = reX.match(s)
			maxv = self.settings.buildarea[0]
		elif axis == 'y':
			m = reY.match(s)
			maxv = self.settings.buildarea[1]
		elif axis == 'z':
			m = reZ.match(s)
			maxv = self.settings.buildarea[1]
		else:
			return s
		
		if m is None or m.lastindex != 3:
			return s
		
		value = float(m.group(2)) + float(shift)
		if value < 0:
			value = 0.0
		elif value > maxv:
			value = float(maxv)
			
		return "%s%s%s" % (m.group(1), str(value), m.group(3))
	
	def onModTemps(self, evt):
		dlg = ModifyTempsDlg(self, self.gObj, self.settings.platemps, self.settings.abstemps)
		dlg.CenterOnScreen()
		rc = dlg.ShowModal()
		if rc == wx.ID_OK:
			bed, hes = dlg.getResult()
			
		dlg.Destroy()
		if rc != wx.ID_OK:
			return
		
		self.applyTempChange(bed, hes)

	def applyTempChange(self, bed, hes):
		self.currentTool = 0
		self.gcode = [self.applySingleTempChange(l, bed, hes) for l in self.gcode]

		self.setModified(True)
		self.gObj = self.buildModel()
		self.modGcSuffixTemps(self.gObj.getTemps())
		self.gcFrame.loadModel(self.gObj, self.gcFrame.getCurrentLayer(), self.gcFrame.getZoom())
		self.lcGCode.setGCode(self.gcode)
		self.lcGCode.refreshList()
		self.updateInfoDlg(self.currentLayer)
		
	def modGcSuffixTemps(self, nTemps):
		bstr = "%.1f" % nTemps[0]
		
		h = []
		nct = 0
		for x in nTemps[1]:
			if x is None:
				nct += 1
			else:
				if nct != 0:
					h.extend([None]*nct)
					nct = 0
				h.append("%.1f" % x)
		hestr = ",".join(h)
		
		modifyGCSuffix(self.gcode, None, None, hestr, bstr)
		
	def applySingleTempChange(self, s, bed, hes):
		if "m104" in s.lower() or "m109" in s.lower():
			m = reS.match(s)
			difference = hes[self.currentTool]
		elif "m140" in s.lower() or "m190" in s.lower():
			m = reS.match(s)
			difference = bed
		elif s.startswith("T"):
			try:
				t = int(s[1:])
			except:
				t = None

			if t is not None:
				self.currentTool = t
			return s
		else:
			return s

		if m is None or m.lastindex != 3:
			return s

		value = float(m.group(2))
		if value == 0.0:
			return s

		value += float(difference)
		return "%s%s%s" % (m.group(1), str(value), m.group(3))
	
	def onModSpeed(self, evt):
		dlg = ModifySpeedDlg(self)
		dlg.CenterOnScreen()
		val = dlg.ShowModal()

		if val == wx.ID_OK:
			modSpeeds = dlg.getResult()
			
		dlg.Destroy()
		if val != wx.ID_OK:
			return
		
		self.applySpeedChange([float(x)/100.0 for x in modSpeeds])

	def applySpeedChange(self, speeds):
		self.gcode = [self.applySingleSpeedChange(l, speeds) for l in self.gcode]

		self.setModified(True)
		self.gObj = self.buildModel()
		self.gcFrame.loadModel(self.gObj, self.gcFrame.getCurrentLayer(), self.gcFrame.getZoom())
		self.lcGCode.setGCode(self.gcode)
		self.lcGCode.refreshList()
		self.updateInfoDlg(self.currentLayer)

	def applySingleSpeedChange(self, s, speeds):
		if "m117" in s or "M117" in s:
			return s

		m = reF.match(s)
		if m is None or m.lastindex != 3:
			return s

		e = reE.match(s)
		if e is None: #no extrusion - must  be a move
			factor = speeds[1]
		else:
			factor = speeds[0]

		value = float(m.group(2)) * float(factor)
		return "%s%s%s" % (m.group(1), str(value), m.group(3))
	
	def onFilChange(self, evt):
		insertPoint = self.lcGCode.getSelectedLine()
		dlg = FilamentChangeDlg(self, self.gcode, self.gObj,
				insertPoint,
				self.gObj[self.currentLayer].printHeight())
		rc = dlg.ShowModal()
		if rc == wx.ID_OK:
			ngc = dlg.getValues()
			
		dlg.Destroy()
		if rc != wx.ID_OK:
			return
		
		if insertPoint == 0:
			self.gcode = ngc + self.gcode
		else:
			self.gcode = self.gcode[:insertPoint] + ngc + self.gcode[insertPoint:]
		
		self.setModified(True)
		self.enableButtons()
		self.gObj = self.buildModel()
		self.gcFrame.loadModel(self.gObj, self.currentLayer, None)
		self.lcGCode.setGCode(self.gcode)
		self.lcGCode.setLayerBounds(self.gObj.getGCodeLines(self.currentLayer))
		self.updateInfoDlg(self.currentLayer)
	
	def onEditGCode(self, evt):
		self.editDlg = EditGCodeDlg(self, self.gcode, "<live buffer>", self.editClosed)
		self.editDlg.CenterOnScreen()
		self.editDlg.Show()
		self.enableButtons(flag=False, openButtons=True)
		
	def editClosed(self, rc):
		self.enableButtons(flag=True, openButtons=True)
		if rc == wx.ID_OK:
			data = self.editDlg.getData()
			
		self.editDlg.Destroy()
		if rc != wx.ID_OK:
			return

		self.gcode = data[:]
		self.setModified(True)
		self.gObj = self.buildModel()
		self.modGcSuffixTemps(self.gObj.getTemps())
		self.gcFrame.loadModel(self.gObj, 0, 1)
		self.currentLayer = 0
		self.setLayerText()
		self.slLayers.SetValue(0)
		self.lcGCode.setGCode(self.gcode)
		self.lcGCode.setLayerBounds(self.gObj.getGCodeLines(0))
		self.lcGCode.refreshList()
		self.updateInfoDlg(0)
			
	def onCbShowMoves(self, evt):
		self.settings.showmoves = self.cbShowMoves.GetValue()
		self.gcFrame.setShowMoves(self.settings.showmoves)
	
	def onCbShowPrevious(self, evt):
		self.settings.showprevious = self.cbShowPrevious.GetValue()
		self.gcFrame.setShowPrevious(self.settings.showprevious)
		
	def onCbLineNbrs(self, evt):
		self.settings.uselinenbrs = self.cbLineNbrs.GetValue()
		self.lcGCode.setLineNumbers(self.settings.uselinenbrs)
		
	def onLayerScroll(self, evt):
		v = self.slLayers.GetValue()
		if v == self.currentLayer:
			return
		
		self.changeLayer(v)
		
	def onUp(self, evt):
		lmax = self.slLayers.GetRange()[1]
		if self.currentLayer >= lmax:
			return
		
		v = self.currentLayer + 1
		self.changeLayer(v)
	
	def onDown(self, evt):
		if self.currentLayer <= 0:
			return
		
		v = self.currentLayer - 1
		self.changeLayer(v)
		
	def changeLayer(self, v):
		self.currentLayer = v
		self.gcFrame.setLayer(v)
		self.slLayers.SetValue(v)
		self.setLayerText()
		self.lcGCode.setLayerBounds(self.gObj.getGCodeLines(v))
		self.showLayerProperties(v)
		
	def setLayerText(self):
		if self.gObj is None:
			ht = 0.0
		else:
			ht = self.gObj[self.currentLayer].printHeight()
		self.stLayerText.SetLabel("Layer Height: %0.3f" % ht)
		
	def reportSelectedLine(self, ln):
		self.gcFrame.reportSelectedLine(ln)
					
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
				self.parent.GEditClosed()
		else:
			self.parent.GEditClosed()
		
	def loadGCode(self, fn):
		if fn is None:
			self.gcode = []
			return None
		
		try:
			self.gcode = list(open(fn))
		except:
			print "Error opening file %s" % fn
			return None
		
		return self.buildModel()
		
	def buildModel(self):
		rgcode = [s.rstrip() for s in self.gcode]
		
		cnc = CNC(self.settings.acceleration)
		
		ln = -1
		for gl in rgcode:
			ln += 1
			if ";" in gl:
				gl = gl.split(";")[0]
			if gl.strip() == "":
				continue
			
			p = re.split("\\s+", gl, 1)
			
			params = {}
			if not (p[0].strip() in ["M117", "m117"]):
				if len(p) >= 2:
					self.paramStr = p[1]
					
					if "X" in self.paramStr:
						params["X"] = self._get_float("X")
						
					if "Y" in self.paramStr:
						params["Y"] = self._get_float("Y")
			
					if "Z" in self.paramStr:
						params["Z"] = self._get_float("Z")
			
					if "E" in self.paramStr:
						params["E"] = self._get_float("E")
			
					if "F" in self.paramStr:
						params["F"] = self._get_float("F")
			
					if "S" in self.paramStr:
						params["S"] = self._get_float("S")
			
			cnc.execute(p[0], params, ln)
			
		gobj = cnc.getGObject()
		gobj.setMaxLine(ln)
		self.totalTime, self.layerTimes = cnc.getTimes()

		self.totalTimeStr = formatElapsed(self.totalTime)
		self.layerTimeStr = [formatElapsed(s) for s in self.layerTimes]

		return gobj
				
	def _get_float(self,which):
		try:
			return float(gcRegex.findall(self.paramStr.split(which)[1])[0])
		except:
			print "exception: ", self.paramStr
	
	def onSaveAs(self, evt):
		wildcard = "GCode (*.gcode)|*.gcode"

		dlg = wx.FileDialog(
			self, message="Save as ...", defaultDir=self.settings.lastdirectory, 
			defaultFile="", wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		
		val = dlg.ShowModal()

		if val != wx.ID_OK:
			dlg.Destroy()
			return
		
		path = dlg.GetPath()
		dlg.Destroy()

		ext = os.path.splitext(os.path.basename(path))[1]
		if ext == "":
			path += ".gcode"
			
		self.saveFile(path)
		
	def onSave(self, evt):
		if self.filename is None:
			self.onSaveAs(evt)
		else:
			self.saveFile(self.filename)
		
	def saveFile(self, path):			
		fp = file(path, 'w')
		
		for ln in self.gcode:
			fp.write("%s\n" % ln.rstrip())
			
		self.setModified(False)
			
		fp.close()
		
		self.filename = path
		if self.settings.autoexport:
			self.parent.exportGcFile(path)
		self.updateTitle()
		
		dlg = wx.MessageDialog(self, "G Code file\n" + path + "\nwritten.",
			'Save Successful', wx.OK | wx.ICON_INFORMATION)
		dlg.ShowModal()
		dlg.Destroy()
		
	def onSaveLayers(self, evt):
		dlg = SaveLayerDlg(self, self.gObj)
		rc = dlg.ShowModal()
		if rc == wx.ID_OK:
			sx, ex, ereset, zmodify, zdelta = dlg.getValues()
			
		dlg.Destroy()
		if rc != wx.ID_OK:
			return
		
		startLine = self.gObj.getGCodeLines(sx)[0]
		endLine = self.gObj.getGCodeLines(ex)[1]
		
		wildcard = "GCode (*.gcode)|*.gcode"

		dlg = wx.FileDialog(
			self, message="Save as ...", defaultDir=self.settings.lastdirectory, 
			defaultFile="", wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		
		val = dlg.ShowModal()

		if val != wx.ID_OK:
			dlg.Destroy()
			return
		
		path = dlg.GetPath()
		dlg.Destroy()

		ext = os.path.splitext(os.path.basename(path))[1]
		if ext == "":
			path += ".gcode"
			
		fp = file(path, 'w')
		
		if ereset:
			fp.write("G92 E%0.5f\n" % self.gObj[sx].startingE())
			
		if zmodify:
			fp.write("\n".join([self.applyAxisShift(ln, 'z', zdelta).rstrip() for ln in self.gcode[startLine:endLine+1]]))
		else:
			fp.write("\n".join([ln.rstrip() for ln in self.gcode[startLine:endLine+1]]))
			
		fp.close()
		
		dlg = wx.MessageDialog(self, "G Code file\n" + path + "\nwritten.",
			'Save Layers Successful', wx.OK | wx.ICON_INFORMATION)
		dlg.ShowModal()
		dlg.Destroy()
		
	def applyZMod(self, ln, modflag):
		if not modflag:
			return ln
		
		return ln
