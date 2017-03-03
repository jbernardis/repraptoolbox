import ConfigParser

import os

INIFILE = "plater.ini"

def parseBoolean(val, defaultVal):
	lval = val.lower();
	
	if lval == 'true' or lval == 't' or lval == 'yes' or lval == 'y':
		return True
	
	if lval == 'false' or lval == 'f' or lval == 'no' or lval == 'n':
		return False
	
	return defaultVal

class Settings:
	def __init__(self, folder):
		self.section = "plater"	
		
		self.lastdirectory = "."
		self.scale = 2
		self.buildarea = [200, 200]
		self.preview = True
		self.centeronarrange = True
		self.spinstlview = True
		self.autoexport = True
		self.autoenqueue = False
		self.arrangestrategy = "row"
		self.arrangemargin = 2
		
		self.inifile = os.path.join(folder, INIFILE)
		
		self.cfg = ConfigParser.ConfigParser()
		self.cfg.optionxform = str
		if not self.cfg.read(self.inifile):
			print "Settings file %s does not exist.  Using default values" % INIFILE
			return

		if self.cfg.has_section(self.section):
			for opt, value in self.cfg.items(self.section):
				if opt == "lastdirectory":
					self.lastdirectory = value
				elif opt == "arrangestrategy":
					self.arrangestrategy = value
				elif opt == "arrangemargin":
					try:
						self.arrangemargin = int(value)
					except:
						print "Invalid value for arrangemargin"
						self.arrangemargin = 2
				elif opt == "preview":
					self.preview = parseBoolean(value, True)
				elif opt == "centeronarrange":
					self.centeronarrange = parseBoolean(value, True)
				elif opt == "spinstlview":
					self.spinstlview = parseBoolean(value, True)
				elif opt == "autoexport":
					self.autoexport = parseBoolean(value, True)
				elif opt == "autoenqueue":
					self.autoenqueue = parseBoolean(value, False)
				elif opt == "scale":
					try:
						self.scale = int(value)
					except:
						print "Invalid value for scale"
						self.scale = 2
				elif opt == 'buildarea':
					try:
						s = [200, 200]
						exec("s=%s" % value)
						self.buildarea = s
					except:
						print "invalid value in ini file for buildarea"
						self.buildarea = [200, 200]
					
	def save(self):
		try:
			self.cfg.add_section(self.section)
		except ConfigParser.DuplicateSectionError:
			pass
		
		self.cfg.set(self.section, "lastdirectory", str(self.lastdirectory))
		self.cfg.set(self.section, "arrangestrategy", str(self.arrangestrategy))
		self.cfg.set(self.section, "arrangemargin", str(self.arrangemargin))
		self.cfg.set(self.section, "preview", str(self.preview))
		self.cfg.set(self.section, "centeronarrange", str(self.centeronarrange))
		self.cfg.set(self.section, "spinstlview", str(self.spinstlview))
		self.cfg.set(self.section, "autoexport", str(self.autoexport))
		self.cfg.set(self.section, "autoenqueue", str(self.autoenqueue))
		self.cfg.set(self.section, "scale", str(self.scale))
		self.cfg.set(self.section, "buildarea", str(self.buildarea))

		try:		
			cfp = open(self.inifile, 'wb')
		except:
			print "Unable to open settings file %s for writing" % self.inifile
			return
		self.cfg.write(cfp)
		cfp.close()
