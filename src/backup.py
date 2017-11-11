import os
import zipfile
import sys, inspect

import ConfigParser

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))

BASEINIFILE = "rrtb.ini"

class CfgBackup:
	def __init__(self):
		self.baseIniFiles = [BASEINIFILE,
				"GCodeQueue/gcodequeue.ini",
				"GEdit/gedit.ini",
				"History/history.ini",
				"Plater/plater.ini",
				"SliceQueue/slicequeue.ini",
				"STLViewer/stlview.ini"]

		self.dataFiles = ["GCodeQueue/gcode.queue",
				"SliceQueue/slice.queue",
				"History/rrtb.history"]

		self.slicerIniFiles = [["CuraEngine/curaengine.ini", "curaengine", ["cfgdirectory", "jsonfile"]],
				["Slic3r/slic3r.ini", "slic3r", ["cfgdirectory"]]]

	def enqueueForBackup(self, fn, required=True):
		if not os.path.isfile(fn):
			print "file does not exist: %s" % fn
			return not required

		if not os.access(fn, os.R_OK):
			print "file is not readable: %s" % fn
			return False

		self.bkQueue.append(fn)
		return True

	def enqueueTreeForBackup(self, dname):
		for dirName, subdirList, fileList in os.walk(dname):
			for fname in fileList:
				self.enqueueForBackup(os.path.join(dirName, fname))

	def getPrinters(self, cfg, fn):
		section = "toolbox"	
		try:
			value = cfg.get(section, "printers")
			try:
				s = []
				exec("s=%s" % value)
				printers = s
				return printers
			except:
				print "invalid value in ini file for printers"
				return []
		except:
			print "Unable to parse ini file '%s' for printers" % fn
			return []

	def getMacros(self, cfg, fn):
		section = "macros"	

		if not cfg.has_section(section):
			print "No macros section in file '%s'" % fn
			return []

		idx = 1
		result = []
		while True:
			option = "macro.%d" % idx
			if not cfg.has_option(section, option):
				return result

			idx += 1
			value = cfg.get(section, option)
			try:
				fn = value.split(",")[1]
				result.append(fn)
			except:
				print "invalid value in ini file for %s" % option

	def backupQueue(self):
		self.bkQueue = []
		for fn in self.baseIniFiles:
			self.enqueueForBackup(os.path.join(cmdFolder, fn))

		for fn in self.dataFiles:
			self.enqueueForBackup(os.path.join(cmdFolder, fn))

		for fn, section, cfgkeys in self.slicerIniFiles:
			inifn = os.path.join(cmdFolder, fn)
			self.enqueueForBackup(inifn)
			cfg = ConfigParser.ConfigParser()
			cfg.optionxform = str
			if not cfg.read(inifn):
				print "Settings file %s does not exist." % inifn
			else:
				for k in cfgkeys:
					if cfg.has_option(section, k):
						self.enqueueTreeForBackup(cfg.get(section, k))
					else:
						print "settings file %s does not have section/option %s/%s" % (inifn, section, k)

		inifn = os.path.join(cmdFolder, BASEINIFILE)
		cfg = ConfigParser.ConfigParser()
		cfg.optionxform = str
		if not cfg.read(inifn):
			print "Settings file %s does not exist." % inifn
			p = []
		else:
			p = self.getPrinters(cfg, inifn)
			print "Discovered printers: ", str(p)

		macroMap = {}
		for pn in p:
			inifn = os.path.join(cmdFolder, "Printer", pn+".ini")
			cfg = ConfigParser.ConfigParser()
			cfg.optionxform = str
			if not cfg.read(inifn):
				print "Settings file %s does not exist." % inifn
			else:
				self.enqueueForBackup(inifn)
				macros = self.getMacros(cfg, inifn)
				for m in macros:
					macroMap[m] = True

			eepFn = os.path.join(cmdFolder, "Printer", "settings.%s.eep" % pn)
			self.enqueueForBackup(eepFn, required=False)

		for m in macroMap.keys():
			self.enqueueForBackup(m)
		return self.bkQueue

bu = CfgBackup()
q = bu.backupQueue()

with zipfile.ZipFile('spam.zip', 'w') as myzip:
	for f in q:
		myzip.write(f)

z = zipfile.ZipFile('spam.zip', 'r')
print str(z.namelist())
z.close()
