'''
Created on Oct 28, 2016

@author: Jeff
'''
import os, inspect

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))

import wx.lib.newevent
import shlex
import subprocess
import thread
import json

from settings import Settings
from images import Images
from gcsuffix import buildGCSuffix
from curacfg import CuraCfgDlg

(SlicerEvent, EVT_CURA_UPDATE) = wx.lib.newevent.NewEvent()
CURA_MESSAGE = 1
CURA_FINISHED = 2
CURA_CANCELLED = 3

MATERIAL_BASE = 1000
BUTTONDIM = (48, 48)


def loadProfile(fn, log):
	with open(fn) as json_data:
		kdict = json.load(json_data)
			
	return kdict

class SlicerThread:
	def __init__(self, win, executable, stlFile, gcFile, jsonFile, profileCfg, materialCfg, printerCfg):
		self.win = win
		self.executable = executable
		self.stlFile = stlFile
		self.gcFile = gcFile
		self.jsonFile = jsonFile
		self.profileCfg = profileCfg
		self.materialCfg = materialCfg
		self.printerCfg = printerCfg
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
		print "Need to build command line here"
		args = [self.executable, "-j", self.jsonFile, "-o", self.gcFile]
		for k,v in self.profileCfg.iteritems():
			args.extend(("-s", "%s=%s" % (k,v)))
		for k,v in self.printerCfg.iteritems():
			args.extend(("-s", "%s=%s" % (k,v)))
		ex = 0
		for m in self.materialCfg:
			args.append("-e%d" % ex)
			ex += 1
			for k,v in m.iteritems():
				args.extend(("-s", "%s=%s" % (k,v)))
		print args
		try:
			p = subprocess.Popen(args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
		except:
			evt = SlicerEvent(msg = "Exception occurred trying to spawn cura_engine", state = CURA_CANCELLED)
			wx.PostEvent(self.win, evt)
			return
		
		obuf = ''
		while not self.cancelled:
			o = p.stdout.read(1)
			if o == '': break
			if o == '\r' or o == '\n':
				if len(obuf.strip()) > 0:
					state = CURA_MESSAGE
					evt = SlicerEvent(msg = obuf, state = state)
					wx.PostEvent(self.win, evt)
				obuf = ''
			elif ord(o) < 32:
				pass
			else:
				obuf += o
				
		if self.cancelled:
			evt = SlicerEvent(msg = None, state = CURA_CANCELLED)
			p.kill()
		else:
			evt = SlicerEvent(msg = None, state = CURA_FINISHED)
			
		p.wait()
		wx.PostEvent(self.win, evt)

		self.running = False


class CuraEngineDlg(wx.Frame):
	def __init__(self, parent):
		wx.Frame.__init__(self, None, wx.ID_ANY, 'Cura Engine', size=(100, 100))
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.parent = parent
		self.log = self.parent.log
		self.settings = Settings(cmdFolder)
		self.images = Images(os.path.join(cmdFolder, "images"))
		
		self.cfgDlg = None
		
		self.stlFn = None
		self.gcDir = self.settings.lastgcodedirectory
		self.gcFn = None
		
		self.slicing = False
		self.sliceComplete = False
		
		self.Bind(EVT_CURA_UPDATE, self.curaUpdate)
		self.Show()
		ico = wx.Icon(os.path.join(cmdFolder, "images", "cura.png"), wx.BITMAP_TYPE_PNG)
		self.SetIcon(ico)
		
		self.lblStl = wx.StaticText(self, wx.ID_ANY, "STL File:", size=(70, -1))
		self.tcStl = wx.TextCtrl(self, wx.ID_ANY, "", size=(450, -1), style=wx.TE_READONLY)
		
		self.cbGcDir = wx.CheckBox(self, wx.ID_ANY, "Use STL directory for G Code file")
		self.cbGcDir.SetToolTipString("Use the directory from the STL file for the resulting G Code file")
		self.cbGcDir.SetValue(self.settings.usestldir)
		self.Bind(wx.EVT_CHECKBOX, self.onCbGcDir, self.cbGcDir)

		self.tcGcDir = wx.TextCtrl(self, wx.ID_ANY, "", size=(330, -1), style=wx.TE_READONLY)
		self.bGcDir = wx.Button(self, wx.ID_ANY, "...", size=(30, 22))
		self.bGcDir.Enable(not self.settings.usestldir)
		self.bGcDir.SetToolTipString("Choose G Code directory")
		self.Bind(wx.EVT_BUTTON, self.onBGcDir, self.bGcDir)
		
		self.lblGc = wx.StaticText(self, wx.ID_ANY, "G Code File:", size=(70, -1))
		self.tcGc = wx.TextCtrl(self, wx.ID_ANY, "", size=(450, -1), style=wx.TE_READONLY)
		
		self.loadConfigFiles()
		
		self.chProfile = wx.Choice(self, wx.ID_ANY, size = (225,-1), choices = self.choicesProfile)
		self.Bind(wx.EVT_CHOICE, self.onChoiceProfile, self.chProfile)
		cxProfile = 0
		if self.settings.profilechoice in self.choicesProfile:
			cxProfile = self.choicesProfile.index(self.settings.profilechoice)
		self.chProfile.SetSelection(cxProfile)
		
		self.chPrinter = wx.Choice(self, wx.ID_ANY, size = (225, -1), choices = self.choicesPrinter)
		self.Bind(wx.EVT_CHOICE, self.onChoicePrinter, self.chPrinter)
		cxPrinter = 0
		if self.settings.printerchoice in self.choicesPrinter:
			cxPrinter = self.choicesPrinter.index(self.settings.printerchoice)
		self.chPrinter.SetSelection(cxPrinter)
		
		if len(self.choicesPrinter) > 0:
			self.nExtruders = self.getExtruderCount(self.lCfgPrinter[self.choicesPrinter[cxPrinter]])
		else:
			self.nExtruders = 0

		self.chMaterial = [None, None, None, None]
		cxMaterial = [0, 0, 0, 0]
		for ex in range(len(self.chMaterial)):
			self.chMaterial[ex] = wx.Choice(self, MATERIAL_BASE + ex, size = (225, -1), choices = self.choicesMaterial)
			self.Bind(wx.EVT_CHOICE, self.onChoiceMaterial, self.chMaterial[ex])
			if self.settings.materialchoice[ex] in self.choicesMaterial:
				cxMaterial[ex] = self.choicesMaterial.index(self.settings.materialchoice[ex])
			self.chMaterial[ex].SetSelection(cxMaterial[ex])
			self.chMaterial[ex].Enable(ex < self.nExtruders)
			
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
		
		szCfgL.Add(wx.StaticText(self, wx.ID_ANY, "Profile:"))
		szCfgL.Add(self.chProfile)
		
		szCfgL.AddSpacer((20, 20))
		szCfgL.Add(wx.StaticText(self, wx.ID_ANY, "Printer:"))
		szCfgL.Add(self.chPrinter)

		szCfgR.Add(wx.StaticText(self, wx.ID_ANY, "Material:"))
		for ex in range(len(self.chMaterial)):
			szCfgR.Add(self.chMaterial[ex])
			
		szCfg = wx.BoxSizer(wx.HORIZONTAL)
		szCfg.Add(szCfgL)
		szCfg.AddSpacer((50, 20))
		szCfg.Add(szCfgR)
		
		self.tcLog = wx.TextCtrl(self, wx.ID_ANY, size=(600, 200), style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY)
		
		szButton = wx.BoxSizer(wx.HORIZONTAL)
		
		self.bSlice = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSlice, size=BUTTONDIM)
		self.bSlice.SetToolTipString("Slice the file using Cura Engine")
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
		
		szButton.AddSpacer((20, 20))
		
		self.bConfig = wx.BitmapButton(self, wx.ID_ANY, self.images.pngCuracfg, size=BUTTONDIM)
		self.bConfig.SetToolTipString("Load cura configurator")
		self.Bind(wx.EVT_BUTTON, self.onConfig, self.bConfig)
		szButton.Add(self.bConfig)
		
		szButton.AddSpacer((20, 20))
		
		self.bRefresh = wx.BitmapButton(self, wx.ID_ANY, self.images.pngRefresh, size=BUTTONDIM)
		self.bRefresh.SetToolTipString("Refresh dialog box from cura configuration files")
		self.Bind(wx.EVT_BUTTON, self.onRefresh, self.bRefresh)
		szButton.Add(self.bRefresh)
		
		self.enableButtons()
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.AddSpacer((20, 20))
		sizer.Add(szStl)
		sizer.AddSpacer((10, 20))
		
		box = wx.StaticBox(self, wx.ID_ANY, "G Code Directory")
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
		d = loadProfile(cfgfn, self.log)
		k = "machine_extruder_count"
		if k in d.keys():
			return int(d[k])
		return 1
	
	def onCbGcDir(self, evt):
		self.settings.usestldir = self.cbGcDir.GetValue()
		self.bGcDir.Enable(not self.settings.usestldir)
		self.updateFileDisplay()
		
	def onChoiceProfile(self, evt):
		cx = self.chProfile.GetSelection()
		self.settings.profilechoice = self.chProfile.GetString(cx)
		
	def onChoicePrinter(self, evt):
		cx = self.chPrinter.GetSelection()
		pChoice = self.chPrinter.GetString(cx)
		self.settings.printerchoice = pChoice
		
		self.nExtruders = self.getExtruderCount(self.lCfgPrinter[pChoice])
		for ex in range(len(self.chMaterial)):
			self.chMaterial[ex].Enable(ex < self.nExtruders)
		
	def onChoiceMaterial(self, evt):
		ex = evt.GetId() - MATERIAL_BASE
		cx = self.chMaterial[ex].GetSelection()
		self.settings.materialchoice[ex] = self.chMaterial[ex].GetString(cx)
		
	def onConfig(self, evt):
		self.cfgDlg = CuraCfgDlg(self.settings, self.cfgClosed)
		self.bConfig.Enable(False)
		
	def cfgClosed(self):
		self.bConfig.Enable(True)
		self.cfgDlg = None
		
	def onRefresh(self, evt):
		profileChoice = self.chProfile.GetString(self.chProfile.GetSelection())
		printerChoice = self.chPrinter.GetString(self.chPrinter.GetSelection())
		materialChoices = []
		for fx in range(len(self.chMaterial)):
			materialChoices.append(self.chMaterial[fx].GetString(self.chMaterial[fx].GetSelection()))
			
		self.loadConfigFiles()
		
		self.chProfile.SetItems(self.choicesProfile)
		self.chPrinter.SetItems(self.choicesPrinter)
		for fx in range(len(self.chMaterial)):
			self.chMaterial[fx].SetItems(self.choicesMaterial)
		
		cx = 0
		if profileChoice in self.choicesProfile:
			cx = self.choicesProfile.index(profileChoice)
		self.chProfile.SetSelection(cx)
		
		cx = 0
		if printerChoice in self.choicesPrinter:
			cx = self.choicesPrinter.index(printerChoice)
		self.chPrinter.SetSelection(cx)
		
		for fx in range(len(self.chMaterial)):
			cx = 0
			if materialChoices[fx] in self.choicesMaterial:
				cx = self.choicesMaterial.index(materialChoices[fx])
			self.chMaterial[fx].SetSelection(cx)

		
	def loadConfigFiles(self):
		self.lCfgProfile = self.getCfgFiles("profile")
		self.lCfgPrinter = self.getCfgFiles("printer")
		self.lCfgMaterial = self.getCfgFiles("material")
		
		self.choicesProfile  = sorted(self.lCfgProfile.keys())
		self.choicesPrinter  = sorted(self.lCfgPrinter.keys())
		self.choicesMaterial = sorted(self.lCfgMaterial.keys())
		
	def getCfgFiles(self, sdir):
		cfgdir = os.path.join(self.settings.cfgdirectory, sdir)
		try:
			l = os.listdir(cfgdir)
		except:
			self.log("Unable to get %s profiles from cura profile directory: %s" % (sdir, self.settings.cfgdirectory))
			return {}
		r = {}
		for f in sorted(l):
			if not os.path.isdir(f) and f.lower().endswith(".json"):
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
		k = self.chProfile.GetString(self.chProfile.GetSelection())
		dProfile = loadProfile(self.lCfgProfile[k], self.log)
		k = self.chPrinter.GetString(self.chPrinter.GetSelection())
		dPrinter = loadProfile(self.lCfgPrinter[k], self.log)
		dMaterial = []
		
		for i in range(self.nExtruders):
			k = self.chMaterial[i].GetString(self.chMaterial[i].GetSelection())
			dMaterial.append(loadProfile(self.lCfgMaterial[k], self.log))

		self.gcSuffix = self.buildSuffix(dMaterial)
		
		gcbn = os.path.splitext(os.path.basename(self.stlFn))[0] + ".gcode"
		if self.settings.usestldir:
			self.gcFn = os.path.join(os.path.dirname(self.stlFn), gcbn)
		else:
			self.gcFn = os.path.join(self.gcDir, gcbn)
			
		self.slicing = True
		self.sliceComplete = False
		thr = SlicerThread(self, self.settings.executable, self.stlFn, self.gcFn, dProfile, dMaterial, dPrinter)
		thr.Start()
		self.updateFileDisplay()
		self.enableButtons()
		
	def buildSuffix(self, cfgMaterial):
		slCfg = self.getConfigString()

		filSiz = []
		tempsHE = []			
		tempsBed = []
		for cfg in cfgMaterial:
			if "material_diameter" in cfg.keys():
				filSiz.append(cfg["material_diameter"])
			else:
				filSiz.append("")
	
			if "material_print_temperature_layer_0" in cfg.keys():
				tempsHE.append(cfg["material_print_temperature_layer_0"])
			elif "material_print_temperature" in cfg.keys():
				tempsHE.append(cfg["material_print_temperature_layer_0"])
			else:
				tempsHE.append("")
				
			if "material_bed_temperature_layer_0" in cfg.keys():
				tempsBed.append(cfg["material_bed_temperature_layer_0"])
			elif "material_bed_temperature" in cfg.keys():
				tempsBed.append(["material_bed_temperature"])
			else:
				tempsBed.append("")

		empty = "," * (len(cfgMaterial)-1)	
		
		filSiz = ",".join(filSiz)
		if filSiz == empty:
			filSiz = None	
		tempsHE = ",".join(tempsHE)
		if tempsHE == empty:
			tempsHE = None	
		tempsBed = ",".join(tempsBed)
		if tempsBed == empty:
			tempsBed = None	
			
		return buildGCSuffix(slCfg, filSiz, tempsHE, tempsBed)

		
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
		
	def curaUpdate(self, evt):
		if evt.state == CURA_MESSAGE:
			self.tcLog.AppendText(evt.msg.rstrip()+"\n")
		elif evt.state in [ CURA_CANCELLED, CURA_FINISHED ]:
			self.tcLog.AppendText("Cura engine completed\n")
			self.slicing = False
			if evt.state == CURA_FINISHED:
				self.sliceComplete = True
				self.addGcSuffix()
				if self.settings.autoexport:
					self.parent.exportGcFile(self.gcFn)
				
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
		if self.cfgDlg is not None:
			self.cfgDlg.Destroy()
			
		self.settings.save()
		self.parent.CuraEngineClosed()
		self.Destroy()
		
	def getConfigString(self):
		cprint = self.chProfile.GetString(self.chProfile.GetSelection())
		cprinter = self.chPrinter.GetString(self.chPrinter.GetSelection())
		cmaterial = []
		for ex in range(self.nExtruders):
			cmaterial.append(self.chMaterial[ex].GetString(self.chMaterial[ex].GetSelection()))
			
		result = "%s/%s/%s" % (cprint, cprinter, ",".join(cmaterial))
		return result
