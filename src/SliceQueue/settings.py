import ConfigParser

import os

INIFILE = "slicequeue.ini"

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
		
		self.laststldirectory = "."
		self.showstlbasename = True
		
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
				elif opt == "showstlbasename":
					self.showstlbasename = parseBoolean(value, True)
					
	def save(self):
		try:
			self.cfg.add_section(self.section)
		except ConfigParser.DuplicateSectionError:
			pass
		
		self.cfg.set(self.section, "laststldirectory", str(self.laststldirectory))
		self.cfg.set(self.section, "showstlbasename", str(self.showstlbasename))

		try:		
			cfp = open(self.inifile, 'wb')
		except:
			print "Unable to open settings file %s for writing" % self.inifile
			return
		self.cfg.write(cfp)
		cfp.close()
