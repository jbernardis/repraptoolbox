import ConfigParser
import os

INIFILE = "rrtb.ini"


def parseBoolean(val, defaultVal):
	lval = val.lower();
	
	if lval == 'true' or lval == 't' or lval == 'yes' or lval == 'y':
		return True
	
	if lval == 'false' or lval == 'f' or lval == 'no' or lval == 'n':
		return False
	
	return defaultVal

class Settings:
	def __init__(self, folder):
		self.cmdfolder = folder
		self.inifile = os.path.join(folder, INIFILE)
		self.section = "toolbox"	
		
		self.port = 8980
		self.printers = []
		self.tbposition = None
		self.logposition = None
		self.lastlogdirectory = "."
		self.pendantbaud = 9600
		self.pendantport = "/dev/pendant"
				
		self.cfg = ConfigParser.ConfigParser()
		self.cfg.optionxform = str
		if not self.cfg.read(self.inifile):
			print("Settings file %s does not exist.  Using default values" % INIFILE)
			return

		if self.cfg.has_section(self.section):
			for opt, value in self.cfg.items(self.section):
				if opt == 'printers':
					try:
						s = []
						exec("s=%s" % value)
						self.printers = s
					except:
						print "invalid value in ini file for printers"
						self.printers = []
						
				elif opt == 'lastlogdirectory':
					self.lastlogdirectory = value
					
				elif opt == 'pendantport':
					self.pendantport = value
					
				elif opt == 'pendantbaud':
					try:
						self.pendantbaud = int(value)
					except:
						print "Non-integer value in ini file for pendant baud rate"
						self.pendantbaud = 9600
					
				elif opt == 'port':
					try:
						self.port = int(value)
					except:
						print "Non-integer value in ini file for port"
						self.port = 8980
						
				elif opt == 'tbposition':
					try:
						s = []
						exec("s=%s" % value)
						self.tbposition = s
					except:
						print "invalid value in ini file for toolbox position"
						self.tbposition = None
						
				elif opt == 'logposition':
					try:
						s = []
						exec("s=%s" % value)
						self.logposition = s
					except:
						print "invalid value in ini file for log position"
						self.logposition = None
						
				else:
					print("Unknown %s option: %s - ignoring" % (self.section, opt))
		else:
			print("Missing %s section - assuming defaults" % self.section)
		
	def getSection(self, section):
		if not self.cfg.has_section(section):
			return None
		
		result = {}
		for opt, value in self.cfg.items(section):
			result[opt] = value
			
		return result
	
	def save(self):
		try:
			self.cfg.add_section(self.section)
		except ConfigParser.DuplicateSectionError:
			pass
		
		self.cfg.set(self.section, "printers", str(self.printers))
		self.cfg.set(self.section, "tbposition", str(self.tbposition))
		self.cfg.set(self.section, "logposition", str(self.logposition))
		self.cfg.set(self.section, "lastlogdirectory", str(self.lastlogdirectory))
		self.cfg.set(self.section, "port", str(self.port))
		self.cfg.set(self.section, "pendantport", str(self.pendantport))
		self.cfg.set(self.section, "pendantbaud", str(self.pendantbaud))

		try:		
			cfp = open(self.inifile, 'wb')
		except:
			print "Unable to open settings file %s for writing" % self.inifile
			return
		self.cfg.write(cfp)
		cfp.close()
