'''
Created on Oct 28, 2016

@author: Jeff
'''
import os, sys, inspect

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))

import wx.lib.newevent
import re
import subprocess
import thread
import time
import tempfile

from settings import Settings
from images import Images

(SlicerEvent, EVT_SLIC3R_UPDATE) = wx.lib.newevent.NewEvent()
SLIC3R_MESSAGE = 1
SLIC3R_FINISHED = 2
SLIC3R_CANCELLED = 3

FILAMENT_BASE = 1000
BUTTONDIM = (48, 48)

filamentMergeKeys = ['extrusion_multiplier', 'filament_diameter', 'first_layer_temperature', 'temperature']


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
		print args
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


class Slic3rDlg(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, None, title='Slic3r', size=(100, 100))
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.parent = parent
		self.log = self.parent.log
		self.settings = Settings(cmdFolder)
		self.images = Images(os.path.join(cmdFolder, "images"))
		
		self.stlFn = None
		self.gcDir = self.settings.lastgcodedirectory
		self.gcFn = None
		
		self.slicing = False
		self.sliceComplete = False
		
		self.Bind(EVT_SLIC3R_UPDATE, self.slic3rUpdate)
		self.Show()
		
		self.lblStl = wx.StaticText(self, wx.ID_ANY, "STL File:", size=(70, -1))
		self.tcStl = wx.TextCtrl(self, wx.ID_ANY, "", size=(300, -1), style=wx.TE_READONLY)
		
		self.cbGcDir = wx.CheckBox(self, wx.ID_ANY, "Use STL directory for G Code file")
		self.cbGcDir.SetToolTipString("Use the directory from the STL file for the resulting G Code file")
		self.cbGcDir.SetValue(self.settings.usestldir)
		self.Bind(wx.EVT_CHECKBOX, self.onCbGcDir, self.cbGcDir)

		self.tcGcDir = wx.TextCtrl(self, wx.ID_ANY, "", size=(220, -1), style=wx.TE_READONLY)
		self.bGcDir = wx.Button(self, wx.ID_ANY, "...", size=(30, 22))
		self.bGcDir.Enable(not self.settings.usestldir)
		self.bGcDir.SetToolTipString("Choose G Code directory")
		self.Bind(wx.EVT_BUTTON, self.onBGcDir, self.bGcDir)
		
		self.lblGc = wx.StaticText(self, wx.ID_ANY, "G Code File:", size=(70, -1))
		self.tcGc = wx.TextCtrl(self, wx.ID_ANY, "", size=(300, -1), style=wx.TE_READONLY)
		
		self.lCfgPrint = self.getCfgFiles("print")
		self.lCfgPrinter = self.getCfgFiles("printer")
		self.lCfgFilament = self.getCfgFiles("filament")
		
		self.choicesPrint    = sorted(self.lCfgPrint.keys())
		self.chPrint = wx.Choice(self, wx.ID_ANY, size = (150,-1), choices = self.choicesPrint)
		self.Bind(wx.EVT_CHOICE, self.onChoicePrint, self.chPrint)
		cxPrint = 0
		if self.settings.printchoice in self.choicesPrint:
			cxPrint = self.choicesPrint.index(self.settings.printchoice)
		self.chPrint.SetSelection(cxPrint)
		
		self.choicesPrinter  = sorted(self.lCfgPrinter.keys())
		self.chPrinter = wx.Choice(self, wx.ID_ANY, size = (150, -1), choices = self.choicesPrinter)
		self.Bind(wx.EVT_CHOICE, self.onChoicePrinter, self.chPrinter)
		cxPrinter = 0
		if self.settings.printerchoice in self.choicesPrinter:
			cxPrinter = self.choicesPrinter.index(self.settings.printerchoice)
		self.chPrinter.SetSelection(cxPrinter)
		
		self.nExtruders = self.getExtruderCount(self.lCfgPrinter[self.choicesPrinter[cxPrinter]])

		self.choicesFilament = sorted(self.lCfgFilament.keys())
		self.chFilament = [None, None, None, None]
		cxFilament = [0, 0, 0, 0]
		for ex in range(len(self.chFilament)):
			self.chFilament[ex] = wx.Choice(self, FILAMENT_BASE + ex, size = (150, -1), choices = self.choicesFilament)
			self.Bind(wx.EVT_CHOICE, self.onChoiceFilament, self.chFilament[ex])
			if self.settings.filamentchoice[ex] in self.choicesFilament:
				cxFilament[ex] = self.choicesFilament.index(self.settings.filamentchoice[ex])
			self.chFilament[ex].SetSelection(cxFilament[ex])
			self.chFilament[ex].Enable(ex < self.nExtruders)
			
		self.updateFileDisplay()

		szStl = wx.BoxSizer(wx.HORIZONTAL)
		szStl.AddSpacer((20, 10))
		szStl.Add(self.lblStl)
		szStl.Add(self.tcStl)

		szUseStl = wx.BoxSizer(wx.HORIZONTAL)
		szUseStl.AddSpacer((20, 10))
		szUseStl.Add(self.cbGcDir)
		
		szGcDir = wx.BoxSizer(wx.HORIZONTAL)
		szGcDir.AddSpacer((10, 10))
		szGcDir.Add(self.tcGcDir)
		szGcDir.AddSpacer((10, 10))
		szGcDir.Add(self.bGcDir)
		szGcDir.AddSpacer((10, 10))

		szGc = wx.BoxSizer(wx.HORIZONTAL)
		szGc.AddSpacer((20, 10))
		szGc.Add(self.lblGc)
		szGc.Add(self.tcGc)
				
		szCfgL = wx.BoxSizer(wx.VERTICAL)
		szCfgR = wx.BoxSizer(wx.VERTICAL)
		
		szCfgL.Add(wx.StaticText(self, wx.ID_ANY, "Print:"))
		szCfgL.Add(self.chPrint)
		
		szCfgL.AddSpacer((20, 20))
		szCfgL.Add(wx.StaticText(self, wx.ID_ANY, "Printer:"))
		szCfgL.Add(self.chPrinter)

		szCfgR.Add(wx.StaticText(self, wx.ID_ANY, "Filament:"))
		for ex in range(len(self.chFilament)):
			szCfgR.Add(self.chFilament[ex])
			
		szCfg = wx.BoxSizer(wx.HORIZONTAL)
		szCfg.Add(szCfgL)
		szCfg.AddSpacer((50, 20))
		szCfg.Add(szCfgR)
		
		self.tcLog = wx.TextCtrl(self, wx.ID_ANY, size=(400, 200), style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY)
		
		szButton = wx.BoxSizer(wx.HORIZONTAL)
		
		self.bSlice = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSlice, size=BUTTONDIM)
		self.bSlice.SetToolTipString("Slice the file using Slic3r")
		self.Bind(wx.EVT_BUTTON, self.onBSlice, self.bSlice)
		szButton.Add(self.bSlice)
		
		szButton.AddSpacer((100, 10))
		
		self.bOpen = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFileopen, size=BUTTONDIM)
		self.bOpen.SetToolTipString("Select an STL file for slicing")
		self.Bind(wx.EVT_BUTTON, self.onBOpen, self.bOpen)
		szButton.Add(self.bOpen)
		
		szButton.AddSpacer((20, 20))
		
		self.bImport = wx.BitmapButton(self, wx.ID_ANY, self.images.pngImport, size=BUTTONDIM)
		self.bImport.SetToolTipString("Import a model file from toolbox")
		self.Bind(wx.EVT_BUTTON, self.onBImport, self.bImport)
		szButton.Add(self.bImport)
		
		szButton.AddSpacer((20, 20))
		
		self.bExport = wx.BitmapButton(self, wx.ID_ANY, self.images.pngExport, size=BUTTONDIM)
		self.bExport.SetToolTipString("Export G Code file to toolbox")
		self.Bind(wx.EVT_BUTTON, self.onBExport, self.bExport)
		szButton.Add(self.bExport)
		
		self.enableButtons()
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.AddSpacer((20, 20))
		sizer.Add(szStl)
		sizer.AddSpacer((10, 20))
		
		box = wx.StaticBox(self, -1, "G Code Directory")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)

		bsizer.AddSpacer((10, 10))
		bsizer.Add(szUseStl)
		bsizer.AddSpacer((10, 10))
		bsizer.Add(szGcDir)
		bsizer.AddSpacer((10, 10))
		
		sizer.Add(bsizer, 1, wx.ALIGN_CENTER_HORIZONTAL, 1)
		
		sizer.AddSpacer((10, 20))
		sizer.Add(szGc)
		sizer.AddSpacer((10, 10))
		
		sizer.AddSpacer((20, 20))
		sizer.Add(szCfg, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		sizer.AddSpacer((10, 10))
		sizer.Add(self.tcLog, flag=wx.EXPAND | wx.ALL, border=10)
		sizer.AddSpacer((10, 10))
		sizer.Add(szButton, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		sizer.AddSpacer((20, 20))
		
		self.SetSizer(sizer)
		self.Fit()
		
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
		self.bExport.Enable(self.sliceComplete and self.gcFn is not None)
		
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
		suffix = ";@#@# "
		if "filament_diameter" in cfg.keys():
			suffix += " F:%s " % cfg["filament_diameter"]
		else:
			suffix += " F:? "
			
		if "first_layer_temperature" in cfg.keys():
			suffix += " T:%s " % cfg["first_layer_temperature"]
		elif "temperature" in cfg.keys():
			suffix += " T:%s " % cfg["temperature"]
		else:
			suffix += " T:? "
			
		if "first_layer_bed_temperature" in cfg.keys():
			suffix += " B:%s " % cfg["first_layer_bed_temperature"]
		elif "bed_temperature" in cfg.keys():
			suffix += " B:%s " % cfg["bed_temperature"]
		else:
			suffix += " B:? "
		
		return suffix
		
	def onBImport(self, evt):
		self.stlFn = self.parent.importStlFile()
		if self.stlFn is None:
			self.gcDir = None
			self.gcFn = None

		self.updateFileDisplay()			
		self.enableButtons()
	
	def onBExport(self, evt):
		self.parent.exportGcFile(self.gcFn)
		
	def onBOpen(self, evt):
		wildcard = "STL (*.stl)|*.stl|"	 \
			"All files (*.*)|*.*"
			
		dlg = wx.FileDialog(
			self, message="Choose an STL file",
			defaultDir=self.settings.laststldirectory, 
			defaultFile="",
			wildcard=wildcard,
			style=wx.OPEN)

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
				if self.settings.autoexport:
					self.parent.exportGcFile(self.gcFn)
				
			self.tcLog.AppendText("Deleting temporary config file '%s'" % self.cfgTempFn)
			os.unlink(self.cfgTempFn)
			self.updateFileDisplay()
			self.enableButtons()
			
	def addGcSuffix(self):
		fp = open(self.gcFn, "a")
		fp.write(self.gcSuffix + "\n")
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
		self.settings.save()
		self.parent.Slic3rClosed()
		self.Destroy()

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
