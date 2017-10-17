import ConfigParser
import os

INIFILE = "gedit.ini"


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
		self.section = "gedit"	
		
		self.buildarea = [200, 200]
		self.scale = 3
		self.nextruders = 1
		self.showprevious = True
		self.showmoves = True
		self.uselinenbrs = False
		self.autoexport = True
		self.autoenqueue = False
		self.lastdirectory = "C:\\"
		self.platemps = [60, 185]
		self.abstemps = [110, 225]
		self.acceleration = 150
		self.layerheight = 0.2
		
		self.cfg = ConfigParser.ConfigParser()
		self.cfg.optionxform = str
		if not self.cfg.read(self.inifile):
			print("Settings file %s does not exist.  Using default values" % INIFILE)
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
						
				elif opt == 'platemps':
					try:
						s = (60, 185)
						exec("s=%s" % value)
						self.platemps = s
					except:
						print "invalid value in ini file for platemps"
						self.platemps = (60, 185)
						
				elif opt == 'abstemps':
					try:
						s = (110, 225)
						exec("s=%s" % value)
						self.abstemps = s
					except:
						print "invalid value in ini file for abstemps"
						self.abstemps = (110, 225)
						
				elif opt == 'nextruders':
					try:
						self.nextruders = int(value)
					except:
						print("Non-integer value in ini file for nextruders")
						self.nextruders = 1
						
				elif opt == 'scale':
					try:
						self.scale = int(value)
					except:
						print("Non-integer value in ini file for scale")
						self.scale = 3
						
				elif opt == 'acceleration':
					try:
						self.acceleration = int(value)
					except:
						print("Non-integer value in ini file for acceleration")
						self.acceleration = 1500
						
				elif opt == 'layerheight':
					try:
						self.layerheight = float(value)
					except:
						print("Invalid float value in ini file for layerheight")
						self.layerheight = 0.2
						
				elif opt == 'lastdirectory':
					self.lastdirectory = value
						
				elif opt == 'uselinenbrs':
					self.uselinenbrs = parseBoolean(value, False)
						
				elif opt == 'showprevious':
					self.showprevious = parseBoolean(value, True)
						
				elif opt == 'showmoves':
					self.showmoves = parseBoolean(value, True)
						
				elif opt == 'autoexport':
					self.autoexport = parseBoolean(value, True)
						
				elif opt == 'autoenqueue':
					self.autoenqueue = parseBoolean(value, False)
						
				else:
					print("Unknown %s option: %s - ignoring" % (self.section, opt))
		else:
			print("Missing %s section - assuming defaults" % self.section)
	
	def save(self):
		try:
			self.cfg.add_section(self.section)
		except ConfigParser.DuplicateSectionError:
			pass
		
		self.cfg.set(self.section, "buildarea", str(self.buildarea))
		self.cfg.set(self.section, "nextruders", str(self.nextruders))
		self.cfg.set(self.section, "scale", str(self.scale))
		self.cfg.set(self.section, "showprevious", str(self.showprevious))
		self.cfg.set(self.section, "showmoves", str(self.showmoves))
		self.cfg.set(self.section, "autoexport", str(self.autoexport))
		self.cfg.set(self.section, "autoenqueue", str(self.autoenqueue))
		self.cfg.set(self.section, "uselinenbrs", str(self.uselinenbrs))
		self.cfg.set(self.section, "lastdirectory", str(self.lastdirectory))
		self.cfg.set(self.section, "platemps", str(self.platemps))
		self.cfg.set(self.section, "abstemps", str(self.abstemps))
		self.cfg.set(self.section, "acceleration", str(self.acceleration))
		self.cfg.set(self.section, "layerheight", str(self.layerheight))

		try:		
			cfp = open(self.inifile, 'wb')
		except:
			print "Unable to open settings file %s for writing" % self.inifile
			return
		self.cfg.write(cfp)
		cfp.close()
