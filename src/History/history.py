import os
import inspect
import pickle
import time

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))

from images import Images
from historyeventenum import HistoryEventEnum
from settings import Settings

MAX_HIST = 100

class HistoryFile:
	def __init__(self, fn):
		self.fn = fn
		self.refresh()
		
	def getFn(self):
		return self.fn
	
	def getModTime(self):
		return self.modTime
		
	def refresh(self):
		try:
			self.modTime = os.path.getmtime(self.fn)
		except:
			self.modTime = None # file most likely doesn't exist

class HistoryEvent:
	def __init__(self):
		self.timeStamp = time.time()
	
	def dump(self):
		print self.eventType, self.timeStamp, self.gcfn.getFn(), self.text
	
	def getEventType(self):
		return self.eventType
	
	def getEventTypeString(self):
		return HistoryEventEnum.label[self.eventType]
	
	def getTimeStamp(self):
		return self.timeStamp
	
	def getFns(self):
		return [ self.gcfn.getFn() ]
	
	def getString(self):
		return self.text
		
class SliceComplete (HistoryEvent):
	def __init__(self, gcfn, stlfn, slcfg, slfil, sltemp):
		HistoryEvent.__init__(self)
		self.eventType = HistoryEventEnum.SliceComplete
		self.gcfn = gcfn
		self.stlfn = stlfn
		self.slcfg = slcfg
		self.slfil = slfil
		self.sltemp = sltemp
		
	def dump(self):
		print self.eventType, self.timeStamp, self.gcfn.getFn(), self.stlfn.getFn(), self.slcfg, self.slfil, self.sltemp
		
	def getString(self):
		return "%s - %s" % (os.path.basename(self.stlfn.getFn()), self.slcfg)
	
	def getSlCfg(self):
		return self.slcfg
	
	def getFns(self):
		return [ self.gcfn.getFn(), self.stlfn.getFn() ]

class OpenEdit (HistoryEvent):
	def __init__(self, gcfn, txt):
		HistoryEvent.__init__(self)
		self.eventType = HistoryEventEnum.OpenEdit
		self.gcfn = gcfn
		self.text = txt

class FilamentChange (HistoryEvent):
	def __init__(self, gcfn, txt):
		HistoryEvent.__init__(self)
		self.eventType = HistoryEventEnum.FilamentChange
		self.gcfn = gcfn
		self.text = txt

class ShiftModel (HistoryEvent):
	def __init__(self, gcfn, txt):
		HistoryEvent.__init__(self)
		self.eventType = HistoryEventEnum.ShiftModel
		self.gcfn = gcfn
		self.text = txt

class TempChange (HistoryEvent):
	def __init__(self, gcfn, txt):
		HistoryEvent.__init__(self)
		self.eventType = HistoryEventEnum.TempChange
		self.gcfn = gcfn
		self.text = txt

class SpeedChange (HistoryEvent):
	def __init__(self, gcfn, txt):
		HistoryEvent.__init__(self)
		self.eventType = HistoryEventEnum.SpeedChange
		self.gcfn = gcfn
		self.text = txt

class PrintStarted (HistoryEvent):
	def __init__(self, gcfn, txt):
		HistoryEvent.__init__(self)
		self.eventType =  HistoryEventEnum.PrintStarted
		self.gcfn = gcfn
		self.text = txt

class PrintCompleted (HistoryEvent):
	def __init__(self, gcfn, txt):
		HistoryEvent.__init__(self)
		self.eventType = HistoryEventEnum.PrintCompleted
		self.gcfn = gcfn
		self.text = txt
	
class History:
	def __init__(self):
		self.fn = os.path.join(cmdFolder, "rrtb.history")
		self.images = Images(os.path.join(cmdFolder, "images"))
		self.settings = Settings(cmdFolder)
		self.reload()
		self.save()
		
	def reload(self):
		try:		
			fp = open(self.fn, "rb")
			(self.histFiles, self.events) = pickle.load(fp)
			fp.close()
			self.refreshAll()
		except:
			self.histFiles = {}
			self.events = []
		
	def save(self):
		fp = open(self.fn, 'wb')
		pickle.dump((self.histFiles, self.events), fp)
		fp.close()
		self.settings.save()
		
	def dump(self):
		print "Events:"
		for e in self.events:
			e.dump()
			
		print ""
		print "files:"
		for hf in self.histFiles.keys():
			print hf, " : ", self.histFiles[hf].getModTime()

	def refreshAll(self):
		for hk in self.histFiles.keys():
			self.histFiles[hk].refresh()
		self.save()
		
	def addFile(self, fn):
		if fn in self.histFiles.keys():
			hf = self.histFiles[fn]
			hf.refresh()
		else:
			hf = HistoryFile(fn)
			self.histFiles[fn] = hf
		return hf
	
	def addEvent(self, evt):
		self.events.append(evt)
		if len(self.events) > MAX_HIST:
			sx = len(self.events) - MAX_HIST
			self.events = self.events[sx:]
			self.prune()
		self.save()
			
	def prune(self):
		fns = []
		for e in self.events:
			fns.extend(e.getFns())
			
		dlist = []
		for f in self.histFiles.keys():
			if f not in fns:
				dlist.append(f)
				
		for f in dlist:
			del(self.histFiles[f])
	
	def __getitem__(self, ix):
		if ix < 0 or ix >= self.__len__():
			return None
		
		return self.events[ix]
	
	def __iter__(self):
		self.__eindex__ = 0
		return self
	
	def next(self):
		if self.__eindex__ < self.__len__():
			i = self.__eindex__
			self.__eindex__ += 1
			return self.events[i]

		raise StopIteration
	
	def __len__(self):
		return len(self.events)

