'''
Created on Oct 28, 2016

@author: Jeff
'''
import os, inspect

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))

import wx.lib.newevent
import subprocess
import thread
import json

from settings import Settings
from images import Images
from gcsuffix import buildGCSuffix
from curadefinitions import CuraDefinitions
from curacfg import CuraCfgDlg

(SlicerEvent, EVT_CURA_UPDATE) = wx.lib.newevent.NewEvent()
CURA_MESSAGE = 1
CURA_FINISHED = 2
CURA_CANCELLED = 3

MATERIAL_BASE = 1000
BUTTONDIM = (48, 48)

EnableIfTrue = {
	"acceleration_print": "acceleration_enabled",
	"acceleration_print_layer_0": "acceleration_enabled", 
	"acceleration_topbottom": "acceleration_enabled",
	"acceleration_layer_0": "acceleration_enabled"
	}



def loadProfile(fn, log, curasettings):
	with open(fn) as json_data:
		kdict = json.load(json_data)

	result = {}		
	for k, v in kdict.iteritems():
		df = curasettings.getDefinition(k)
		if df is None:
			print "Unable to find definition for (%s)" % k
			continue
		dt = df.getDType()
		
		if dt == "bool":
			result[k] = str(v).lower()
			
		else:
			result[k] = v
			
	return result

class SlicerThread:
	def __init__(self, win, settings, stlFile, gcFile, curasettings, profileCfg, materialCfg, printerCfg):
		self.win = win
		self.settings = settings
		self.stlFile = stlFile
		self.gcFile = gcFile
		self.curasettings = curasettings
		self.profileCfg = profileCfg
		self.materialCfg = materialCfg
		self.printerCfg = printerCfg
		print "SlicerThread: profile = ", profileCfg
		print ""
		print "Printer = ", printerCfg
		print ""
		for m in materialCfg:
			print "Material = ", m
			print ""

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
	
	def addArgs(self, cfg):
		result = []
		for k,v in cfg.iteritems():
			if self.includeSetting(k, cfg):
				result.extend(("-s", "%s=%s" % (k,v)))
		
		return result
	
	def includeSetting(self, sid, cfg):
		stg = self.curasettings.getDefinition(sid)
		if stg is None:
			return True
		
		ex = stg.getEnable()
		if ex is None:
			return True
		
		print "Need to evaluate (%s) to see if (%s) should be included" % (ex, sid)
		
		includeStg = True
		if sid in EnableIfTrue.keys():
			tf = EnableIfTrue[sid]
			if tf in cfg.keys():
				includeStg = cfg[tf]
				if includeStg:
					print "including %s because %s is true" % (sid, tf)
				else:
					print "excluding %s because %s is false" % (sid, tf)
			else:
				print "excluding %s because %s is defaulting" % (sid, tf)
				includeStg = False
			
		return includeStg

	def Run(self):
		args = [self.settings.executable, "slice", "-j", self.settings.jsonfile, "-o", self.gcFile]
		v = str(self.settings.centerobject).lower()
		args.extend(["-s", "center_object=%s" % v])
		args.extend(self.addArgs(self.profileCfg))
		args.extend(self.addArgs(self.printerCfg))
		ex = 0
		for m in self.materialCfg:
			args.append("-e%d" % ex)
			ex += 1
			args.extend(self.addArgs(m))

		args.extend(("-l", self.stlFile))
		print args
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
		
		self.curasettings = CuraDefinitions(self.settings.jsonfile)
		
		self.Bind(EVT_CURA_UPDATE, self.curaUpdate)
		self.Show()
		ico = wx.Icon(os.path.join(cmdFolder, "images", "cura.png"), wx.BITMAP_TYPE_PNG)
		self.SetIcon(ico)
		
		self.tcStl = wx.TextCtrl(self, wx.ID_ANY, "", size=(450, -1), style=wx.TE_READONLY)
		
		self.bOpen = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFileopen, size=BUTTONDIM)
		self.bOpen.SetToolTipString("Select an STL file for slicing")
		self.Bind(wx.EVT_BUTTON, self.onBOpen, self.bOpen)
		
		self.bImport = wx.BitmapButton(self, wx.ID_ANY, self.images.pngImport, size=BUTTONDIM)
		self.bImport.SetToolTipString("Import a model file from toolbox")
		self.Bind(wx.EVT_BUTTON, self.onBImport, self.bImport)
		
		self.cbGcDir = wx.CheckBox(self, wx.ID_ANY, "Use STL directory for G Code file")
		self.cbGcDir.SetToolTipString("Use the directory from the STL file for the resulting G Code file")
		self.cbGcDir.SetValue(self.settings.usestldir)
		self.Bind(wx.EVT_CHECKBOX, self.onCbGcDir, self.cbGcDir)

		self.tcGcDir = wx.TextCtrl(self, wx.ID_ANY, "", size=(450, -1), style=wx.TE_READONLY)
		self.bGcDir = wx.Button(self, wx.ID_ANY, "...", size=(30, 22))
		self.bGcDir.Enable(not self.settings.usestldir)
		self.bGcDir.SetToolTipString("Choose G Code directory")
		self.Bind(wx.EVT_BUTTON, self.onBGcDir, self.bGcDir)
		
		self.tcGc = wx.TextCtrl(self, wx.ID_ANY, "", size=(450, -1), style=wx.TE_READONLY)
		
		self.bExport = wx.BitmapButton(self, wx.ID_ANY, self.images.pngExport, size=BUTTONDIM)
		self.bExport.SetToolTipString("Export G Code file to toolbox")
		self.Bind(wx.EVT_BUTTON, self.onBExport, self.bExport)
		
		self.loadConfigFiles()
		
		self.chProfile = wx.Choice(self, wx.ID_ANY, size = (225,-1), choices = self.choicesProfile)
		self.Bind(wx.EVT_CHOICE, self.onChoiceProfile, self.chProfile)
		cxProfile = 0
		if self.settings.profilechoice in self.choicesProfile:
			cxProfile = self.choicesProfile.index(self.settings.profilechoice)
		else:
			self.settings.profilechoice = self.choicesProfile[0]
			cxProfile = 0
		self.chProfile.SetSelection(cxProfile)
		
		self.chPrinter = wx.Choice(self, wx.ID_ANY, size = (225, -1), choices = self.choicesPrinter)
		self.Bind(wx.EVT_CHOICE, self.onChoicePrinter, self.chPrinter)
		cxPrinter = 0
		if self.settings.printerchoice in self.choicesPrinter:
			cxPrinter = self.choicesPrinter.index(self.settings.printerchoice)
		else:
			self.settings.printerchoice = self.choicesPrinter[0]
			cxPrinter = 0
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
			else:
				self.settings.materialchoice[ex] = self.choicesMaterial[0]
				cxMaterial[ex] = 0
			self.chMaterial[ex].SetSelection(cxMaterial[ex])
			self.chMaterial[ex].Enable(ex < self.nExtruders)
			
		self.updateFileDisplay()

		szStl = wx.BoxSizer(wx.HORIZONTAL)
		szStl.AddSpacer((10, 10))
		szStl.Add(self.tcStl, 1, wx.TOP, 38)
		szStl.AddSpacer((10, 10))
		vsz = wx.BoxSizer(wx.VERTICAL)
		vsz.Add(self.bOpen)
		vsz.AddSpacer((5, 5))
		vsz.Add(self.bImport)
		szStl.Add(vsz)
		szStl.AddSpacer((10, 10))

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
		szGc.AddSpacer((10, 10))
		szGc.Add(self.tcGc, 1, wx.TOP, 8)
		szGc.AddSpacer((10, 10))
		szGc.Add(self.bExport)
		szGc.AddSpacer((10, 10))
				
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
		
		szOpts = wx.BoxSizer(wx.VERTICAL)
		self.cbCenter = wx.CheckBox(self, wx.ID_ANY, "Center Object")
		szOpts.Add(self.cbCenter)
		self.cbCenter.SetValue(self.settings.centerobject)
		self.Bind(wx.EVT_CHECKBOX, self.onCbCenter, self.cbCenter)
		szOpts.AddSpacer((5, 5))

		lbl = wx.StaticText(self, wx.ID_ANY, "X Offset")
		self.tcOffsetX = wx.TextCtrl(self, wx.ID_ANY, "0", size=(80, -1), style=wx.TE_RIGHT)
		self.tcOffsetX.SetToolTipString("Offset in the X direction")
		sz = wx.BoxSizer(wx.HORIZONTAL)
		sz.Add(lbl)
		sz.AddSpacer((5,5))
		sz.Add(self.tcOffsetX)
		szOpts.Add(sz)
		self.tcOffsetX.Bind(wx.EVT_KILL_FOCUS, self.evtOffsetXKillFocus, self.tcOffsetX)
		szOpts.AddSpacer((5, 5))

		lbl = wx.StaticText(self, wx.ID_ANY, "Y Offset")
		self.tcOffsetY = wx.TextCtrl(self, wx.ID_ANY, "0", size=(80, -1), style=wx.TE_RIGHT)
		self.tcOffsetY.SetToolTipString("Offset in the Y direction")
		sz = wx.BoxSizer(wx.HORIZONTAL)
		sz.Add(lbl)
		sz.AddSpacer((5,5))
		sz.Add(self.tcOffsetY)
		szOpts.Add(sz)
		self.tcOffsetY.Bind(wx.EVT_KILL_FOCUS, self.evtOffsetYKillFocus, self.tcOffsetY)
		
		self.tcLog = wx.TextCtrl(self, wx.ID_ANY, size=(600, 200), style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY)
		
		szButton = wx.BoxSizer(wx.HORIZONTAL)
		
		self.bSlice = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSlice, size=BUTTONDIM)
		self.bSlice.SetToolTipString("Slice the file using Cura Engine")
		self.Bind(wx.EVT_BUTTON, self.onBSlice, self.bSlice)
		szButton.Add(self.bSlice)
		
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
		sizer.AddSpacer((10, 10))
		
		box = wx.StaticBox(self, wx.ID_ANY, "STL File")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bsizer.AddSpacer((10, 10))
		bsizer.Add(szStl)
		bsizer.AddSpacer((10, 10))
		sizer.Add(bsizer, flag = wx.EXPAND | wx.ALL, border = 10)
		sizer.AddSpacer((10, 10))
		
		box = wx.StaticBox(self, wx.ID_ANY, "G Code Directory")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bsizer.AddSpacer((10, 10))
		bsizer.Add(szUseStl)
		bsizer.AddSpacer((10, 10))
		bsizer.Add(szGcDir)
		bsizer.AddSpacer((10, 10))
		sizer.Add(bsizer, flag = wx.EXPAND | wx.ALL, border = 10)
		sizer.AddSpacer((10, 10))
		
		box = wx.StaticBox(self, wx.ID_ANY, "G Code File")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bsizer.AddSpacer((10, 10))
		bsizer.Add(szGc)
		bsizer.AddSpacer((10, 10))
		sizer.Add(bsizer, flag = wx.EXPAND | wx.ALL, border = 10)
		
		sizer.AddSpacer((20, 20))
		sizer.Add(szCfg, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		sizer.AddSpacer((10, 10))
		sizer.Add(szOpts, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		sizer.AddSpacer((10, 10))
		sizer.Add(self.tcLog, flag=wx.EXPAND | wx.ALL, border=10)
		sizer.AddSpacer((10, 10))
		sizer.Add(szButton, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		sizer.AddSpacer((20, 20))
		
		self.SetSizer(sizer)
		self.Fit()
		
	def getExtruderCount(self, cfgfn):
		d = loadProfile(cfgfn, self.log, self.curasettings)
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
		
	def onCbCenter(self, evt):
		self.settings.centerobject = self.cbCenter.GetValue()
		
	def evtOffsetXKillFocus(self, evt):
		try:
			float(self.tcOffsetX.GetValue())
		except:
			self.log("Invalid value for X Offset %s" % self.tcOffsetX.GetValue())

	def evtOffsetYKillFocus(self, evt):
		try:
			float(self.tcOffsetY.GetValue())
		except:
			self.log("Invalid value for Y Offset %s" % self.tcOffsetY.GetValue())
		
	def onConfig(self, evt):
		self.cfgDlg = CuraCfgDlg(self.settings, self.curasettings, self.cfgClosed)
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
		dProfile = loadProfile(self.lCfgProfile[k], self.log, self.curasettings)
		k = self.chPrinter.GetString(self.chPrinter.GetSelection())
		dPrinter = loadProfile(self.lCfgPrinter[k], self.log, self.curasettings)
		dMaterial = []
		
		for i in range(self.nExtruders):
			k = self.chMaterial[i].GetString(self.chMaterial[i].GetSelection())
			dMaterial.append(loadProfile(self.lCfgMaterial[k], self.log, self.curasettings))

		self.gcSuffix = self.buildSuffix(dMaterial)
		
		gcbn = os.path.splitext(os.path.basename(self.stlFn))[0] + ".gcode"
		if self.settings.usestldir:
			self.gcFn = os.path.join(os.path.dirname(self.stlFn), gcbn)
		else:
			self.gcFn = os.path.join(self.gcDir, gcbn)
			
		self.slicing = True
		self.sliceComplete = False
		thr = SlicerThread(self, self.settings, self.stlFn, self.gcFn, self.curasettings, dProfile, dMaterial, dPrinter)
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
				filSiz.append(str(self.curasettings.getDefinition("material_diameter").getDefault()))
	
			if "material_print_temperature_layer_0" in cfg.keys():
				tempsHE.append(cfg["material_print_temperature_layer_0"])
			else:
				tempsHE.append(str(self.curasettings.getDefinition("material_print_temperature_layer_0").getDefault()))
				
			if "material_bed_temperature_layer_0" in cfg.keys():
				tempsBed.append(cfg["material_bed_temperature_layer_0"])
			else:
				tempsBed.append(str(self.curasettings.getDefinition("material_bed_temperature_layer_0").getDefault()))
		
		return buildGCSuffix(slCfg, ",".join(filSiz), ",".join(tempsHE), ",".join(tempsBed))

		
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
			self.tcLog.AppendText(evt.msg.rstrip().replace(" -s ", "\n") + "\n")
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
