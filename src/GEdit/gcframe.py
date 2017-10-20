import wx, math
from gobject import ST_MOVE, ST_RETRACTION, ST_REV_RETRACTION

MAXZOOM = 10
ZOOMDELTA = 0.1

RETRACTION_WIDTH = 8
PRINT_WIDTH = 1
			
def triangulate(p1, p2):
	dx = p2[0] - p1[0]
	dy = p2[1] - p1[1]
	d = math.sqrt(dx*dx + dy*dy)
	return d

dk_Gray = wx.Colour(224, 224, 224)
lt_Gray = wx.Colour(128, 128, 128)
black = wx.Colour(0, 0, 0)

RETRACTIONCOLOR = wx.Colour(45, 222, 222)
REVRETRACTIONCOLOR = wx.Colour(196, 28, 173)
PRINTCOLOR = [wx.Colour(37, 61, 180), wx.Colour(42, 164, 105), wx.Colour(229, 129, 34), wx.Colour(224, 55, 38)]

class GcFrame (wx.Window):
	def __init__(self, parent, model, settings):
		self.parent = parent
		self.scale = settings.scale
		self.zoom = 1
		self.offsety = 0
		self.offsetx = 0
		self.startPos = (0, 0)
		self.startOffset = (0, 0)
		self.buildarea = settings.buildarea
		self.model = None
		self.currentlx = None
		self.shiftX = 0
		self.shiftY = 0
		
		self.bracket = [None, None]
		
		self.hiliteLine = 0;
		self.hilitePen1 = wx.Pen(wx.Colour(255, 255, 0), 6)
		self.hilitePen2 = wx.Pen(wx.Colour(255, 255, 255), 1)
		self.movePen = wx.Pen(wx.Colour(0, 0, 0), 1)
		self.backgroundPen = wx.Pen(wx.Colour(128, 128, 128), 1)
		self.bracketPen = wx.Pen(wx.Colour(255, 128, 0), 2)

		self.showmoves = settings.showmoves
		self.showprevious = settings.showprevious
		self.showretractions = settings.showretractions
		self.showrevretractions = settings.showrevretractions
		self.hilitetool = None
		
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
		
	def setShowRetractions(self, flag=True):
		self.showretractions = flag
		self.redrawCurrentLayer()
		
	def setShowRevRetractions(self, flag=True):
		self.showrevretractions = flag
		self.redrawCurrentLayer()
		
	def setHilightTool(self, tool):
		self.hilitetool = tool
		self.redrawCurrentLayer()
		
	def onPaint(self, evt):
		dc = wx.BufferedPaintDC(self, self.buffer)  # @UnusedVariable
		
	def onLeftDown(self, evt):
		self.startPos = evt.GetPositionTuple()
		self.startOffset = (self.offsetx, self.offsety)
		self.CaptureMouse()
		self.SetFocus()
		
	def onLeftUp(self, evt):
		if self.HasCapture():
			self.ReleaseMouse()
			
	def onMotion(self, evt):
		if evt.Dragging() and evt.LeftIsDown():
			x, y = evt.GetPositionTuple()
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
		self.hiliteLine = None
		self.bracket = [None, None]

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

		self.redrawCurrentLayer()
		
	def reportSelectedLine(self, ln):
		self.hiliteLine = ln
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
		
		self.hiliteLine = None
		self.bracket = [None, None]
		self.currentlx = lyr
		self.redrawCurrentLayer()
		
	def setBracket(self, b):
		self.bracket = b
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
		hpts = None
		for sg in layer:
			if not background and sg.hasLineNbr(self.hiliteLine):
				p = sg.getHilitedPoint(self.hiliteLine)
				if p is not None:
					if len(p) == 1:
						p0 = self.transform(p[0][0], p[0][1])
						if lastPt is None:
							hpts = [p0, p0]
						else:
							hpts = [lastPt, p0]
					else:
						hpts = [self.transform(pt[0], pt[1]) for pt in p]
			
			stype = sg.segmentType()
			speeds = sg.getSpeeds()
			tool = sg.getTool()
			pts = [ self.transform(p[0], p[1]) for p in sg]

			if lastPt is not None:
				pts = [lastPt] + pts
					
			lastPt = pts[-1]

			if stype == ST_MOVE and not self.showmoves:
				continue

			if stype == ST_RETRACTION and not self.showretractions:
				continue

			if stype == ST_REV_RETRACTION and not self.showrevretractions:
				continue

			if len(pts) == 0:
				continue

			if len(pts) == 1:
				pts = [[pts[0][0], pts[0][1]], [pts[0][0], pts[0][1]]]
				
			pens.extend([self.getPen(speeds[i], stype, background, tool) for i in range(len(speeds))])
			lines.extend([[pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1]] for i in range(len(pts)-1)])
			pens = pens[:len(lines)]
			
		dc.DrawLineList(lines, pens)

		if self.bracket[0] is not None and self.bracket[1] is not None:
			npt = layer.getPointsBetween(self.bracket)
			if npt is not None and len(npt) > 1:
				dc.SetPen(self.bracketPen)
				dc.DrawLines([self.transform(p[0], p[1]) for p in npt])
			
		if hpts is not None:
			dc.SetPen(self.hilitePen1)
			dc.DrawLine(hpts[0][0], hpts[0][1], hpts[1][0], hpts[1][1])
			dc.SetPen(self.hilitePen2)
			dc.DrawLine(hpts[0][0], hpts[0][1], hpts[1][0], hpts[1][1])

	def getPen(self, speed, segmentType, background, tool):
		if segmentType == ST_MOVE:
			return self.movePen

		if background:
				return self.backgroundPen
				
		if self.hilitetool is not None:
			if self.hilitetool == tool:
				if segmentType == ST_RETRACTION:
					c = RETRACTIONCOLOR
					w = RETRACTION_WIDTH
				elif segmentType == ST_REV_RETRACTION:
					c = REVRETRACTIONCOLOR
					w = RETRACTION_WIDTH
				else:
					c = self.colorBySpeed(speed)
					w = PRINT_WIDTH
			else:
				c = wx.Colour(0, 0, 0)
				if segmentType == ST_RETRACTION:
					w = RETRACTION_WIDTH
				elif segmentType == ST_REV_RETRACTION:
					w = RETRACTION_WIDTH
				else:
					w = PRINT_WIDTH
		else:
			if segmentType == ST_RETRACTION:
				c = RETRACTIONCOLOR
				w = RETRACTION_WIDTH
			elif segmentType == ST_REV_RETRACTION:
				c = REVRETRACTIONCOLOR
				w = RETRACTION_WIDTH
			else:
				c = self.colorBySpeed(speed)
				w = PRINT_WIDTH
			
		return wx.Pen(c, w)	
	
	def colorBySpeed(self, speed):
		if speed < 20:
			return PRINTCOLOR[0]
		
		if speed < 40:
			return PRINTCOLOR[1]
		
		if speed < 60:
			return PRINTCOLOR[2]
		
		return PRINTCOLOR[3]
		
	def transform(self, ptx, pty):
		x = (ptx - self.offsetx + self.shiftX)*self.zoom*self.scale
		y = (self.buildarea[1]-pty - self.offsety - self.shiftY)*self.zoom*self.scale
		return (x, y)
