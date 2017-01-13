import json
import copy

class CuraDefinition():
	def __init__(self, name):
		self.description = ""
		self.name = name
		self.label = None
		self.unit = None
		self.dtype = None
		self.options = None
		self.value = None
		self.default = None
		self.category = None
		self.perExtruder = False
		self.enable = None
		
	def setName(self, name):
		self.name = name
		
	def setDescription(self, desc):
		self.description = desc
		
	def setDefault(self, default):
		self.default = default
		
	def setLabel(self, label):
		self.label = label
		
	def setUnit(self, unit):
		self.unit = unit
		
	def setDType(self, dtype):
		self.dtype = dtype
		
	def setOptions(self, options):
		self.options = options
		
	def setValue(self, value):
		self.value = value
		
	def setCategory(self, cat):
		self.category = cat
		
	def setPerExtruder(self, flag):
		self.perExtruder = flag
		
	def setEnable(self, expr):
		self.enable = expr
		
	def getName(self):
		return self.name
	
	def getDescription(self):
		return self.description
	
	def getDefault(self):
		return self.default
		
	def getLabel(self):
		return self.label
		
	def getUnit(self):
		return self.unit
		
	def getDType(self):
		return self.dtype
		
	def getOptions(self):
		return self.options
		
	def getValue(self):
		return self.value
	
	def getCategory(self):
		return self.category
	
	def getPerExtruder(self):
		return self.perExtruder
	
	def getEnable(self):
		return self.enable
		
	def pprint(self, prefix=""):
		print prefix + "======="
		print prefix + "Name: %s" % self.name
		print prefix + "Description: %s" % self.description
		print prefix + "Default: (%s)" % self.default
		print prefix + "Label: (%s)" % self.label
		print prefix + "Unit: (%s)" % self.unit
		print prefix + "DType: (%s)" % self.dtype
		print prefix + "Options: (%s)" % self.options
		print prefix + "Value: (%s)" % self.value
		print prefix + "Per Extruder: (%s)" % str(self.perExtruder)
		print prefix + "Enable: (%s)" % str(self.enable)
		
class CuraDefinitionCategory():
	def __init__(self, name):
		self.name = name
		self.definitions = {}
		
	def getCategoryName(self):
		return self.name
		
	def addDefinition(self, definition):
		definition.setCategory(self.name)
		self.definitions[definition.getName()] = definition
		
	def getDefinition(self, definitionName):
		if not definitionName in self.definitions.keys():
			return None
		
		return self.definitions[definitionName]
		
	def __iter__(self):
		self.__lindex__ = 0
		self.__index__ = self.definitions.keys()
		return self
	
	def next(self):
		if self.__lindex__ < self.__len__():
			i = self.__lindex__
			self.__lindex__ += 1
			return self.definitions[self.__index__[i]]

		raise StopIteration
	
	def __len__(self):
		return len(self.definitions.keys())
		
class CuraDefinitions():
	def __init__(self, fn):
		self.categories = {}
		with open(fn) as json_data:
			jsdata = json.load(json_data)
		
		jsSettings = jsdata["settings"]
		
		for s in jsSettings.keys():
			self.parseChildren(s, jsSettings[s])
			
		stg = self.getDefinition("machine_nozzle_size")
		for i in range(3):
			stg1 = copy.copy(stg)
			stg1.setName("%s_%d" % (stg.getName(), i+1))
			stg1.setLabel("%s_%d" % (stg.getLabel(), i+1))
			self.addDefinition(stg.getCategory(), stg1)
			
	def parseChildren(self, category, jsdata):
		if "children" in jsdata.keys():
			for ch in jsdata["children"].keys():
				stg = CuraDefinition(ch)
				self.addDefinition(category, stg)
				
				chdata = jsdata["children"][ch]
				
				if "default_value" in chdata.keys():
					stg.setDefault(chdata["default_value"])
					
				if "description" in chdata.keys():
					stg.setDescription(chdata["description"])
					
				if "settable_per_extruder" in chdata.keys():
					stg.setPerExtruder(chdata["settable_per_extruder"])
					
				if "label" in chdata.keys():
					stg.setLabel(chdata["label"])
					
				if "unit" in chdata.keys():
					stg.setUnit(chdata["unit"])
	
				dtype = ""			
				if "type" in chdata.keys():
					dtype = chdata["type"]
					stg.setDType(dtype)
					
				if "value" in chdata.keys():
					stg.setValue(chdata["value"])
					
				if dtype == "enum" and "options" in chdata.keys():
					stg.setOptions(chdata["options"])
					
				self.parseChildren(category, chdata)
		
	def addDefinition(self, category, definition):
		if not category in self.categories.keys():
			self.categories[category] = CuraDefinitionCategory(category)
		self.categories[category].addDefinition(definition)
		
	def getDefinition(self, definitionName, category=None):
		if not category is None:
			if not category in self.categories.keys():
				return None
			
			return self.categories[category].getDefinition(definitionName)
		else:
			for cat in self.categories.keys():
				s = self.categories[cat].getDefinition(definitionName)
				if not s is None:
					return s
				
			return None
		
	def __iter__(self):
		self.__lindex__ = 0
		self.__index__ = self.categories.keys()
		return self
	
	def next(self):
		if self.__lindex__ < self.__len__():
			i = self.__lindex__
			self.__lindex__ += 1
			return self.categories[self.__index__[i]]

		raise StopIteration
	
	def __len__(self):
		return len(self.categories.keys())


