#!/bin/env python
import wx
import os
import ConfigParser

from ovtypes import OvTypeCB, OvTypeInt, OvTypeNum, OvTypeNumList, OvTypeNumPct, OvTypeChoice

class OverRideField:
	def __init__(self, label, dataType, units, helpText=None):
		self.label = label
		self.dataType = dataType
		self.units = units
		self.helpText = helpText
		
	def getLabel(self):
		return self.label
	
	def getDataType(self):
		return self.dataType
	
	def getUnits(self):
		return self.units
	
	def setHelpText(self, ht):
		self.helpText = ht
	
	def getHelpText(self):
		return self.helpText
	
	

ovData = {}

ovData["filament_diameter"] = OverRideField("Filament diameter (list)", OvTypeNumList(), "mm", "Filament diameter in mm.  Comma separated list for multiple extruders")
ovData["extrusion_multiplier"] = OverRideField("Extrusion Multiplier (list)", OvTypeNumList(), None, "multiplier applied to extrusion amount.  Comma separated list for multiple extruders")
ovData["layer_height"] = OverRideField("Layer Height (mm)", OvTypeNum(), None, 'Layer height in mm')
ovData["extrusion_width"] = OverRideField("Extrusion Width", OvTypeNumPct(), "mm or %", "extrusion width in mm or as a percentage of layer height")
ovData["fill_density"] = OverRideField("Fill Density", OvTypeNumPct(), "dec or %", "density of fill material - a decimal or a percentage")
ovData["fill_pattern"] = OverRideField("Fill Pattern", OvTypeChoice(["Rectilinear", "Line", "Concentric", "Honeycomb", "3D Honeycomb", "Hilbert Curve",
									"Archimedean Chords", "Octagram Spiral" ]), None, "choose the infill pattern")
ovData["temperature"] = OverRideField("Temperature (list)", OvTypeNumList(), "deg", "extruder temperature - layers 2 and up.  Comma seperated list for multiple extruders")
ovData["bed_temperature"] = OverRideField("Bed Temperature", OvTypeNum(), "deg", "bed temperature - layers 2 and up.")
ovData["first_layer_temperature"] = OverRideField("First Layer Temperature (list)", OvTypeNumList(), "deg", "extruder temperature - layer 1 only.  Comma seperated list for multiple extruders")
ovData["first_layer_bed_temperature"] = OverRideField("First Layer Bed Temperature", OvTypeNum(), "deg", "bed temperature - layer 1 only")
ovData["printspeed"] = OverRideField("Perimeter, Infill, and Solid Infill Speed", OvTypeNum(), "mm/s", "print speed in mm/second for the stated print operations")
ovData["first_layer_speed"] = OverRideField("First Layer Speed", OvTypeNumPct(), "mm/s or %", "first layer print speed.  mm/s or a percentage of normal print speed")
ovData["travel_speed"] = OverRideField("Travel Speed", OvTypeNum(), "mm/s", "speed for non printing moves - mm/second")
ovData["skirts"] = OverRideField("Skirt Loops", OvTypeInt(), None, "Number of loops of the skirt")
ovData["skirt_height"] = OverRideField("Skirt Height", OvTypeInt(), None, "Number of layers of the skirt")
ovData["brim_width"] = OverRideField("Brim Width", OvTypeNum(), "mm", "width of the brim in mm.  0 = disable brim")
ovData["support_material"] = OverRideField("Support Material", OvTypeCB(), None, "Enable/Disable support")
ovData["raft_layers"] = OverRideField("Raft Layers", OvTypeInt(), None, "Number of layers of raft.  = 0 disable raft")

ovOrder = [ "filament_diameter", "extrusion_multiplier", "layer_height", "extrusion_width", "fill_density", "fill_pattern",
		"temperature", "first_layer_temperature", "bed_temperature", "first_layer_bed_temperature",
		"printspeed", "first_layer_speed", "travel_speed", "skirts", "skirt_height", "brim_width", "support_material", "raft_layers" ]

OVFN = "overrides.ini"
OVSECTION = "slic3r"

def loadOverrides(inidir):
	cfg = ConfigParser.ConfigParser()
	cfg.optionxform = str
	fn = os.path.join(inidir, OVFN)
	if not cfg.read(fn):
		return {}

	ov = {}
	if cfg.has_section(OVSECTION):
		for opt, value in cfg.items(OVSECTION):
			ov[opt] = value
			
	return ov

def saveOverrides(ov, inidir):
	cfg = ConfigParser.ConfigParser()
	cfg.optionxform = str
	cfg.add_section(OVSECTION)
	
	for opt, value in ov.iteritems():
		cfg.set(OVSECTION, opt, value)

	fn = os.path.join(inidir, OVFN)
	try:		
		cfp = open(fn, 'wb')
	except:
		print "Unable to open overrides file %s for writing" % OVFN
		return
	
	cfg.write(cfp)
	cfp.close()
	
class Slic3rOverRideDlg(wx.Frame):
	def __init__(self, parent, iniDir, cbClose):
		wx.Frame.__init__(self, None, wx.ID_ANY, 'Slic3r Over-Rides', size=(100, 100))
		self.parent = parent
		self.iniDir = iniDir
		self.cbClose = cbClose

		self.Bind(wx.EVT_CLOSE, self.doClose)
		
		sz = wx.BoxSizer(wx.VERTICAL)
		sz.AddSpacer((10, 10))
		
		self.cbs = {}
		self.tcs = {}
		self.dis = {}
		
		ov = loadOverrides(self.iniDir)
		self.modified = False
		
		preModified = False
		
		t = wx.TextCtrl(self, wx.ID_ANY, "", size=(-1, -1))
		HT = t.GetSizeTuple()[1]
		szWidget = (100, HT)
		t.Destroy()
		
		self.bSave = wx.Button(self, wx.ID_ANY, "Save")
		self.Bind(wx.EVT_BUTTON, self.doBSave, self.bSave)
		self.bSave.Enable(False)
		
		self.bExit = wx.Button(self, wx.ID_ANY, "Exit")
		self.Bind(wx.EVT_BUTTON, self.doClose, self.bExit)
		
		for tag in ovOrder:
			hsz = wx.BoxSizer(wx.HORIZONTAL)
			hsz.AddSpacer((10, 10))
			
			fld = ovData[tag]
			
			cb = wx.CheckBox(self, wx.ID_ANY, fld.getLabel(), size=(260, HT), name=tag)
			hsz.Add(cb)
			self.cbs[tag] = cb
			cb.SetValue(tag in ov.keys())
			self.Bind(wx.EVT_CHECKBOX, self.doCheckBox, cb)

			di = fld.getDataType()
			di.setTag(tag)
			self.dis[tag] = di	
			tc = di.createWidget(self, szWidget)
			hsz.Add(tc)
			ht = fld.getHelpText()
			if ht is not None:
				tc.SetToolTipString(ht)

			self.tcs[tag] = tc
			if cb.IsChecked():
				tc.Enable(True)
				if di.setValue(ov[tag]):
					preModified = True
			else:
				tc.Enable(False)
				
			di.enableBinding()

			units = fld.getUnits()				
			if not units is None:
				st = wx.StaticText(self, wx.ID_ANY, units)
				hsz.AddSpacer((10, 10))
				hsz.Add(st, 1, wx.TOP, int(HT/5.0))
				hsz.AddSpacer((5, 5))
				
			hsz.AddSpacer((10, 10))
			
			sz.Add(hsz)
			sz.AddSpacer((2, 2))
			
		sz.AddSpacer((20, 20))
		hsz = wx.BoxSizer(wx.HORIZONTAL)
		
		hsz.Add(self.bSave)
		hsz.AddSpacer((20, 20))
		hsz.Add(self.bExit)
		
		sz.Add(hsz, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		sz.AddSpacer((20, 20))
		
		self.SetSizer(sz)
		self.Layout()
		self.Fit()
		
		if preModified:
			self.setModified()
		
	def setModified(self, flag=True):
		self.modified = flag
		if flag:
			self.bSave.Enable(True)
			self.bExit.SetLabel("Cancel")
		else:
			self.bSave.Enable(False)
			self.bExit.SetLabel("Exit")
		
	def doCheckBox(self, evt):
		cb = evt.GetEventObject()
		tag = cb.GetName()
		
		self.tcs[tag].Enable(cb.IsChecked())
		self.setModified()
		
	def doBSave(self, evt):
		ov = {}
		
		for tag in self.cbs.keys():
			cb = self.cbs[tag]
			if cb.IsChecked():
				di = self.dis[tag]
				ov[tag] = di.getValue()

		saveOverrides(ov, self.iniDir)
		self.cbClose(True)

	def doClose(self, evt):
		if self.modified:
			dlg = wx.MessageDialog(self, 'Pending changes will be lost.\nAre you sure you want to exit?',
				'Abandon Changes?', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
			rc = dlg.ShowModal()
			dlg.Destroy()
			
			if rc == wx.ID_NO:
				return

		self.cbClose(False)
		
	def terminate(self):
		self.Destroy()
