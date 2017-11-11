import wx, math

from map import Map

buildarea = [200, 200]
scale = 2

clrNormal = '#008000'
clrSelected = '#00f400'

def worldToScreen(ptx, pty):
	x = ptx * scale
	y = (buildarea[1] - pty )* scale
	return (x, y)

def screenToWorld(ptx, pty):
	x = ptx / scale
	y = buildarea[1] - pty / scale
	return (x, y)

class Hull:
	def __init__(self, stlObj, seq):
		self.stlObj = stlObj
		self.seq = seq
		#self.transx = self.transy = 0
		
		self.refresh()

	def commitDeltas(self):
		self.stlObj.applyDeltas()
		
		self.ptsWorld = self.stlObj.hull
		self.ptsScreen = [worldToScreen(x[0], x[1]) for x in self.stlObj.hull]
		
	def refresh(self):
		self.ptsWorld = self.stlObj.hull
		self.ptsScreen = [worldToScreen(x[0], x[1]) for x in self.ptsWorld]
		self.recalculate()
		
	def recalculate(self):
		self.minx = 99999
		self.maxx = -99999
		self.miny = 99999
		self.maxy = -99999
		for p in self.ptsWorld:
			if p[0] > self.maxx: self.maxx = p[0]
			if p[0] < self.minx: self.minx = p[0]
			if p[1] > self.maxy: self.maxy = p[1]
			if p[1] < self.miny: self.miny = p[1]
		
		self.centerx = (self.maxx + self.minx)/2.0
		self.centery = (self.maxy + self.miny)/2.0
		self.width = self.maxx - self.minx
		self.height = self.maxy - self.miny
		self.area = self.width * self.height
		
	def translate(self, dx, dy):
		self.stlObj.deltaTranslation(dx, dy)
				
		for p in self.ptsWorld:
			p[0] += dx
			p[1] += dy
		self.ptsScreen = [worldToScreen(x[0], x[1]) for x in self.ptsWorld]
			
		self.minx += dx
		self.maxx += dx
		self.centerx += dx
		
		self.miny += dy
		self.maxy += dy
		self.centery += dy
		
	def rotate(self, da):
		self.stlObj.deltaRotation(da)
		rads = math.radians(da)
		cos = math.cos(rads)
		sin = math.sin(rads)
		
		ptsNew = []
		self.minx = self.miny = 99999
		self.maxx = self.maxy = -99999
		for p in self.ptsWorld:
			xp = (p[0]-self.centerx)*cos - (p[1]-self.centery)*sin + self.centerx
			if xp < self.minx: self.minx=xp
			if xp > self.maxx: self.maxx=xp
			
			yp = (p[0]-self.centerx)*sin + (p[1]-self.centery)*cos + self.centery
			if yp < self.miny: self.miny=yp
			if yp > self.maxy: self.maxy=yp
			ptsNew.append([xp, yp])
			
		self.ptsWorld = ptsNew
		self.ptsScreen = [worldToScreen(x[0], x[1]) for x in self.ptsWorld]
		self.centerx = (self.maxx + self.minx)/2.0
		self.centery = (self.maxy + self.miny)/2.0
		self.width = self.maxx - self.minx
		self.height = self.maxy - self.miny
		self.area = self.width * self.height
		
	def translatexy(self, dx, dy):
		self.stlObj.deltaTranslation(dx, dy)
		
		ptsNew = []
		self.minx = self.miny = 99999
		self.maxx = self.maxy = -99999
		for p in self.ptsWorld:
			xp = p[0] + dx
			if xp < self.minx: self.minx=xp
			if xp > self.maxx: self.maxx=xp
			
			yp = p[1] + dy
			if yp < self.miny: self.miny=yp
			if yp > self.maxy: self.maxy=yp
			ptsNew.append([xp, yp])
			
		self.ptsWorld = ptsNew
		self.ptsScreen = [worldToScreen(x[0], x[1]) for x in self.ptsWorld]
		self.centerx = (self.maxx + self.minx)/2.0
		self.centery = (self.maxy + self.miny)/2.0
		self.width = self.maxx - self.minx
		self.height = self.maxy - self.miny
		self.area = self.width * self.height
		
	def scalexyz(self, sx, sy, sz):
		self.stlObj.applyDeltas()
		self.stlObj.scalexyz(sx, sy, sz)
		
		self.ptsWorld = self.stlObj.hull
		self.ptsScreen = [worldToScreen(x[0], x[1]) for x in self.ptsWorld]
		
		self.recalculate()
		
	def yzMirror(self):
		self.stlObj.applyDeltas()
		self.stlObj.yzmirror()
		
		self.ptsWorld = self.stlObj.hull
		self.ptsScreen = [worldToScreen(x[0], x[1]) for x in self.stlObj.hull]
		
		self.recalculate()
		
	def xzMirror(self):
		self.stlObj.applyDeltas()
		self.stlObj.xzmirror()
		
		self.ptsWorld = self.stlObj.hull
		self.ptsScreen = [worldToScreen(x[0], x[1]) for x in self.stlObj.hull]
		
		self.recalculate()
		
	def xyMirror(self):
		self.stlObj.applyDeltas()
		self.stlObj.xymirror()
		
		self.ptsWorld = self.stlObj.hull
		self.ptsScreen = [worldToScreen(x[0], x[1]) for x in self.stlObj.hull]
		self.recalculate()
		
	def xyRotate(self, xa, ya):
		self.stlObj.applyDeltas()
		self.stlObj.rotatexy(xa, ya)
		
		self.ptsWorld = self.stlObj.hull
		self.ptsScreen = [worldToScreen(x[0], x[1]) for x in self.stlObj.hull]
		
		self.recalculate()
					
dk_Gray = wx.Colour(224, 224, 224)
lt_Gray = wx.Colour(128, 128, 128)
black = wx.Colour(0, 0, 0)

class StlFrame (wx.Window):
	def __init__(self, parent, settings):
		self.parent = parent
		self.settings = settings
		
		global buildarea
		global scale
		buildarea = self.settings.buildarea
		scale = self.settings.scale
		
		self.startPos = None
		self.hulls = []
		self.selectedSeq = None
		self.selectedHull = None
		
		sz = [(x+1) * scale for x in buildarea]
		
		wx.Window.__init__(self,parent,size=sz)
		
		self.initBuffer()
		
		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
		self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
		self.Bind(wx.EVT_MOTION, self.onMotion)
		self.Bind(wx.EVT_LEFT_DCLICK, self.onLeftDClick)
		self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel, self)

	def setSelection(self, seq):
		for h in self.hulls:
			if h.seq == seq:
				self.selectHull(h)
				self.refresh()
				return
			
	def commitDeltas(self, h):
		if h is None:
			h = self.selectedHull
		if h is None:
			return
		
		#self.transx = self.transy = 0
		h.commitDeltas()
			
	def selectHull(self, h):
		self.commitDeltas(None)

		self.selectedHull = h
		if h is None:
			self.selectedSeq = None
		else:
			self.selectedSeq = h.seq
			
	def findHullBySeq(self, seq):
		for h in self.hulls:
			if seq == h.seq:
				return h
			
		return None
			
	def addHull(self, stlObj, seq):
		h = Hull(stlObj, seq)
		self.hulls.append(h)
		self.selectHull(h)
		self.refresh()
		
	def refreshHull(self, seq):
		h = self.findHullBySeq(seq)
		if h is None: return
		
		h.refresh()
		self.refresh()
		
		
	def delHull(self, seq):
		nh = []
		for h in self.hulls:
			if h.seq != seq:
				nh.append(h)

		self.hulls = nh
		self.selectHull(None)
		self.refresh()

	def delAllHulls(self):
		self.hulls = []
		self.selectHull(None)
		self.refresh()
		
	def findClosest(self, ptx, pty):
		matchHull = None
		if len(self.hulls) == 0:
			return None
		
		for h in self.hulls:
			d = math.hypot(h.centerx-ptx, h.centery-pty)
			dx = math.fabs(h.centerx-ptx)
			dy = math.fabs(h.centery-pty)
			if dx < h.width/2 and dy < h.height/2:
				matchHull = h
		
		return matchHull
		
	def onLeftDown(self, evt):
		pos = evt.GetPosition()
		x, y = screenToWorld(pos[0], pos[1])
		self.startPos = [x, y]
		h = self.findClosest(x, y)
		if not h is None:
			if h.seq != self.selectedSeq:
				self.selectHull(h)
				self.parent.setFilesSelection(h.seq)
				self.refresh()
			
		self.CaptureMouse()
		self.SetFocus()
		
	def onLeftDClick(self, evt):
		if self.selectedHull is None:
			return
		
		pos = evt.GetPosition()
		x, y = screenToWorld(pos[0], pos[1])
		h = self.selectedHull
		h.translate(x-h.centerx, y-h.centery)
		self.refresh()
		
	def onLeftUp(self, evt):
		self.startPos = None
		if self.HasCapture():
			self.ReleaseMouse()
			
	def onMotion(self, evt):
		if evt.Dragging() and evt.LeftIsDown() and self.startPos != None:
			pos = evt.GetPosition()
			x, y = screenToWorld(pos[0], pos[1])
			dx = x - self.startPos[0]
			dy = y - self.startPos[1]

			self.startPos[0] = x
			self.startPos[1] = y 
			
			if not self.selectedHull is None:
				self.selectedHull.translate(dx, dy)
				self.refresh()
			
		evt.Skip()
		
	def rotate(self, deg):
		if self.selectedHull is None:
			return
		self.selectedHull.rotate(deg)
		self.refresh()
		
	def translatexy(self, dx, dy):
		if self.selectedHull is None:
			return
		self.selectedHull.translatexy(dx, dy)
		self.refresh()
		
	def scalexyz(self, sx, sy, sz):
		if self.selectedHull is None:
			return
		self.selectedHull.scalexyz(sx, sy, sz)
		self.refresh()
		
	def onMouseWheel(self, evt):
		if self.selectedHull is None:
			return
		z = evt.GetWheelRotation()
		if z > 0:
			self.selectedHull.rotate(1)
		else:
			self.selectedHull.rotate(-1)
		self.refresh()
		
	def yzMirror(self):
		if self.selectedHull is None:
			return
		
		self.selectedHull.commitDeltas()
		self.selectedHull.yzMirror()
		self.refresh()
		
	def xzMirror(self):
		if self.selectedHull is None:
			return
		
		self.selectedHull.commitDeltas()
		self.selectedHull.xzMirror()
		self.refresh()
		
	def xyMirror(self):
		if self.selectedHull is None:
			return
		
		self.selectedHull.commitDeltas()
		self.selectedHull.xyMirror()
		self.refresh()
		
	def xyRotate(self, xa, ya):
		if self.selectedHull is None:
			return
		
		self.selectedHull.commitDeltas()
		self.selectedHull.xyRotate(xa, ya)
		self.refresh()
		
	def centerPlate(self):
		if not self.selectedHull is None:
			self.selectedHull.commitDeltas()

		minx = miny = 99999
		maxx = maxy = -99999
		for h in self.hulls:
			if h.minx < minx: minx = h.minx
			if h.maxx > maxx: maxx = h.maxx
			if h.miny < miny: miny = h.miny
			if h.maxy > maxy: maxy = h.maxy
			
		cx = minx + (maxx - minx)/2.0
		cy = miny + (maxy - miny)/2.0
		
		tx = buildarea[0]/2.0 - cx
		ty = buildarea[1]/2.0 - cy
		
		for h in self.hulls:
			h.translate(tx, ty)
			h.commitDeltas()
			
		self.refresh()
		
	def arrange(self):
		def cmpobj(a, b):
			return cmp(b.area, a.area)
		
		if not self.selectedHull is None:
			self.selectedHull.commitDeltas()

		omap = Map(buildarea, self.settings.arrangestrategy)
		
		for h in sorted(self.hulls, cmpobj):
			x, y = omap.find(h.width+self.settings.arrangemargin*2, h.height+self.settings.arrangemargin*2)
			if x is None or y is None:
				ud = self.parent.findUserDataBySeq(h.seq)
				if ud is None:
					name = h.stlObj.name
				else:
					name = ud.getName()
					
				dlg = wx.MessageDialog(self,
					"Object\n\n%s\n\ndoes not fit." % name,
					"Plate is full",
					wx.OK | wx.ICON_EXCLAMATION)
				dlg.ShowModal()
				dlg.Destroy()

			else:
				dx = x - h.centerx + h.width/2 + self.settings.arrangemargin
				dy = y - h.centery + h.height/2 + self.settings.arrangemargin
				
				h.translate(dx, dy)
				h.commitDeltas()
				
				width = h.width+self.settings.arrangemargin*2
				height = h.height+self.settings.arrangemargin*2
				omap.mark(x, y, width, height)


		if self.settings.centeronarrange:
			self.centerPlate()
		else:			
			self.refresh()

	def gridArrange(self, seqNbrs, rows, cols):
		master = self.findHullBySeq(seqNbrs[0])
		if master is None:
			return
		
		if not self.selectedHull is None:
			self.selectedHull.commitDeltas()
		
		dx = master.width + self.settings.arrangemargin*2
		dy = master.height + self.settings.arrangemargin*2
		
		hx = 0
		for col in range(cols):
			for row in range(rows):
				seq = seqNbrs[hx]
				hx += 1
				h = self.findHullBySeq(seq)
				h.translate(col * dx, row * dy)
				h.commitDeltas()
				
		if self.settings.centeronarrange:
			self.centerPlate()
		else:			
			self.refresh()


	def onSize(self, evt):
		self.initBuffer()
		
	def initBuffer(self):
		w, h = self.GetClientSize();
		self.buffer = wx.Bitmap(w, h)
		self.refresh()
		
	def refresh(self):
		dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
		self.drawGraph(dc)
		
	def onPaint(self, evt):
		dc = wx.BufferedPaintDC(self, self.buffer)
		
	def drawGraph(self, dc):
		dc.SetBackground(wx.Brush(wx.Colour(255, 255, 255)))
		dc.Clear()
		
		self.drawGrid(dc)
		self.drawObjects(dc)

	def drawGrid(self, dc):
		yleft = 0

		yright = (buildarea[1])*scale
		if yright > buildarea[1]*scale: yright = buildarea[1]*scale

		for x in range(0, buildarea[0]+1, 10):
			if x == 0 or x == buildarea[0]:
				dc.SetPen(wx.Pen(black, 1))
			elif x%50 == 0:
				dc.SetPen(wx.Pen(lt_Gray, 1))
			else:
				dc.SetPen(wx.Pen(dk_Gray, 1))
			x = x *scale
			if x >= 0 and x <= buildarea[0]*scale:
				dc.DrawLine(x, yleft, x, yright)
			
		xtop = 0

		xbottom = buildarea[0] *scale
		if xbottom > buildarea[0]*scale: xbottom = buildarea[0]*scale

		for y in range(0, buildarea[1]+1, 10):
			if y == 0 or y == buildarea[1]:
				dc.SetPen(wx.Pen(black, 1))
			if y%50 == 0:
				dc.SetPen(wx.Pen(lt_Gray, 1))
			else:
				dc.SetPen(wx.Pen(dk_Gray, 1))
			y = y *scale
			if y >= 0 and y <= buildarea[1]*scale:
				dc.DrawLine(xtop, y, xbottom, y)
				
	def drawObjects(self, dc):
		pen = wx.Pen(black, 2)
		pen.SetJoin(wx.JOIN_MITER)
		dc.SetPen(pen)
		
		dc.SetBrush(wx.Brush(clrNormal))
		for h in self.hulls:
			if h.seq != self.selectedSeq:
				dc.DrawPolygon(h.ptsScreen)
				
		if not self.selectedHull is None:
			dc.SetBrush(wx.Brush(clrSelected))
			dc.DrawPolygon(self.selectedHull.ptsScreen)


