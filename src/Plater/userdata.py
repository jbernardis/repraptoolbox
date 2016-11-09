class UserData:
	def __init__(self, fn, stlObj, seq):
		self.fn = fn
		self.stlObj = stlObj
		self.seq = seq
		self.part = None
		self.formObjectName()
		
	def formObjectName(self):
		self.name = self.fn
		if not self.part is None:
			self.name += " - Part %s " % self.part
		self.name += " (Object %d)" % self.seq
			
	def setPart(self, part):
		self.part = part
		self.formObjectName()
	
	def getName(self):
		return self.name
		
	def getFn(self):
		return self.fn
		
	def clone(self, seq):
		s = self.stlObj.clone()
		return UserData(self.fn, s, seq)
	
	def getStlObj(self):
		return self.stlObj
	
	def setStlObj(self, stlObj):
		self.stlObj = stlObj
		
	def getSeqNbr(self):
		return self.seq
