import math
from gobject import gobject, layer, segment, ST_MOVE, ST_PRINT, ST_RETRACTION, ST_REV_RETRACTION;

class CNC:
	def __init__(self, acceleration, ht=0.2):
		self.curX = 0
		self.curY = 0
		self.curZ = 0
		self.curE = 0
		
		self.gObject = gobject()
		self.currentLayer = layer(0, 0)
		self.currentHeight = 0
		self.curTool = 0
		self.currentSegment = segment(0, self.curTool)
		self.currentSegmentType = 0
		self.recordPoint((0, 0), 0, ST_MOVE, 0, 0, 0, 0, 0)
		
		self.minERate = [999.9, 999.0, 999.0, 999.0]
		self.maxERate = [0.0, 0.0, 0.0, 0.0]
		self.maxTool = 0
		self.totalE = [0.0, 0.0, 0.0, 0.0]
		self.layerE = [0.0, 0.0, 0.0, 0.0]
		self.layerHt = ht
		self.ew = 0.56
		
		self.layerTimes = []
		self.layerTime = 0
		self.totalTime = 0.0
		
		self.minBedTemp = 999.0
		self.maxBedTemp = 0.0
		self.minHETemp = [999.0, 999.0, 999.0, 999.0]
		self.maxHETemp = [0, 0, 0, 0]
		
		self.speed = 0
		self.relative = False
		
		self.lastSpeed = 0.0
		self.lastDx = 0.0
		self.lastDy = 0.0
		
		self.acceleration = acceleration

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
			return self.dispatch[cmd](parms, sourceLine)
		elif cmd.startswith("T"):
			nt = int(cmd.strip()[1:])
			if nt > 0 and nt < 4:
				if nt != self.curTool:
					self.currentLayer.addSegment(self.currentSegment)
					self.curTool = nt
					self.currentSegment = segment(self.currentSegmentType, self.curTool)
					if self.curTool > self.maxTool:
						self.maxTool = self.curTool
			return 0
		else:
			return 0
		
	def moveFast(self, parms, sourceLine):
		return self.move(parms, sourceLine)
		
	def moveSlow(self, parms, sourceLine):
		return self.move(parms, sourceLine)
		
	def move(self, parms, sourceLine):
		x = self.curX
		y = self.curY
		z = self.curZ
		e = self.curE
		self.checkCoords(parms)
		
		self.lastSpeed = self.speed
		if 'F' in parms.keys():
			self.speed = float(parms["F"]) / 60.0
			
		eUsed = self.curE - e
		
		if eUsed == 0:
			st = ST_MOVE
		else:
			st = ST_PRINT
			
		dx = self.curX - x
		dy = self.curY - y
		dz = self.curZ - z
		
		calcTime = 0.0
		dist = math.hypot(dx, dy)
		if dist == 0 and dz == 0 and eUsed != 0:
			if eUsed > 0:
				st = ST_REV_RETRACTION
			else:
				st = ST_RETRACTION
				
		if dist != 0 and eUsed != 0 and st == ST_PRINT:
			w = eUsed/(dist*self.layerHt)
		else:
			w = 0.5
			
		self.recordPoint((self.curX, self.curY), self.curZ, st, sourceLine, e, eUsed, w, self.speed)

		if dx * self.lastDx + dy * self.lastDy <= 0:
			self.lastSpeed = 0
				
		de = self.curE - e
			
		if dist == 0:
			if dz > 0:
				dist = dz
			else:
				dist = de
				
		if self.speed == self.lastSpeed:
			calcTime = dist / self.speed if self.speed != 0 else 0
		else:
			d = 2 * abs(((self.speed + self.lastSpeed) * (self.speed - self.lastSpeed) * 0.5) / self.acceleration)
			if d <= dist and self.lastSpeed + self.speed != 0 and self.speed != 0:
				calcTime = 2 * d / (self.lastSpeed + self.speed)
				calcTime += (dist - d) / self.speed
			else:
				calcTime = 2 * dist / (self.lastSpeed + self.speed)  

		self.lastDx = dx
		self.lastDy = dy
			
		self.layerTime += calcTime
		self.totalTime += calcTime
		return calcTime
	
	def recordPoint(self, p, ht, st, sourceLine, eBefore, eUsed, lineWidth, speed):
		if ht != self.currentHeight:
			self.currentLayer.addSegment(self.currentSegment)
			self.gObject.addLayer(self.currentLayer)
			self.layerTimes.append(self.layerTime)
			self.layerTime = 0
			self.currentLayer = layer(ht, eBefore)
			self.currentHeight = ht
			self.currentSegment = segment(st, self.curTool)
			self.currentSegmentType = st
			self.currentSegment.addPoint(p, sourceLine, eUsed, lineWidth, speed)
			
		elif st != self.currentSegmentType:
			self.currentLayer.addSegment(self.currentSegment)
			self.currentSegment = segment(st, self.curTool)
			self.currentSegmentType = st
			self.currentSegment.addPoint(p, sourceLine, eUsed, lineWidth, speed)
			
		else:
			self.currentSegment.addPoint(p, sourceLine, eUsed, lineWidth, speed)
			
	def getGObject(self):
		self.currentLayer.addSegment(self.currentSegment);
		self.gObject.addLayer(self.currentLayer)
		self.layerTimes.append(self.layerTime)
		self.gObject.setMaxLine(self.sourceLine)
		
		hes = []
		for h in self.maxHETemp:
			if h == 0:
				hes.append(None)
			else:
				hes.append(h)
				
		self.gObject.setTemps(self.maxBedTemp, hes)
		return self.gObject
	
	def getMaxTool(self):
		return self.maxTool
	
	def getTimes(self):
		return self.totalTime, self.layerTimes
	
	def dwell(self, parms, sourceLine):
		ct = 0
		if 'P' in parms.keys():
			ct = float(parms['P'])/1000.0
		elif 'S' in parms.keys():
			ct = float(parms['S'])
		self.layerTime += ct
		self.totalTime += ct
		return ct
		
	def setInches(self, parms, sourceLine):
		return 0
		
	def setMillimeters(self, parms, sourceLine):
		return 0

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
			
		self.recordPoint((self.curX, self.curY), self.curZ, ST_MOVE, sourceLine, self.curE, 0, 0, 0)
		return 0
		
	def setAbsolute(self, parms, sourceLine):
		self.relative = False
		return 0
		
	def setRelative(self, parms, sourceLine):
		self.relative = True
		return 0
		
	def tempBed(self, parms, sourceLine):
		if 'S' in parms.keys():
			t = float(parms['S'])
			if t < self.minBedTemp and t != 0:
				self.minBedTemp = t
			if t > self.maxBedTemp:
				self.maxBedTemp = t
		return 0
		
	def tempHE(self, parms, sourceLine):
		if 'S' in parms.keys():
			t = float(parms['S'])
			if t < self.minHETemp[self.curTool] and t != 0:
				self.minHETemp[self.curTool] = t
			if t > self.maxHETemp[self.curTool]:
				self.maxHETemp[self.curTool] = t
		return 0
		
	def axisReset(self, parms, sourceLine):
		if 'X' in parms.keys():
			self.curX = float(parms['X'])
		if 'Y' in parms.keys():
			self.curY = float(parms['Y'])
		if 'Z' in parms.keys():
			self.curZ = float(parms['Z'])
		if 'E' in parms.keys():
			self.curE = float(parms['E'])
		return 0
	
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
		



