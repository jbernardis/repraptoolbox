import os
import inspect
import pickle
import time

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))

from historyeventenum import HistoryEventEnum

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
	
	def getEventType(self):
		return self.eventType
	
	def getFns(self):
		return [ self.gcfn.getFn() ]
		
class SliceComplete (HistoryEvent):
	def __init__(self, gcfn, stlfn, slcfg, slfil, sltemp):
		HistoryEvent.__init__(self)
		self.eventType = HistoryEventEnum.SliceComplete
		self.gcfn = gcfn
		self.stlfn = stlfn
		self.slcfg = slcfg
		self.slfil = slfil
		self.sltemp = sltemp
		
	def getString(self):
		pass
	
	def getFns(self):
		return [ self.gcfn.getFn(), self.stlfn.getFn() ]

class OpenEdit (HistoryEvent):
	def __init__(self, gcfn, txt):
		HistoryEvent.__init__(self)
		self.eventType = HistoryEventEnum.OpenEdit
		self.gcfn = gcfn
		self.text = txt
		
	def getString(self):
		pass

class FilamentChange (HistoryEvent):
	def __init__(self, gcfn, txt):
		HistoryEvent.__init__(self)
		self.eventType = HistoryEventEnum.FilamentChange
		self.gcfn = gcfn
		self.text = txt
		
	def getString(self):
		pass

class ShiftModel (HistoryEvent):
	def __init__(self, gcfn, txt):
		HistoryEvent.__init__(self)
		self.eventType = HistoryEventEnum.ShiftModel
		self.gcfn = gcfn
		self.text = txt
		
	def getString(self):
		pass

class TempChange (HistoryEvent):
	def __init__(self, gcfn, txt):
		HistoryEvent.__init__(self)
		self.eventType = HistoryEventEnum.TempChange
		self.gcfn = gcfn
		self.text = txt
		
	def getString(self):
		pass

class SpeedChange (HistoryEvent):
	def __init__(self, gcfn, txt):
		HistoryEvent.__init__(self)
		self.eventType = HistoryEventEnum.SpeedChange
		self.gcfn = gcfn
		self.text = txt
		
	def getString(self):
		pass

class PrintStarted (HistoryEvent):
	def __init__(self, gcfn, txt):
		HistoryEvent.__init__(self)
		self.eventType =  HistoryEventEnum.PrintStarted
		self.gcfn = gcfn
		self.text = txt
		
	def getString(self):
		pass

class PrintCompleted (HistoryEvent):
	def __init__(self, gcfn, txt):
		HistoryEvent.__init__(self)
		self.eventType = HistoryEventEnum.PrintCompleted
		self.gcfn = gcfn
		self.text = txt
		
	def getString(self):
		pass
	
class History:
	def __init__(self):
		self.fn = os.path.join(cmdFolder, "rrtb.history")
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
		
	def refreshAll(self):
		for hk in self.histFiles.keys():
			self.histFiles[hk].refresh()
		
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
			sx = MAX_HIST - len(self.events)
			self.events = self.events[sx:]
			self.prune()
			
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

