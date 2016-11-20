import math
from gobject import gobject, layer, segment, ST_MOVE, ST_PRINT, ST_RETRACTION, ST_REV_RETRACTION;

class CNC:
	def __init__(self):
		self.curX = 0
		self.curY = 0
		self.curZ = 0
		self.curE = 0
		
		self.gObject = gobject()
		self.currentLayer = layer(0, 0)
		self.currentHeight = 0
		self.currentSegment = segment(0)
		self.currentSegmentType = 0
		self.recordPoint((0, 0), 0, ST_MOVE, 0, 0)
		
		self.minERate = [999.9, 999.0]
		self.maxERate = [0.0, 0.0]
		self.curTool = 0
		self.maxTool = 0
		self.totalE = [0.0, 0.0]
		self.layerHt = 0.0
		self.ew = 0.56
		
		self.minBedTemp = 999.0
		self.maxBedTemp = 0.0
		self.minHETemp = [999.0, 999.0, 999.0, 999.0]
		self.maxHETemp = [0, 0, 0, 0]
		
		self.speed = 0
		self.relative = False

		self.dispatch = {
			"G0": self.moveFast,
			"G1": self.moveSlow,
			"G4": self.dwell,
			"G20": self.setInches,
			"G21": self.setMillimeters,
			"G28": self.home,
			"G90": self.setAbsolute,
			"G91": self.setRelative,
			"G92": self.axisReset,
			"M140": self.tempBed,
			"M190": self.tempBed,
			"M104": self.tempHE,
			"M109": self.tempHE,
			}
		
	def execute(self, cmd, parms, sourceLine):
		self.sourceLine = sourceLine
		if cmd in self.dispatch.keys():
			self.dispatch[cmd](parms, sourceLine)
		elif cmd.startswith("T"):
			nt = int(cmd.strip()[1:])
			if nt > 0 and nt < 4:
				self.curTool = nt
				if self.curTool > self.maxTool:
					self.maxTool = self.curTool
		else:
			pass
		
	def moveFast(self, parms, sourceLine):
		self.move(parms, sourceLine)
		
	def moveSlow(self, parms, sourceLine):
		self.move(parms, sourceLine)
		
	def move(self, parms, sourceLine):
		x = self.curX
		y = self.curY
		z = self.curZ
		e = self.curE
		self.checkCoords(parms)
		if 'F' in parms.keys():
			self.speed = float(parms["F"])
			
		eUsed = self.curE - e
		
		if eUsed == 0:
			st = ST_MOVE
		else:
			st = ST_PRINT
			
		dz = self.curZ - z
			
		dist = math.hypot(self.curX - x, self.curY - y)
		if dist == 0 and dz == 0 and eUsed != 0:
			if eUsed > 0:
				st = ST_REV_RETRACTION
			else:
				st = ST_RETRACTION
			
		self.recordPoint((self.curX, self.curY), self.curZ, st, sourceLine, e)
	
	def recordPoint(self, p, ht, st, sourceLine, eBefore):
		if ht != self.currentHeight:
			self.currentLayer.addSegment(self.currentSegment)
			self.gObject.addLayer(self.currentLayer)
			self.currentLayer = layer(ht, eBefore)
			self.currentHeight = ht
			self.currentSegment = segment(st)
			self.currentSegmentType = st
			self.currentSegment.addPoint(p, sourceLine)
			
		elif st != self.currentSegmentType:
			self.currentLayer.addSegment(self.currentSegment)
			self.currentSegment = segment(st)
			self.currentSegmentType = st
			self.currentSegment.addPoint(p, sourceLine)
			
		else:
			self.currentSegment.addPoint(p, sourceLine)
			
	def getGObject(self):
		self.currentLayer.addSegment(self.currentSegment);
		self.gObject.addLayer(self.currentLayer)
		self.gObject.setMaxLine(self.sourceLine)
		
		hes = []
		for h in self.maxHETemp:
			if h == 0:
				hes.append(None)
			else:
				hes.append(h)
				
		self.gObject.setTemps(self.maxBedTemp, hes)
		return self.gObject
	
	def dwell(self, parms, sourceLine):
		pass
		
	def setInches(self, parms, sourceLine):
		pass
		
	def setMillimeters(self, parms, sourceLine):
		pass

	def home(self, parms, sourceLine):
		naxes = 0
		if 'X' in parms.keys():
			self.curX = 0
			naxes += 1
		if 'Y' in parms.keys():
			self.curY = 0
			naxes += 1
		if 'Z' in parms.keys():
			self.curZ = 0
			naxes += 1
			
		if naxes == 0:
			self.curX = 0
			self.curY = 0
			self.curZ = 0
			
		self.recordPoint((self.curX, self.curY), self.curZ, ST_MOVE, sourceLine, self.curE)
		
	def setAbsolute(self, parms, sourceLine):
		self.relative = False
		
	def setRelative(self, parms, sourceLine):
		self.relative = True
		
	def tempBed(self, parms, sourceLine):
		if 'S' in parms.keys():
			t = float(parms['S'])
			if t < self.minBedTemp and t != 0:
				self.minBedTemp = t
			if t > self.maxBedTemp:
				self.maxBedTemp = t
		
	def tempHE(self, parms, sourceLine):
		if 'S' in parms.keys():
			t = float(parms['S'])
			if t < self.minHETemp[self.curTool] and t != 0:
				self.minHETemp[self.curTool] = t
			if t > self.maxHETemp[self.curTool]:
				self.maxHETemp[self.curTool] = t
		
	def axisReset(self, parms, sourceLine):
		if 'X' in parms.keys():
			self.curX = float(parms['X'])
		if 'Y' in parms.keys():
			self.curY = float(parms['Y'])
		if 'Z' in parms.keys():
			self.curZ = float(parms['Z'])
		if 'E' in parms.keys():
			self.curE = float(parms['E'])
	
	def checkCoords(self, parms):
		if self.relative:
			if 'X' in parms.keys():
				self.curX += float(parms["X"])
			if 'Y' in parms.keys():
				self.curY += float(parms["Y"])
			if 'Z' in parms.keys():
				self.curZ += float(parms["Z"])
			if 'E' in parms.keys():
				self.curE += float(parms["E"])
		else:
			if 'X' in parms.keys():
				self.curX = float(parms["X"])
			if 'Y' in parms.keys():
				self.curY = float(parms["Y"])
			if 'Z' in parms.keys():
				self.curZ = float(parms["Z"])
			if 'E' in parms.keys():
				self.curE = float(parms["E"])
		



