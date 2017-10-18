import math

ST_MOVE = 0
ST_RETRACTION = -1
ST_REV_RETRACTION = -2
ST_PRINT = 1

class segment:
	def __init__(self, stype, tool):
		self.points = []
		self.lineRef = []
		self.widths = []
		self.speeds = []
		self.stype = stype
		self.tool = tool
		self.eUsed = 0
		self.xmin = 99999
		self.xmax = -99999
		self.ymin = 99999
		self.ymax = -99999
		
	def addPoint(self, p, lineNbr, eUsed, width, speed):
		self.eUsed += eUsed
		if p[0] < self.xmin: self.xmin = p[0]
		if p[0] > self.xmax: self.xmax = p[0]
		if p[1] < self.ymin: self.ymin = p[1]
		if p[1] > self.ymax: self.ymax = p[1]
		self.points.append(p)
		self.lineRef.append(lineNbr)
		self.widths.append(width)
		self.speeds.append(speed)
		
	def getPointsBetween(self, bracket):
		result = []
		for i in range(len(self.lineRef)):
			lx = self.lineRef[i]
			if lx < bracket[0]: continue
			if lx > bracket[1]: break
			result.append(self.points[i])
			
		return result
		
	def hasLineNbr(self, ln):
		if ln is None:
			return False
		if len(self.lineRef) == 0:
			return False
		
		return self.lineRef[0] <= ln and ln <= self.lineRef[-1]
	
	def getHilitedPoint(self, ln):
		for i in range(len(self.points)):
			if self.lineRef[i] == ln:
				if i == 0:
					return [self.points[i]]
				else:
					return [self.points[i-1], self.points[i]]
			
		return None
		
	def segmentLength(self):
		return len(self.points)
	
	def segmentType(self):
		return self.stype
	
	def getTool(self):
		return self.tool
	
	def getWidths(self):
		return self.widths
	
	def getLineRefs(self):
		return self.lineRef
	
	def getSpeeds(self):
		return self.speeds
	
	def getFilament(self):
		return self.tool, self.eUsed
	
	def getFirstLine(self):
		if len(self.lineRef) == 0:
			return None
		return self.lineRef[0]
	
	def getLastLine(self):
		if len(self.lineRef) == 0:
			return None
		return self.lineRef[-1]
	
	def __getitem__(self, ix):
		if ix < 0 or ix >= self.__len__():
			return None
		
		return self.points[ix]
	
	def __iter__(self):
		self.__lindex__ = 0
		return self
	
	def next(self):
		if self.__lindex__ < self.__len__():
			i = self.__lindex__
			self.__lindex__ += 1
			return self.points[i]

		raise StopIteration
	
	def __len__(self):
		return len(self.points)
	
class layer:
	def __init__(self, height, starte):
		self.height = height
		self.starte = starte
		self.segments = []
		self.xmin = 99999
		self.xmax = -99999
		self.ymin = 99999
		self.ymax = -99999
		self.printSegments = 0
		self.eUsed = [0.0, 0.0, 0.0, 0.0]
		
	def addSegment(self, segment):
		if segment.segmentType() == ST_PRINT:
			self.printSegments += 1
			if segment.xmax > self.xmax: self.xmax = segment.xmax
			if segment.xmin < self.xmin: self.xmin = segment.xmin
			if segment.ymax > self.ymax: self.ymax = segment.ymax
			if segment.ymin < self.ymin: self.ymin = segment.ymin
			
		self.segments.append(segment)
		t, e = segment.getFilament()
		self.eUsed[t] += e
		
	def getFilament(self):
		return self.eUsed
		
	def getPointsBetween(self, bracket):
		result = []
		for sg in self.segments:
			result.extend(sg.getPointsBetween(bracket))
		return result
		
	def segmentCount(self):
		return len(self.segments)
	
	def getFirstLine(self):
		if len(self.segments) == 0:
			return 0
		
		return self.segments[0].getFirstLine()
	
	def printHeight(self):
		return self.height
	
	def minMaxXY(self):
		return self.xmin, self.ymin, self.xmax, self.ymax
	
	def startingE(self):
		return self.starte
	
	def __getitem__(self, ix):
		if ix < 0 or ix >= self.__len__():
			return None
		
		return self.segments[ix]
	
	def __iter__(self):
		self.__lindex__ = 0
		return self
	
	def next(self):
		if self.__lindex__ < self.__len__():
			i = self.__lindex__
			self.__lindex__ += 1
			return self.segments[i]

		raise StopIteration
	
	def __len__(self):
		return len(self.segments)		
	
class gobject:
	def __init__(self):
		self.xmin = 99999
		self.xmax = -99999
		self.ymin = 99999
		self.ymax = -99999
		self.maxLine = 0
		self.layers = []
		self.filamentLayers = None
		self.eUsed = [0.0, 0.0, 0.0, 0.0]
		
	def setMaxLine(self, mxl):
		self.maxLine = mxl
		
	def getMaxLine(self):
		return self.maxLine
		
	def addLayer(self, layer):
		if layer.printSegments > 0:
			if layer.xmax > self.xmax: self.xmax = layer.xmax
			if layer.xmin < self.xmin: self.xmin = layer.xmin
			if layer.ymax > self.ymax: self.ymax = layer.ymax
			if layer.ymin < self.ymin: self.ymin = layer.ymin
		self.layers.append(layer)
		le = layer.getFilament()
		for i in range(len(self.eUsed)):
			self.eUsed[i] += le[i]
			
	def getFilament(self):
		return self.eUsed
	
	def getLayerFilament(self, lx):
		if self.filamentLayers is None:
			self.filamentLayers = [self.layers[x].getFilament() for x in range(len(self.layers))]
			
		if len(self.layers) <= lx:
			return None
		
		priorUsed = [0.0, 0.0, 0.0, 0.0]
		for lyx in range(lx):
			for fx in range(4):
				priorUsed[fx] += self.filamentLayers[lyx][fx]

		afterUsed = [0.0, 0.0, 0.0, 0.0]
		for lyx in range(lx+1, len(self.layers)):
			for fx in range(4):
				afterUsed[fx] += self.filamentLayers[lyx][fx]
		
		return self.filamentLayers[lx], priorUsed, afterUsed
		
	def layerCount(self):
		return len(self.layers)
	
	def getGCodeLines(self, lx):
		if len(self.layers) <= lx:
			return None, None
		
		if lx == 0:
			first = 0
		else:
			first = self.layers[lx].getFirstLine()
			
		if lx >= len(self.layers)-1:
			last = self.maxLine
		else:
			last = self.layers[lx+1].getFirstLine() - 1
			
		return first, last
	
	def getLayerHeight(self, lx):
		if len(self.layers) <= lx:
			return None
		
		return self.layers[lx].printHeight()
	
	def getLayerMinMaxXY(self, lx):
		if len(self.layers) <= lx:
			return None, None, None, None
		
		return self.layers[lx].minMaxXY()
	
	def getTemps(self):
		return (self.bed, self.hes)
	
	def setTemps(self, bed, hes):
		self.bed = bed
		self.hes = hes
	
	def __getitem__(self, ix):
		if ix < 0 or ix >= self.__len__():
			return None
		
		return self.layers[ix]
	
	def __iter__(self):
		self.__lindex__ = 0
		return self
	
	def next(self):
		if self.__lindex__ < self.__len__():
			i = self.__lindex__
			self.__lindex__ += 1
			return self.layers[i]

		raise StopIteration
	
	def __len__(self):
		return len(self.layers)
