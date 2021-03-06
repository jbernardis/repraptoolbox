'''
Created on Oct 28, 2016

@author: Jeff
'''
import os, inspect

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))

import wx.lib.newevent
import re
import shlex
import subprocess
import thread
import time
import tempfile

from settings import Settings
from images import Images
from override import Slic3rOverRideDlg, loadOverrides
from gcsuffix import buildGCSuffix
from History.history import SliceComplete

(SlicerEvent, EVT_SLIC3R_UPDATE) = wx.lib.newevent.NewEvent()
SLIC3R_MESSAGE = 1
SLIC3R_FINISHED = 2
SLIC3R_CANCELLED = 3

FILAMENT_BASE = 1000
BUTTONDIM = (48, 48)

filamentMergeKeys = ['extrusion_multiplier', 'filament_diameter', 'first_layer_temperature', 'temperature']

multiOverrides = {"printspeed": ["infill_speed", "solid_infill_speed", "perimeter_speed"]}

def loadProfiles(fnames, mergeKeys, log):
	kdict = {}

	for fn in fnames:	
		try:
			l = list(open(fn))
		except:
			log("Unable to open Slic3r settings file: %s" % fn)
			return kdict
		
		for ln in l:
			if ln.startswith('#'):
				continue
			
			lw = ln.split('=')
			if len(lw) != 2:
				continue
			
			dkey = lw[0].strip()
			dval = lw[1].strip()
			if dkey in kdict.keys():
				if dkey in mergeKeys:
					kdict[dkey] += ',' + dval
			else:
				kdict[dkey] = dval
				
	return kdict

class SlicerThread:
	def __init__(self, win, executable, stlFile, gcFile, cfgFile):
		self.win = win
		self.executable = executable
		self.stlFile = stlFile
		self.gcFile = gcFile
		self.cfgFile= cfgFile
		self.running = False
		self.cancelled = False

	def Start(self):
		self.running = True
		self.cancelled = False
		thread.start_new_thread(self.Run, ())

	def Stop(self):
		self.cancelled = True

	def IsRunning(self):
		return self.running

	def Run(self):
		args = [self.executable, "--load", self.cfgFile, self.stlFile, "-o", self.gcFile]
		try:
			p = subprocess.Popen(args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
		except:
			evt = SlicerEvent(msg = "Exception occurred trying to spawn slic3r", state = SLIC3R_CANCELLED)
			wx.PostEvent(self.win, evt)
			return
		
		obuf = ''
		while not self.cancelled:
			o = p.stdout.read(1)
			if o == '': break
			if o == '\r' or o == '\n':
				if len(obuf.strip()) > 0:
					state = SLIC3R_MESSAGE
					evt = SlicerEvent(msg = obuf, state = state)
					wx.PostEvent(self.win, evt)
				obuf = ''
			elif ord(o) < 32:
				pass
			else:
				obuf += o
				
		if self.cancelled:
			evt = SlicerEvent(msg = None, state = SLIC3R_CANCELLED)
			p.kill()
		else:
			evt = SlicerEvent(msg = None, state = SLIC3R_FINISHED)
			
		p.wait()
		wx.PostEvent(self.win, evt)

		self.running = False

class Slic3rDlg(wx.Frame):
	def __init__(self, parent):
		wx.Frame.__init__(self, None, wx.ID_ANY, 'Slic3r', size=(100, 100))
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.parent = parent
		self.log = self.parent.log
		self.history = parent.history
		self.settings = Settings(cmdFolder)
		self.images = Images(os.path.join(cmdFolder, "images"))
		
		self.stlFn = None
		self.gcDir = self.settings.lastgcodedirectory
		self.gcFn = None
		
		self.slicing = False
		self.sliceComplete = False
		self.ovrDlg = None
		self.overRideValues = loadOverrides(cmdFolder)
		
		self.Bind(EVT_SLIC3R_UPDATE, self.slic3rUpdate)
		self.Show()
		ico = wx.Icon(os.path.join(cmdFolder, "images", "slic3r.png"), wx.BITMAP_TYPE_PNG)
		self.SetIcon(ico)
		
		self.tcStl = wx.TextCtrl(self, wx.ID_ANY, "", size=(450, -1), style=wx.TE_READONLY)
		
		self.bOpen = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFileopen, size=BUTTONDIM)
		self.bOpen.SetToolTip("Select an STL file for slicing")
		self.Bind(wx.EVT_BUTTON, self.onBOpen, self.bOpen)
		
		self.bImport = wx.BitmapButton(self, wx.ID_ANY, self.images.pngImport, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onBImport, self.bImport)
		
		self.bImportQ = wx.BitmapButton(self, wx.ID_ANY, self.images.pngNext, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onBImportFromQueue, self.bImportQ)
		
		self.cbGcDir = wx.CheckBox(self, wx.ID_ANY, "Use STL directory for G Code file")
		self.cbGcDir.SetToolTip("Use the directory from the STL file for the resulting G Code file")
		self.cbGcDir.SetValue(self.settings.usestldir)
		self.Bind(wx.EVT_CHECKBOX, self.onCbGcDir, self.cbGcDir)

		self.tcGcDir = wx.TextCtrl(self, wx.ID_ANY, "", size=(330, -1), style=wx.TE_READONLY)
		self.bGcDir = wx.Button(self, wx.ID_ANY, "...", size=(30, 22))
		self.bGcDir.Enable(not self.settings.usestldir)
		self.bGcDir.SetToolTip("Choose G Code directory")
		self.Bind(wx.EVT_BUTTON, self.onBGcDir, self.bGcDir)
		
		self.tcGc = wx.TextCtrl(self, wx.ID_ANY, "", size=(450, -1), style=wx.TE_READONLY)
		
		self.bExport = wx.BitmapButton(self, wx.ID_ANY, self.images.pngExport, size=BUTTONDIM)
		self.bExport.SetToolTip("Export G Code file to toolbox")
		self.Bind(wx.EVT_BUTTON, self.onBExport, self.bExport)
		
		self.cbAutoExport = wx.CheckBox(self, wx.ID_ANY, "Auto-export")
		self.cbAutoExport.SetToolTip("Automatically export the G code file when finished")
		self.Bind(wx.EVT_CHECKBOX, self.onAutoExport, self.cbAutoExport)
		self.cbAutoExport.SetValue(self.settings.autoexport)
		
		self.cbAutoEnqueue = wx.CheckBox(self, wx.ID_ANY, "Auto-enqueue")
		self.cbAutoEnqueue.SetToolTip("Automatically enqueue the G code file when exporting")
		self.Bind(wx.EVT_CHECKBOX, self.onAutoEnqueue, self.cbAutoEnqueue)
		self.cbAutoEnqueue.SetValue(self.settings.autoenqueue)
		
		self.loadConfigFiles()
		
		self.chPrint = wx.Choice(self, wx.ID_ANY, size = (225,-1), choices = self.choicesPrint)
		self.Bind(wx.EVT_CHOICE, self.onChoicePrint, self.chPrint)
		cxPrint = 0
		if self.settings.printchoice in self.choicesPrint:
			cxPrint = self.choicesPrint.index(self.settings.printchoice)
		self.chPrint.SetSelection(cxPrint)
		
		self.chPrinter = wx.Choice(self, wx.ID_ANY, size = (225, -1), choices = self.choicesPrinter)
		self.Bind(wx.EVT_CHOICE, self.onChoicePrinter, self.chPrinter)
		cxPrinter = 0
		if self.settings.printerchoice in self.choicesPrinter:
			cxPrinter = self.choicesPrinter.index(self.settings.printerchoice)
		self.chPrinter.SetSelection(cxPrinter)
		
		self.nExtruders = self.getExtruderCount(self.lCfgPrinter[self.choicesPrinter[cxPrinter]])

		self.chFilament = [None, None, None, None]
		cxFilament = [0, 0, 0, 0]
		for ex in range(len(self.chFilament)):
			self.chFilament[ex] = wx.Choice(self, FILAMENT_BASE + ex, size = (225, -1), choices = self.choicesFilament)
			self.Bind(wx.EVT_CHOICE, self.onChoiceFilament, self.chFilament[ex])
			if self.settings.filamentchoice[ex] in self.choicesFilament:
				cxFilament[ex] = self.choicesFilament.index(self.settings.filamentchoice[ex])
			self.chFilament[ex].SetSelection(cxFilament[ex])
			self.chFilament[ex].Enable(ex < self.nExtruders)
			
		self.updateFileDisplay()

		szStl = wx.BoxSizer(wx.VERTICAL)
		szStl.AddSpacer(5)
		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(10)
		hsz.Add(self.tcStl)
		hsz.AddSpacer(10)
		szStl.Add(hsz)
		szStl.AddSpacer(10)
		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(10)
		hsz.Add(self.bOpen)
		hsz.AddSpacer(5)
		hsz.Add(self.bImport)
		hsz.AddSpacer(5)
		hsz.Add(self.bImportQ)
		szStl.Add(hsz)

		szUseStl = wx.BoxSizer(wx.HORIZONTAL)
		szUseStl.AddSpacer(20)
		szUseStl.Add(self.cbGcDir)
		
		szGcDir = wx.BoxSizer(wx.HORIZONTAL)
		szGcDir.AddSpacer(10)
		szGcDir.Add(self.tcGcDir)
		szGcDir.AddSpacer(10)
		szGcDir.Add(self.bGcDir)
		szGcDir.AddSpacer(10)

		szGc = wx.BoxSizer(wx.VERTICAL)
		szGcH = wx.BoxSizer(wx.HORIZONTAL)
		szGcH.AddSpacer(10)
		szGcH.Add(self.tcGc, 1, wx.TOP, 8)
		szGcH.AddSpacer(10)
		szGcH.Add(self.bExport)
		szGcH.AddSpacer(10)
		szGc.Add(szGcH)
		
		szGcH = wx.BoxSizer(wx.HORIZONTAL)
		szGcH.AddSpacer(50)
		szGcH.Add(self.cbAutoExport)
		szGcH.AddSpacer(30)
		szGcH.Add(self.cbAutoEnqueue)
		szGcH.AddSpacer(10)
		szGc.Add(szGcH)

		szCfgL = wx.BoxSizer(wx.VERTICAL)
		szCfgR = wx.BoxSizer(wx.VERTICAL)
		
		szCfgL.Add(wx.StaticText(self, wx.ID_ANY, "Print:"))
		szCfgL.Add(self.chPrint)
		
		szCfgL.AddSpacer(20)
		szCfgL.Add(wx.StaticText(self, wx.ID_ANY, "Printer:"))
		szCfgL.Add(self.chPrinter)

		szCfgR.Add(wx.StaticText(self, wx.ID_ANY, "Filament:"))
		for ex in range(len(self.chFilament)):
			szCfgR.Add(self.chFilament[ex])
			
		szCfg = wx.BoxSizer(wx.HORIZONTAL)
		szCfg.Add(szCfgL)
		szCfg.AddSpacer(50)
		szCfg.Add(szCfgR)
		
		szOverRide = wx.BoxSizer(wx.HORIZONTAL)
		
		self.bOverRide = wx.BitmapButton(self, wx.ID_ANY, self.images.pngOverride, size=BUTTONDIM)
		self.bOverRide.SetToolTip("Modify slic3r over-rides")
		self.Bind(wx.EVT_BUTTON, self.doOverRide, self.bOverRide)
		szOverRide.Add(self.bOverRide, 0, wx.ALIGN_CENTER_VERTICAL, 1)
		szOverRide.AddSpacer(10)

		self.cbOverRide = wx.CheckBox(self, wx.ID_ANY, "Apply Over-Rides")
		self.cbOverRide.SetToolTip("Apply over ride values to the slice operation")
		self.cbOverRide.SetValue(False)
		szOverRide.Add(self.cbOverRide, 0, wx.ALIGN_CENTER_VERTICAL, 1)
		szOverRide.AddSpacer(10)
		
		self.tcOverRide = wx.TextCtrl(self, wx.ID_ANY, size=(300, 140), style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY)
		szOverRide.Add(self.tcOverRide)
		self.showOverRideValues()
		
		self.tcLog = wx.TextCtrl(self, wx.ID_ANY, size=(600, 200), style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY)
		
		szButton = wx.BoxSizer(wx.HORIZONTAL)
		
		self.bSlice = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSlice, size=BUTTONDIM)
		self.bSlice.SetToolTip("Slice the file using Slic3r")
		self.Bind(wx.EVT_BUTTON, self.onBSlice, self.bSlice)
		szButton.Add(self.bSlice)
		
		szButton.AddSpacer(100)
		
		self.bConfig = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSlic3r, size=BUTTONDIM)
		self.bConfig.SetToolTip("Load slic3r to modify configurations")
		self.Bind(wx.EVT_BUTTON, self.onConfig, self.bConfig)
		szButton.Add(self.bConfig)
		
		szButton.AddSpacer(20)
		
		self.bRefresh = wx.BitmapButton(self, wx.ID_ANY, self.images.pngRefresh, size=BUTTONDIM)
		self.bRefresh.SetToolTip("Refresh dialog box from slic3r configuration files")
		self.Bind(wx.EVT_BUTTON, self.onRefresh, self.bRefresh)
		szButton.Add(self.bRefresh)
		
		self.enableButtons()
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.AddSpacer(5)
		
		box = wx.StaticBox(self, wx.ID_ANY, "STL File")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bsizer.AddSpacer(5)
		bsizer.Add(szStl)
		bsizer.AddSpacer(5)
		sizer.Add(bsizer, flag = wx.EXPAND | wx.ALL, border = 5)
		
		box = wx.StaticBox(self, wx.ID_ANY, "G Code Directory")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bsizer.AddSpacer(5)
		bsizer.Add(szUseStl)
		bsizer.AddSpacer(5)
		bsizer.Add(szGcDir)
		bsizer.AddSpacer(5)
		sizer.Add(bsizer, flag = wx.EXPAND | wx.ALL, border = 5)
		
		box = wx.StaticBox(self, wx.ID_ANY, "G Code File")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bsizer.AddSpacer(10)
		bsizer.Add(szGc)
		bsizer.AddSpacer(10)
		sizer.Add(bsizer, flag = wx.EXPAND | wx.ALL, border = 5)
		
		box = wx.StaticBox(self, wx.ID_ANY, "Slic3r Configuration")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bsizer.AddSpacer(5)
		bsizer.Add(szCfg, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		bsizer.AddSpacer(5)
		bsizer.Add(szOverRide, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		bsizer.AddSpacer(5)
		sizer.Add(bsizer, flag = wx.EXPAND | wx.ALL, border = 5)

		sizer.Add(self.tcLog, flag=wx.EXPAND | wx.ALL, border=5)
		sizer.AddSpacer(5)
		sizer.Add(szButton, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		sizer.AddSpacer(5)
		
		self.SetSizer(sizer)
		self.Fit()
		if self.settings.dlgposition is not None:
			self.SetPosition(self.settings.dlgposition)
			
	def setImportButton(self, msg):
		if msg is None:
			self.bImportQ.SetToolTip("")
			self.bImportQ.Enable(False)
		else:
			self.bImportQ.SetToolTip(msg)
			self.bImportQ.Enable(True)
			
	def setImportFile(self, fn):
		if fn is None:
			self.bImport.SetToolTip("")
			self.bImport.Enable(False)
		else:
			self.bImport.SetToolTip("Import model file (%s)" % fn)
			self.bImport.Enable(True)
		
	def getExtruderCount(self, cfgfn):
		try:
			cfg = list(open(cfgfn))
		except:
			return 1
		
		for l in cfg:
			if "nozzle_diameter" in l:
				data = re.split("\s*=\s*", l)[1]
				return len(data.split(","))
		return 1
	
	def onCbGcDir(self, evt):
		self.settings.usestldir = self.cbGcDir.GetValue()
		self.bGcDir.Enable(not self.settings.usestldir)
		self.updateFileDisplay()
		
	def onChoicePrint(self, evt):
		cx = self.chPrint.GetSelection()
		self.settings.printchoice = self.chPrint.GetString(cx)
		
	def onChoicePrinter(self, evt):
		cx = self.chPrinter.GetSelection()
		pChoice = self.chPrinter.GetString(cx)
		self.settings.printerchoice = pChoice
		
		self.nExtruders = self.getExtruderCount(self.lCfgPrinter[pChoice])
		for ex in range(len(self.chFilament)):
			self.chFilament[ex].Enable(ex < self.nExtruders)
		
	def onChoiceFilament(self, evt):
		ex = evt.GetId() - FILAMENT_BASE
		cx = self.chFilament[ex].GetSelection()
		self.settings.filamentchoice[ex] = self.chFilament[ex].GetString(cx)
		
	def onConfig(self, evt):
		cmd = "%s --no-plater" % self.settings.executable
		args = shlex.split(str(cmd))
		try:
			subprocess.Popen(args,stderr=subprocess.STDOUT,stdout=subprocess.PIPE)
		except:
			self.log("Exception occurred trying to spawn slic3r")
			return
		
	def onRefresh(self, evt):
		printChoice = self.chPrint.GetString(self.chPrint.GetSelection())
		printerChoice = self.chPrinter.GetString(self.chPrinter.GetSelection())
		filamentChoices = []
		for fx in range(len(self.chFilament)):
			filamentChoices.append(self.chFilament[fx].GetString(self.chFilament[fx].GetSelection()))
			
		self.loadConfigFiles()
		
		self.chPrint.SetItems(self.choicesPrint)
		self.chPrinter.SetItems(self.choicesPrinter)
		for fx in range(len(self.chFilament)):
			self.chFilament[fx].SetItems(self.choicesFilament)
		
		cx = 0
		if printChoice in self.choicesPrint:
			cx = self.choicesPrint.index(printChoice)
		self.chPrint.SetSelection(cx)
		
		cx = 0
		if printerChoice in self.choicesPrinter:
			cx = self.choicesPrinter.index(printerChoice)
		self.chPrinter.SetSelection(cx)
		
		for fx in range(len(self.chFilament)):
			cx = 0
			if filamentChoices[fx] in self.choicesFilament:
				cx = self.choicesFilament.index(filamentChoices[fx])
			self.chFilament[fx].SetSelection(cx)

		
	def loadConfigFiles(self):
		self.lCfgPrint = self.getCfgFiles("print")
		self.lCfgPrinter = self.getCfgFiles("printer")
		self.lCfgFilament = self.getCfgFiles("filament")
		
		self.choicesPrint    = sorted(self.lCfgPrint.keys())
		self.choicesPrinter  = sorted(self.lCfgPrinter.keys())
		self.choicesFilament = sorted(self.lCfgFilament.keys())
		
	def getCfgFiles(self, sdir):
		cfgdir = os.path.join(self.settings.cfgdirectory, sdir)
		try:
			l = os.listdir(cfgdir)
		except:
			self.log("Unable to get %s profiles from slic3r profile directory: %s" % (sdir, self.settings.cfgdirectory))
			return {}
		r = {}
		for f in sorted(l):
			if not os.path.isdir(f) and f.lower().endswith(".ini"):
				r[os.path.splitext(os.path.basename(f))[0]] = os.path.join(cfgdir, f)
		return r
		
	def enableButtons(self):
		self.bSlice.Enable(not self.slicing and self.stlFn is not None)
		self.bExport.Enable(self.sliceComplete and self.gcFn is not None and not self.settings.autoexport)
		
	def onBGcDir(self, evt):
		dlg = wx.DirDialog(self,
				message="Choose a directory for G Code files",
				defaultPath=self.settings.lastgcodedirectory)
		
		rc = dlg.ShowModal()
		if rc == wx.ID_OK:
			path = dlg.GetPath()
			
		dlg.Destroy()
		if rc != wx.ID_OK:
			return
		
		self.settings.lastgcodedirectory = path
		self.gcDir = path
		self.updateFileDisplay()
				
	def onBSlice(self, evt):
		cfgMap = self.mergeConfigFiles()
		if self.cbOverRide.IsChecked():
			cfgMap = self.applyOverRides(cfgMap)
			
		self.gcSuffix = self.buildSuffix(cfgMap)
		tfn = tempfile.NamedTemporaryFile(delete=False)
		s = "# generated by repraptb on " + time.strftime("%c", time.localtime()) + "\n"
		tfn.write(s)
		for k in sorted(cfgMap.keys()):
			tfn.write(k + " = " + cfgMap[k] + "\n")
		
		tfn.close()
		self.cfgTempFn = tfn.name
		
		gcbn = os.path.splitext(os.path.basename(self.stlFn))[0] + ".gcode"
		if self.settings.usestldir:
			self.gcFn = os.path.join(os.path.dirname(self.stlFn), gcbn)
		else:
			self.gcFn = os.path.join(self.gcDir, gcbn)
			
		self.slicing = True
		self.sliceComplete = False
		thr = SlicerThread(self, self.settings.executable, self.stlFn, self.gcFn, self.cfgTempFn)
		thr.Start()
		self.updateFileDisplay()
		self.enableButtons()
		
	def buildSuffix(self, cfg):
		slCfg = self.getConfigString()

		filSiz = None
		if "filament_diameter" in cfg.keys():
			filSiz = cfg["filament_diameter"]

		tempsHE = None			
		if "first_layer_temperature" in cfg.keys():
			tempsHE = cfg["first_layer_temperature"]
		elif "temperature" in cfg.keys():
			tempsHE = cfg["temperature"]
			
		tempsBed = None
		if "first_layer_bed_temperature" in cfg.keys():
			tempsBed = cfg["first_layer_bed_temperature"]
		elif "bed_temperature" in cfg.keys():
			tempsBed = cfg["bed_temperature"]
		
		self.sufCfg = slCfg
		self.sufFilSiz = filSiz
		self.sufTemps = tempsHE + "/" + tempsBed
		return buildGCSuffix(slCfg, filSiz, tempsHE, tempsBed)
		
	def onBImport(self, evt):
		self.stlFn = self.parent.importStlFile()
		if self.stlFn is None:
			self.gcDir = None
			self.gcFn = None

		self.updateFileDisplay()			
		self.enableButtons()
		
	def onBImportFromQueue(self, evt):
		self.stlFn = self.parent.importStlFromQueue()
		if self.stlFn is None:
			self.gcDir = None
			self.gcFn = None
		
		self.updateFileDisplay()			
		self.enableButtons()
	
	def onBExport(self, evt):
		self.parent.exportGcFile(self.gcFn, True, self.settings.autoenqueue)
		
	def onAutoExport(self, evt):
		self.settings.autoexport = self.cbAutoExport.GetValue()
		self.enableButtons()
		
	def onAutoEnqueue(self, evt):
		self.settings.autoenqueue = self.cbAutoEnqueue.GetValue()
		
	def onBOpen(self, evt):
		wildcard = "STL (*.stl)|*.stl;*.STL|"	 \
			"All files (*.*)|*.*"
			
		dlg = wx.FileDialog(
			self, message="Choose an STL file",
			defaultDir=self.settings.laststldirectory, 
			defaultFile="",
			wildcard=wildcard,
			style=wx.FD_OPEN)

		rc = dlg.ShowModal()
		if rc == wx.ID_OK:
			path = dlg.GetPath().encode('ascii','ignore')
		dlg.Destroy()
		if rc != wx.ID_OK:
			return

		self.stlFn = path		
		self.settings.laststldirectory = os.path.dirname(path)
		
		self.updateFileDisplay()
		self.enableButtons()
		
	def slic3rUpdate(self, evt):
		if evt.state == SLIC3R_MESSAGE:
			self.tcLog.AppendText(evt.msg.rstrip()+"\n")
		elif evt.state in [ SLIC3R_CANCELLED, SLIC3R_FINISHED ]:
			self.tcLog.AppendText("Slic3r completed\n")
			self.slicing = False
			if evt.state == SLIC3R_FINISHED:
				self.sliceComplete = True
				self.addGcSuffix()
				self.history.addEvent(SliceComplete(
					self.history.addFile(self.gcFn),
					self.history.addFile(self.stlFn),
					self.sufCfg))
				self.parent.exportGcFile(self.gcFn, self.settings.autoexport, self.settings.autoenqueue)
				
			self.tcLog.AppendText("Deleting temporary config file '%s'" % self.cfgTempFn)
			os.unlink(self.cfgTempFn)
			self.updateFileDisplay()
			self.enableButtons()
			
	def addGcSuffix(self):
		fp = open(self.gcFn, "a")
		for s in self.gcSuffix:
			fp.write(s + "\n")
		fp.close()
			
	def updateFileDisplay(self):
		if self.stlFn is None:
			self.tcStl.SetValue("")
		else:
			self.tcStl.SetValue(self.stlFn)
			
		if self.settings.usestldir:
			self.tcGcDir.SetValue("")
		elif self.gcDir is None:
			self.tcGcDir.SetValue("")
		else:
			self.tcGcDir.SetValue(self.gcDir)
		
		if self.slicing:
			self.tcGc.SetValue("<slicing active>")
		elif self.sliceComplete:
			self.tcGc.SetValue(self.gcFn)
		else:
			self.tcGc.SetValue("")
		
	def onClose(self, evt):
		if self.ovrDlg is not None:
			self.ovrDlg.terminate()
		self.parent.Slic3rClosed()
		self.terminate()
		
	def terminate(self):
		self.settings.dlgposition = self.GetPosition()
		self.settings.save()
		self.Destroy()
		
	def getConfigString(self):
		cprint = self.chPrint.GetString(self.chPrint.GetSelection())
		cprinter = self.chPrinter.GetString(self.chPrinter.GetSelection())
		cfilament = []
		for ex in range(self.nExtruders):
			cfilament.append(self.chFilament[ex].GetString(self.chFilament[ex].GetSelection()))
			
		result = "Slic3r(%s/%s/%s)" % (cprint, cprinter, ",".join(cfilament))
		return result

	def mergeConfigFiles(self):		
		dProfile = {}
		k = self.chPrint.GetString(self.chPrint.GetSelection())
		dProfile.update(loadProfiles([self.lCfgPrint[k]], [], self.log))
		
		k = self.chPrinter.GetString(self.chPrinter.GetSelection())
		dProfile.update(loadProfiles([self.lCfgPrinter[k]], [], self.log))

		filamentFns = []		
		for ex in range(self.nExtruders):
			k = self.chFilament[ex].GetString(self.chFilament[ex].GetSelection())
			filamentFns.append(self.lCfgFilament[k])
		dProfile.update(loadProfiles(filamentFns, filamentMergeKeys, self.log))
		
		return dProfile
	
	def doOverRide(self, evt):
		self.bOverRide.Enable(False)
		self.ovDlg = Slic3rOverRideDlg(self, cmdFolder, self.closeOverRide)
		self.ovDlg.Show()
		
	def closeOverRide(self, changed):
		self.bOverRide.Enable(True)
		if changed:
			self.overRideValues = loadOverrides(cmdFolder)
			self.showOverRideValues()
			
		self.ovDlg.Destroy()
		self.ovrDlg = None
		
	def showOverRideValues(self):
		self.tcOverRide.Clear()
		for k in self.overRideValues.keys():
			self.tcOverRide.AppendText("%s = %s\n" % (k, self.overRideValues[k]))
			
	def applyOverRides(self, cfgMap):
		self.log("Applying Slic3r override values:")
		for k in self.overRideValues.keys():
			if k not in cfgMap.keys() and k not in multiOverrides.keys():
				self.log("==> override key (%s) is not in config map" % k)
			elif k in filamentMergeKeys:
				v = self.reconcileMergeKeys(cfgMap[k], self.overRideValues[k])
				cfgMap[k] = v
				self.log("  %s -> %s" % (k, v))
			elif k in multiOverrides.keys():
				self.log("  %s ->" % k)
				for mk in multiOverrides[k]:
					if mk in filamentMergeKeys:
						v = self.reconcileMergeKeys(cfgMap[mk], self.overRideValues[k])
					else:
						v = self.overRideValues[k]
					cfgMap[mk] = v
					self.log("    %s -> %s" % (mk, v))
			else:
				v = self.overRideValues[k]
				cfgMap[k] = v
				self.log("  %s -> %s" % (k, v))
				
		return cfgMap
	
	def reconcileMergeKeys(self, cfgList, ovList):
		cfl = cfgList.split(",")
		ovl = ovList.split(",")
		
		for i in range(len(ovl)):
			if i < len(cfl):
				cfl[i] = ovl[i]
				
		return ",".join(cfl)

		

