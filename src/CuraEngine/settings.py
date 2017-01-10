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
		self.jsonfile = "/usr/share/cura/resources/definitions/fdmprinter.def.json"
		self.usestldir = True
		self.laststldirectory = "."
		self.lastgcodedirectory = "."
		self.profilechoice = "normal"
		self.printerchoice = "prism"
		self.materialchoice = ["PLA", "PLA", "PLA", "PLA"]
		self.autoexport = True
		self.centerobject = True
		
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
				elif opt == "centerobject":
					self.centerobject = parseBoolean(value, True)
				elif opt == "executable":
					self.executable = value
				elif opt == "cfgexecutable":
					self.cfgexecutable = value
				elif opt == "cfgdirectory":
					self.cfgdirectory = value
				elif opt == "jsonfile":
					self.jsonfile = value
				elif opt == "profilechoice":
					self.profilechoice = value
				elif opt == "printerchoice":
					self.printerchoice = value
				elif opt == "autoexport":
					self.autoexport = parseBoolean(value, True)
				elif opt == "materialchoice":
					self.materialchoice = re.split("\s*,\s*", value)
		else:
			print "no section named (%s) in inifile (%s)" % (self.section, self.inifile)
					
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
		self.cfg.set(self.section, "profilechoice", str(self.profilechoice))
		self.cfg.set(self.section, "printerchoice", str(self.printerchoice))
		self.cfg.set(self.section, "materialchoice", ",".join(self.materialchoice))
		self.cfg.set(self.section, "autoexport", str(self.autoexport))
		self.cfg.set(self.section, "centerobject", str(self.centerobject))

		try:		
			cfp = open(self.inifile, 'w')
		except:
			print "Unable to open settings file %s for writing" % self.inifile
			return
		self.cfg.write(cfp)
		cfp.close()
