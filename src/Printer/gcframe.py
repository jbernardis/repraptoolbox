import wx, math
from gobject import ST_MOVE, ST_PRINT, ST_RETRACTION, ST_REV_RETRACTION

MAXZOOM = 10
ZOOMDELTA = 0.1
THICK_ADJUSTMENT = 2.0


def setColor(a,b):
		res = []
		for i in range(101):
				x = [a[j] - b[j] * i / 100 for j in range(3)]
				res.append(x)
		return res

dcMat = [setColor([255,0,0], [135,0,0]), setColor([253,111,17], [119,55,15]), setColor([253,245,30], [117,113,28])]

def printedColor(tool, distance):
		d = distance
		if d > 100:
				d = 100
		return dcMat[tool][d]

unprintedColor = ["blue", "green", "cyan"]

def colorByPos(distance, tool):
		if distance >= 0: # not yet printed
				return unprintedColor[tool]
		else:
				return printedColor(tool, -distance)
			
def triangulate(p1, p2):
	dx = p2[0] - p1[0]
	dy = p2[1] - p1[1]
	d = math.sqrt(dx*dx + dy*dy)
	return d

#orange = wx.Colour(237, 139, 33)
dk_Gray = wx.Colour(224, 224, 224)
lt_Gray = wx.Colour(128, 128, 128)
black = wx.Colour(0, 0, 0)

class GcFrame (wx.Window):
	def __init__(self, parent, model, settings):
		self.parent = parent
		self.log = self.parent.log
		self.scale = settings.scale
		self.zoom = 1
		self.offsety = 0
		self.offsetx = 0
		self.startPos = (0, 0)
		self.startOffset = (0, 0)
		self.buildarea = settings.buildarea
		self.model = None
		self.layerMap = []				
		self.currentlx = None
		self.printPosition = 0
		self.shiftX = 0
		self.shiftY = 0
		self.toolPathOnly = settings.toolpathonly
		
		self.movePen = wx.Pen(wx.Colour(0, 0, 0), 1)
		self.movePenPrinted = wx.Pen(wx.Colour(0, 0, 0), 2)
		self.backgroundPen = wx.Pen(wx.Colour(128, 128, 128), 1)

		self.showmoves = settings.showmoves
		self.showprevious = settings.showprevious
		self.syncWithPrint = True
		
		sz = [(x+1) * self.scale for x in self.buildarea]
		
		wx.Window.__init__(self,parent,size=sz)
		self.Show()
		
		self.initBuffer()
		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
		self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
		self.Bind(wx.EVT_MOTION, self.onMotion)
		self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel, self)

		if model != None:
			self.loadModel(model)
		
	def onSize(self, evt):
		self.initBuffer()
		
	def setShowMoves(self, flag=True):
		self.showmoves = flag
		self.redrawCurrentLayer()
		
	def setShowPrevious(self, flag=True):
		self.showprevious = flag
		self.redrawCurrentLayer()
		
	def setSyncWithPrint(self, flag=True):
		self.syncWithPrint = flag
		
	def setPrintPosition(self, position):
		if position == -1:
			self.printPosition = self.layerMap[-1][1]
		else:
			self.printPosition = position
		
		posLayer = None
		for lx in range(len(self.layerMap)):
			if self.layerMap[lx][0] <= self.printPosition and self.layerMap[lx][1] >= self.printPosition:
				posLayer = lx
				break
			
		if posLayer is None:
			self.log("Unable to determine layer for print position %d" % position)
			return
		
		if posLayer == self.currentlx:
			self.redrawCurrentLayer()
		elif self.syncWithPrint:
			self.setLayer(posLayer)
		
	def onPaint(self, evt):
		dc = wx.BufferedPaintDC(self, self.buffer)
		
	def onLeftDown(self, evt):
		self.startPos = evt.GetPosition()
		self.startOffset = (self.offsetx, self.offsety)
		self.CaptureMouse()
		self.SetFocus()
		
	def onLeftUp(self, evt):
		if self.HasCapture():
			self.ReleaseMouse()
			
	def onMotion(self, evt):
		if evt.Dragging() and evt.LeftIsDown():
			x, y = evt.GetPosition()
			dx = x - self.startPos[0]
			dy = y - self.startPos[1]
			self.offsetx = self.startOffset[0] - dx/(2*self.zoom)
			if self.offsetx < 0:
				self.offsetx = 0
			if self.offsetx > (self.buildarea[0]-self.buildarea[0]/self.zoom):
				self.offsetx = self.buildarea[0]-self.buildarea[0]/self.zoom
				
			self.offsety = self.startOffset[1] - dy/(2*self.zoom)
			if self.offsety < 0:
				self.offsety = 0
			if self.offsety > (self.buildarea[1]-self.buildarea[1]/self.zoom):
				self.offsety = self.buildarea[1]-self.buildarea[1]/self.zoom

			self.redrawCurrentLayer()
			
		evt.Skip()
		
	def onMouseWheel(self, evt):
		if evt.GetWheelRotation() < 0:
			self.zoomIn()
		else:
			self.zoomOut()
					
	def zoomIn(self):
		if self.zoom < MAXZOOM:
			zoom = self.zoom + ZOOMDELTA
			self.setZoom(zoom)

	def zoomOut(self):
		if self.zoom > 1:
			zoom = self.zoom - ZOOMDELTA
			self.setZoom(zoom)

	def loadModel(self, model, layer=0, zoom=1):
		self.model = model

		if model is None:
			self.currentlx = None
		else:
			self.currentlx = layer
		self.shiftX = 0
		self.shiftY = 0
		if not zoom is None:
			self.zoom = zoom
			if zoom == 1:
				self.offsetx = 0
				self.offsety = 0

		self.layerMap = []				
		if self.model is not None:
			for lx in range(len(self.model)):
				self.layerMap.append(self.model.getGCodeLines(lx))

		self.printPosition = 0
		self.redrawCurrentLayer()
		
	def initBuffer(self):
		w, h = self.GetClientSize();
		self.buffer = wx.EmptyBitmap(w, h)
		self.redrawCurrentLayer()
		
	def setLayer(self, lyr):
		if self.model is None:
			return
		if lyr < 0 or lyr >= self.model.layerCount():
			return
		if lyr == self.currentlx:
			return
		
		self.currentlx = lyr
		self.redrawCurrentLayer()
		
	def getCurrentLayer(self):
		return self.currentlx
	
	def getZoom(self):
		return self.zoom

	def setZoom(self, zoom):
		if zoom > self.zoom:
			oldzoom = self.zoom
			self.zoom = zoom
			cx = self.offsetx + self.buildarea[0]/oldzoom/2.0
			cy = self.offsety + self.buildarea[1]/oldzoom/2.0
			self.offsetx = cx - self.buildarea[0]/self.zoom/2.0
			self.offsety = cy - self.buildarea[1]/self.zoom/2.0
		else:
			oldzoom = self.zoom
			self.zoom = zoom
			cx = self.offsetx + self.buildarea[0]/oldzoom/2.0
			cy = self.offsety + self.buildarea[1]/oldzoom/2.0
			self.offsetx = cx - self.buildarea[0]/self.zoom/2.0
			self.offsety = cy - self.buildarea[1]/self.zoom/2.0
			if self.offsetx < 0:
				self.offsetx = 0
			if self.offsetx > (self.buildarea[0]-self.buildarea[0]/self.zoom):
				self.offsetx = self.buildarea[0]-self.buildarea[0]/self.zoom
				
			if self.offsety < 0:
				self.offsety = 0
			if self.offsety > (self.buildarea[1]-self.buildarea[1]/self.zoom):
				self.offsety = self.buildarea[1]-self.buildarea[1]/self.zoom

		self.redrawCurrentLayer()
		
	def setShift(self, sx, sy):
		self.shiftX = sx
		self.shiftY = sy
		self.redrawCurrentLayer()
		
	def setToolPathsOnly(self, flag):
		self.toolPathOnly = flag
		self.redrawCurrentLayer()
		
	def redrawCurrentLayer(self):
		dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)

		self.drawGraph(dc, self.currentlx)

		del dc
		self.Refresh()
		self.Update()
		
	def drawGraph(self, dc, lyr):
		dc.SetBackground(wx.Brush(wx.Colour(255, 255, 230)))
		dc.Clear()
		
		self.drawGrid(dc)
		self.drawLayer(dc, lyr)

	def drawGrid(self, dc):
		yleft = (0 - self.offsety)*self.zoom*self.scale
		if yleft < 0: yleft = 0

		yright = (self.buildarea[1] - self.offsety)*self.zoom*self.scale
		if yright > self.buildarea[1]*self.scale: yright = self.buildarea[1]*self.scale

		for x in range(0, self.buildarea[0]+1, 10):
			if x == 0 or x == self.buildarea[0]:
				dc.SetPen(wx.Pen(black, 1))
			elif x%50 == 0:
				dc.SetPen(wx.Pen(lt_Gray, 1))
			else:
				dc.SetPen(wx.Pen(dk_Gray, 1))
			x = (x - self.offsetx)*self.zoom*self.scale
			if x >= 0 and x <= self.buildarea[0]*self.scale:
				dc.DrawLine(x, yleft, x, yright)
			
		xtop = (0 - self.offsetx)*self.zoom*self.scale
		if xtop <1: xtop = 1

		xbottom = (self.buildarea[0] - self.offsetx)*self.zoom*self.scale
		if xbottom > self.buildarea[0]*self.scale: xbottom = self.buildarea[0]*self.scale

		for y in range(0, self.buildarea[1]+1, 10):
			if y == 0 or y == self.buildarea[1]:
				dc.SetPen(wx.Pen(black, 1))
			if y%50 == 0:
				dc.SetPen(wx.Pen(lt_Gray, 1))
			else:
				dc.SetPen(wx.Pen(dk_Gray, 1))
			y = (y - self.offsety)*self.zoom*self.scale
			if y >= 0 and y <= self.buildarea[1]*self.scale:
				dc.DrawLine(xtop, y, xbottom, y)
			
	def drawLayer(self, dc, lx):
		if lx is None:
			return
		
		pl = self.currentlx-1
		if pl>=0 and self.showprevious:
			self.drawOneLayer(dc, pl, background=True)
		
		self.drawOneLayer(dc, lx)
		
	def drawOneLayer(self, dc, lx, background=False):
		if lx is None:
			return
		
		layer = self.model[lx]

		lines = []
		pens = []
		lastPt = None
		for sg in layer:
			stype = sg.segmentType()
			widths = sg.getWidths()

			lineRefs = sg.getLineRefs()
			tool = sg.getTool()
			pts = [ self.transform(p[0], p[1]) for p in sg]

			if lastPt is not None:
				pts = [lastPt] + pts
			lastPt = pts[-1]

			if stype == ST_MOVE and not self.showmoves:
				continue

			if stype == ST_RETRACTION:
				continue

			if stype == ST_REV_RETRACTION:
				continue

			if len(pts) == 0:
				continue

			if len(pts) == 1:
				pts = [[pts[0][0], pts[0][1]], [pts[0][0], pts[0][1]]]
				
			pens.extend([self.getPen(widths[i], lineRefs[i], stype, background, tool) for i in range(len(widths))])
			lines.extend([[pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1]] for i in range(len(pts)-1)])
			pens = pens[:len(lines)]
			
		dc.DrawLineList(lines, pens)

	def getPen(self, width, lineref, segmentType, background, tool):
		if segmentType == ST_MOVE:
			if self.printPosition >= lineref:
				return self.movePenPrinted
			else:
				return self.movePen

		if background:
				return self.backgroundPen

		if self.toolPathOnly:
				w = 1
		else:
				w = width * self.zoom * self.scale * THICK_ADJUSTMENT
				
		return wx.Pen(colorByPos(lineref-self.printPosition, tool), w)	

	def transform(self, ptx, pty):
		x = (ptx - self.offsetx + self.shiftX)*self.zoom*self.scale
		y = (self.buildarea[1]-pty - self.offsety - self.shiftY)*self.zoom*self.scale
		return (x, y)
