import ConfigParser

import os

def parseBoolean(val, defaultVal):
	lval = val.lower();
	
	if lval == 'true' or lval == 't' or lval == 'yes' or lval == 'y':
		return True
	
	if lval == 'false' or lval == 'f' or lval == 'no' or lval == 'n':
		return False
	
	return defaultVal

class PrtSettings:
	def __init__(self, folder, printerName):
		self.section = printerName	
		
		self.inifile = os.path.join(folder, printerName + ".ini")

		self.nextruders = 1		
		self.xyspeed = 2000
		self.zspeed = 2000
		self.espeed = 300
		self.acceleration = 1500
		self.edistance = 5
		self.moveabsolute = True
		self.extrudeabsolute = True
		self.useM82 = False
		self.speedquery = None
		defaultBedinfo = [0, 125, 60, 110, 'M140', 'M190']
		self.bedinfo = defaultBedinfo
		defaultHeinfo = [0, 250, 185, 225, 'M104', 'M109']
		self.heinfo = defaultHeinfo
		self.lastdirectory = "."
		self.lastmacrodirectory = "."
		self.scale = 2
		self.buildarea = [200, 200]
		self.firmwaretype = "MARLIN"
		self.showmoves = False
		self.showprevious = False
		self.ctrlposition = None
		self.tempposition = None
		self.propposition = None
		self.monposition = None
		
		self.cfg = ConfigParser.ConfigParser()
		self.cfg.optionxform = str
		if not self.cfg.read(self.inifile):
			print "Settings file %s.ini does not exist.  Using default values" % printerName
			return

		if self.cfg.has_section(self.section):
			for opt, value in self.cfg.items(self.section):
				if opt == 'buildarea':
					try:
						s = (200, 200)
						exec("s=%s" % value)
						self.buildarea = s
					except:
						print "invalid value in ini file for buildarea"
						self.buildarea = (200, 200)
						
				elif opt == 'ctrlposition':
					try:
						s = None
						exec("s=%s" % value)
						self.ctrlposition = s
					except:
						self.tempposition = None
						
				elif opt == 'tempposition':
					try:
						s = None
						exec("s=%s" % value)
						self.tempposition = s
					except:
						self.tempposition = None
						
				elif opt == 'propposition':
					try:
						s = None
						exec("s=%s" % value)
						self.propposition = s
					except:
						self.propposition = None
						
				elif opt == 'monposition':
					try:
						s = None
						exec("s=%s" % value)
						self.monposition = s
					except:
						self.monposition = None
						
				elif opt == "lastdirectory":
					self.lastdirectory = value
					
				elif opt == "lastmacrodirectory":
					self.lastmacrodirectory = value
					
				elif opt == "firmwaretype":
					self.firmwaretype = value
					
				elif opt == 'nextruders':
					try:
						self.nextruders = int(value)
					except:
						print "Non-integer value in ini file for nextruders"
						self.nextruders = 1
						
					if self.nextruders < 1 or self.nextruders > 4:
						print "Out of range value in ini file for nextruders"
						self.nextruders = 1
						
				elif opt == 'scale':
					try:
						self.scale = int(value)
					except:
						print "Non-integer value in ini file for scale"
						self.scale = 2
						
				elif opt == 'xyspeed':
					try:
						self.xyspeed = int(value)
					except:
						print "Non-integer value in ini file for xyspeed"
						self.xyspeed = 2000
						
				elif opt == 'zspeed':
					try:
						self.zspeed = int(value)
					except:
						print "Non-integer value in ini file for zspeed"
						self.zspeed = 300
						
				elif opt == 'espeed':
					try:
						self.espeed = int(value)
					except:
						print "Non-integer value in ini file for espeed"
						self.espeed = 300
				
				elif opt == 'acceleration':
					try:
						self.acceleration = int(value)
					except:
						print "Non-integer value in ini file for acceleration"
						self.acceleration = 1500

				elif opt == 'edistance':
					try:
						self.edistance = int(value)
					except:
						print "Non-integer value in ini file for edistance"
						self.edistance = 5
						
				elif opt == 'speedquery':
					if value == "None":
						self.speedquery = None
					else:
						self.speedquery = value
						
				elif opt == 'moveabsolute':
					self.moveabsolute = parseBoolean(value, True)
					
				elif opt == 'extrudeabsolute':
					self.extrudeabsolute = parseBoolean(value, True)
					
				elif opt == 'usem82':
					self.useM82 = parseBoolean(value, False)
					
				elif opt == 'bedinfo':
					try:
						s = defaultBedinfo
						exec("s=%s" % value)
						self.bedinfo = s
					except:
						print "invalid value in ini file for bedinfo"
						self.bedinfo = defaultBedinfo
						
				elif opt == 'heinfo':
					try:
						s = defaultHeinfo
						exec("s=%s" % value)
						self.heinfo = s
					except:
						print "invalid value in ini file for heinfo"
						self.heinfo = defaultHeinfo
						
				elif opt == 'showmoves':
					self.showmoves = parseBoolean(value, False)
					
				elif opt == 'showprevious':
					self.showprevious = parseBoolean(value, False)
					
		self.loadMacros()

	def loadMacros(self):	
		self.macroOrder = []
		self.macroList = {}				
		section = "macros"	
		if self.cfg.has_section(section):
			i = 0
			while True:
				i += 1
				key = "macro." + str(i)
				if not self.cfg.has_option(section, key): break
				
				try:
					mkey, mfile = self.cfg.get(section, key).split(',', 1)
				except:
					self.showError("Unable to parse config for %s" % key)
					break
				
				mkey = mkey.strip()
				self.macroOrder.append(mkey)
				self.macroList[mkey] = mfile.strip()
			
	def save(self):
		try:
			self.cfg.add_section(self.section)
		except ConfigParser.DuplicateSectionError:
			pass
		
		self.cfg.set(self.section, "lastdirectory", str(self.lastdirectory))
		self.cfg.set(self.section, "lastmacrodirectory", str(self.lastmacrodirectory))
		self.cfg.set(self.section, "firmwaretype", str(self.firmwaretype))
		self.cfg.set(self.section, "nextruders", str(self.nextruders))
		self.cfg.set(self.section, "xyspeed", str(self.xyspeed))
		self.cfg.set(self.section, "zspeed", str(self.zspeed))
		self.cfg.set(self.section, "espeed", str(self.espeed))
		self.cfg.set(self.section, "acceleration", str(self.acceleration))
		self.cfg.set(self.section, "edistance", str(self.edistance))
		self.cfg.set(self.section, "moveabsolute", str(self.moveabsolute))
		self.cfg.set(self.section, "extrudeabsolute", str(self.extrudeabsolute))
		self.cfg.set(self.section, "usem82", str(self.useM82))
		self.cfg.set(self.section, "speedquery", str(self.speedquery))
		self.cfg.set(self.section, "bedinfo", str(self.bedinfo))
		self.cfg.set(self.section, "heinfo", str(self.heinfo))
		self.cfg.set(self.section, "scale", str(self.scale))
		self.cfg.set(self.section, "buildarea", str(self.buildarea))
		self.cfg.set(self.section, "showmoves", str(self.showmoves))
		self.cfg.set(self.section, "showprevious", str(self.showprevious))
		self.cfg.set(self.section, "ctrlposition", str(self.ctrlposition))
		self.cfg.set(self.section, "tempposition", str(self.tempposition))
		self.cfg.set(self.section, "propposition", str(self.propposition))
		self.cfg.set(self.section, "monposition", str(self.monposition))
		
		self.saveMacros()

		try:		
			cfp = open(self.inifile, 'wb')
		except:
			print "Unable to open settings file %s for writing" % self.inifile
			return
		self.cfg.write(cfp)
		cfp.close()
		
	def saveMacros(self):
		section = "macros"
		try:
			self.cfg.add_section(section)
		except ConfigParser.DuplicateSectionError:
			pass
			
		for m in range(len(self.macroOrder)):
			opt = "macro.%d" % (m+1)
			val = self.macroOrder[m] + "," + self.macroList[self.macroOrder[m]]
			self.cfg.set(section, opt, val)

