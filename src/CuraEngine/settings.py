import ConfigParser

import os
import re

INIFILE = "curaengine.ini"

def parseBoolean(val, defaultVal):
	lval = val.lower();
	
	if lval == 'true' or lval == 't' or lval == 'yes' or lval == 'y':
		return True
	
	if lval == 'false' or lval == 'f' or lval == 'no' or lval == 'n':
		return False
	
	return defaultVal

class Settings:
	def __init__(self, folder):
		self.section = "curaengine"	
		
		self.executable = "/usr/bin/CuraEngine"
		self.cfgexecutable = "/usr/bin/cura"
		self.cfgdirectory = "/home/jeff/.curaengine"
		self.jsonfile = "/usr/share/cura/resources/definitions/fdmextruder.def.json"
		self.usestldir = True
		self.laststldirectory = "."
		self.lastgcodedirectory = "."
		self.profilechoice = "normal"
		self.printerchoice = "prism"
		self.materialchoice = ["PLA", "PLA", "PLA", "PLA"]
		self.autoexport = True
		
		self.inifile = os.path.join(folder, INIFILE)
		
		self.cfg = ConfigParser.ConfigParser()
		self.cfg.optionxform = str
		if not self.cfg.read(self.inifile):
			print "Settings file %s does not exist.  Using default values" % INIFILE
			return

		if self.cfg.has_section(self.section):
			for opt, value in self.cfg.items(self.section):
				if opt == "laststldirectory":
					self.laststldirectory = value
				elif opt == "lastgcodedirectory":
					self.lastgcodedirectory = value
				elif opt == "usestldir":
					self.usestldir = parseBoolean(value, True)
				elif opt == "executable":
					self.executable = value
				elif opt == "cfgdirectory":
					self.cfgdirectory = value
				elif opt == "printchoice":
					self.printchoice = value
				elif opt == "printerchoice":
					self.printerchoice = value
				elif opt == "autoexport":
					self.autoexport = parseBoolean(value, True)
				elif opt == "filamentchoice":
					self.filamentchoice = re.split("\s*,\s*", value)
					
	def save(self):
		try:
			self.cfg.add_section(self.section)
		except ConfigParser.DuplicateSectionError:
			pass
		
		self.cfg.set(self.section, "laststldirectory", str(self.laststldirectory))
		self.cfg.set(self.section, "lastgcodedirectory", str(self.lastgcodedirectory))
		self.cfg.set(self.section, "usestldir", str(self.usestldir))
		self.cfg.set(self.section, "executable", str(self.executable))
		self.cfg.set(self.section, "cfgdirectory", str(self.cfgdirectory))
		self.cfg.set(self.section, "printchoice", str(self.printchoice))
		self.cfg.set(self.section, "printerchoice", str(self.printerchoice))
		self.cfg.set(self.section, "filamentchoice", ",".join(self.filamentchoice))
		self.cfg.set(self.section, "autoexport", str(self.autoexport))

		try:		
			cfp = open(self.inifile, 'wb')
		except:
			print "Unable to open settings file %s for writing" % self.inifile
			return
		self.cfg.write(cfp)
		cfp.close()
