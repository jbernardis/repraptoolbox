import wx
import wx.propgrid as wxpg

import os
import re
import inspect
import json

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))

class PropertiesGrid(wxpg.PropertyGrid):
	def __init__(self, parent, catOrder, propertyOrder, definitions):

		pgFont = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		wxpg.PropertyGrid.__init__(self, parent)
		
		self.Bind(wxpg.EVT_PG_CHANGING, self.onPropertyChanged)
		self.definitionsMap = {}

		self.SetFont(pgFont)
		self.parent = parent
		self.catOrder = catOrder
		self.propertyOrder = propertyOrder
		self.definitions = definitions
		self.log = self.parent.log
		
		self.modified = False

		self.SetCaptionBackgroundColour(wx.Colour(215, 255, 215))
		self.SetCaptionTextColour(wx.Colour(0, 0, 0))
		self.SetMarginColour(wx.Colour(215, 255, 215))
		self.SetCellBackgroundColour(wx.Colour(255, 255, 191))
		self.SetCellTextColour(wx.Colour(0, 0, 0))
		self.SetCellDisabledTextColour(wx.Colour(0, 0, 0))
		self.SetEmptySpaceColour(wx.Colour(215, 255, 215))
		self.SetLineColour(wx.Colour(0, 0, 0))
		
		self.properties = {}
		self.SetExtraStyle(wxpg.PG_EX_HELP_AS_TOOLTIPS)

		lines = 0		
		for cat in catOrder:
			self.Append(wxpg.PropertyCategory(cat))
			lines += 1
			for k in propertyOrder[cat]:
				stg = definitions.getDefinition(k)
				if stg is None:
					self.log("unable to find definition (%s)" % k)
					continue
				self.definitionsMap[k] = stg
				
				pid = str(stg.getLabel())
					
				dt = stg.getDType()
				if dt == "str":
					pgp = wxpg.StringProperty(pid, value="")
					self.Append(pgp)
					
				elif dt == "float":
					pgp = wxpg.FloatProperty(pid, value=0.0)
					self.Append(pgp)
					
				elif dt in ["int", "extruder"]:
					pgp = wxpg.IntProperty(pid, value=0)
					self.Append(pgp)
					
				elif dt == "bool":
					pgp = wxpg.BoolProperty(pid, value=False)
					self.Append(pgp)
					self.SetPropertyAttribute(pid, "UseCheckbox", True)
					
				elif dt == "enum":
					opts = [str(x) for x in stg.getOptions()]
					pgp = wxpg.EnumProperty(pid, labels=opts, values=range(len(opts)), value=0)
					self.Append(pgp)
					
				else:
					self.log("taking default action for unknown data type: %s" % dt)
					pgp = wxpg.StringProperty(pid, value="")
					self.Append(pgp)
				
				lines += 1
				self.properties[k] = pgp

		self.rowCount = lines
		
		self.setBaseValues()
		self.SetSplitterLeft()
		
	def setBaseValues(self):
		for cat in self.catOrder:
			for k in self.propertyOrder[cat]:
				if not k in self.definitionsMap.keys():
					continue
				
				stg = self.definitionsMap[k]
				pid = str(stg.getLabel())
					
				dt = stg.getDType()
				if dt == "str":
					v = stg.getDefault()
					if v is not None:
						v = v.replace("\n", "\\n")
					v = str(v)
					self.SetPropertyValue(pid, v)
					
				elif dt == "float":
					v = stg.getDefault()
					if v is None:
						v = 0.0
					try:
						v = float(v)
					except:
						self.log("cannot convert " + str(v) + " to type float")
						v = 0.0
							
					self.SetPropertyValue(pid, v)
					
				elif dt in ["int", "extruder"]:
					v = stg.getDefault()
					if v is None:
						v = 0
					try:
						v = int(v)
					except:
						self.log("cannot convert "+ str(v) + " to type int")
						v = 0.0

					self.SetPropertyValue(pid, v)
					
				elif dt == "bool":
					v = stg.getDefault()
					if v is None:
						v = False
						
					self.SetPropertyValue(pid, v)
					
				elif dt == "enum":
					opts = [str(x) for x in stg.getOptions()]
					v = stg.getDefault()
					if v is None:
						v = opts[0]
						vx = 0
					else:
						try:
							vx = opts.index(v)
						except:
							v = opts[0]
							vx = 0
					self.SetPropertyValue(pid, vx)
					
				else:
					self.log("taking default action for unknown data type: %s" % dt)
					v = str(stg.getDefault())
					self.SetPropertyValue(pid, v)
					
				self.SetPropertyHelpString(pid, self.formHelpText(stg, v))
				
	def setOverlay(self, fn):
		self.setModified(False)
		self.setBaseValues()
		if fn is None:
			self.SetSplitterLeft()
			return
		
		with open(fn) as json_data:
			cfgData = json.load(json_data)

		for opt, value in cfgData.iteritems():
			if not opt in self.definitionsMap.keys():
				continue
			
			stg = self.definitionsMap[opt]
			pid = str(stg.getLabel())
				
			dt = stg.getDType()
			if dt == "str":
				v = str(value)
				if v is not None:
					v = v.replace("\n", "\\n")
				self.SetPropertyValue(pid, v)
				
			elif dt == "float":
				try:
					v = float(value)
				except:
					self.log("cannot convert "+ str(value) + " to type float")
					v = 0.0
						
				self.SetPropertyValue(pid, v)
				
			elif dt in ["int", "extruder"]:
				try:
					v = int(value)
				except:
					self.log("cannot convert "+ str(value) + " to type int")
					v = 0.0

				self.SetPropertyValue(pid, v)
				
			elif dt == "bool":
				v = False
				if value.lower() == "true":
					v = True
					
				self.SetPropertyValue(pid, v)
				
			elif dt == "enum":
				opts = [str(x) for x in stg.getOptions()]
				try:
					v = value
					vx = opts.index(value)
				except:
					v = opts[0]
					vx = 0
				self.SetPropertyValue(pid, vx)
				
			else:
				continue
				
			self.SetPropertyHelpString(pid, self.formHelpText(stg, v))
			
		self.SetSplitterLeft()

	def onPropertyChanged(self, evt):
		self.setModified()
		
	def hasBeenModified(self):
		return self.modified
	
	def setModified(self, flag=True):
		self.modified = flag
		self.parent.setModified(flag)
		
	def formHelpText(self, stg, cv):
		ht = stg.getDescription()
		
		ut = stg.getUnit()
		if ut is not None:
			ht += " (%s)" % ut
			
		dft = stg.getDefault()
		dt = stg.getDType()
		if dt == "str":
			if dft is not None:
				dft = "\\n".join(re.split('\n', dft))

		if cv != dft:
			ht += " Default: %s" % str(dft)
		
		return ht
		
	def getHeight(self):
		n = self.GetRowHeight()
		ht = n * (self.rowCount+1) + 15
		if ht > 500:
			ht = 500
		return ht
		
	def setProperty(self, pid, value):
		if pid not in self.properties.keys():
			self.log("Unknown property key: %s" % pid)
			return
		
		self.properties[pid].SetValue(value)
		
	def getNonDefaultProperties(self):
		result = {}
		for k in self.properties.keys():
			pgp = self.properties[k]
			stg = self.definitionsMap[k]
			
			gridVal = str(pgp.GetValueAsString()) 
			dftVal = str(stg.getDefault())
			
			dt = stg.getDType()
			
			if dt == "float":
				if gridVal.endswith(".0"):
					gridVal = gridVal[:-2]
				if dftVal.endswith(".0"):
					dftVal = dftVal[:-2]
					
			elif dt == "str":
				gridVal = gridVal.replace("\\n", "\n")
				
			if gridVal != dftVal:
				result[k] = str(gridVal)
				
		return result
