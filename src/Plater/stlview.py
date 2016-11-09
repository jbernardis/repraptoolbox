from wx import glcanvas
import wx
import os

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import vbo

VIEW_MODE_LOAD = 0
VIEW_MODE_LOOK = 1
VIEW_MODE_LOOK_HERE = 2
		
import struct, math
import numpy as np

BUTTONDIM = (48,48)

def vec(*args):
	return (GLfloat * len(args))(*args)
	
class StlCanvas(glcanvas.GLCanvas):
	def __init__(self, parent, wid=-1, buildarea=(200, 200), pos=wx.DefaultPosition,
				 size=(600, 600), style=0, mainwindow=None):
		attribList = (glcanvas.WX_GL_RGBA,  # RGBA
					  glcanvas.WX_GL_DOUBLEBUFFER,  # Double Buffered
					  glcanvas.WX_GL_DEPTH_SIZE, 24)  # 24 bit

		glcanvas.GLCanvas.__init__(self, parent, wid, size=size, style=style, pos=pos, attribList=attribList)
		self.init = False
		self.context = glcanvas.GLContext(self)
		
		self.spin = True
		self.originAtCenter = True

		# initial mouse position
		self.lastx = self.x = 0
		self.lasty = self.y = 0
		self.anglex = self.angley = self.anglez = 0
		self.transx = self.transy = 0
		self.resetView = True
		self.light0Pos = [0, 50, 150]
		self.light1Pos = [0, -50, 150]
		self.size = None
		
		self.clientwidth = size[0]
		self.drawGrid = False
		self.stlObject = None
		self.zoom = 1.0
		self.buildarea = buildarea
		self.adjPt = [x/2 for x in buildarea]
		
		self.setGridArrays()

		self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
		self.Bind(wx.EVT_LEFT_DCLICK, self.OnMouseDouble)
		self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
		self.Bind(wx.EVT_RIGHT_DOWN, self.OnMouseRightDown)
		self.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)
		self.Bind(wx.EVT_RIGHT_UP, self.OnMouseRightUp)
		self.Bind(wx.EVT_MOTION, self.OnMouseMotion)
		
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

	def setSpin(self, val):
		self.spin = val

	def getSpin(self):
		return self.spin

	def OnEraseBackground(self, event):
		pass # Do nothing, to avoid flashing on MSW.

	def OnSize(self, event):
		size = self.size = self.GetClientSize()
		if self.GetContext():
			if self.IsShown() and self.GetParent().IsShown():
				self.SetCurrent(self.context)
				glViewport(0, 0, size.width, size.height)
		event.Skip()

	def OnPaint(self, event):
		dc = wx.PaintDC(self)
		if self.IsShown():
			self.SetCurrent(self.context)
			if not self.init:
				self.init = True
				self.InitGL()
			self.OnDraw()

	def OnMouseDown(self, evt):
		self.SetFocus()
		self.CaptureMouse()
		self.stopTimer()
		self.x, self.y = self.lastx, self.lasty = evt.GetPosition()

	def startTimer(self):
		self.timer.Start(50)

	def stopTimer(self):
		self.timer.Stop()

	def OnTimer(self, evt):
		if not self.spin:
			return
		
		self.anglez = 0.5
		self.Refresh(False)
		
	def OnMouseRightDown(self, evt):
		self.SetFocus()
		self.CaptureMouse()
		self.stopTimer()
		self.x, self.y = self.lastx, self.lasty = evt.GetPosition()

	def OnMouseUp(self, evt):
		if self.HasCapture():
			self.ReleaseMouse()
			self.startTimer()

	def OnMouseRightUp(self, evt):
		if self.HasCapture():
			self.ReleaseMouse()
			self.startTimer()
		
	def OnMouseDouble(self, evt):
		self.resetView = True
		self.setZoom(1.0)
		self.Refresh(False)

	def OnMouseMotion(self, evt):
		if evt.Dragging() and evt.LeftIsDown():
			self.lastx, self.lasty = self.x, self.y
			self.x, self.y = evt.GetPosition()
			self.anglex = self.x - self.lastx
			self.angley = self.y - self.lasty
			self.transx = 0
			self.transy = 0
			self.Refresh(False)

		elif evt.Dragging() and evt.RightIsDown():
			self.lastx, self.lasty = self.x, self.y
			self.x, self.y = evt.GetPosition()
			self.anglex = 0
			self.angley = 0
			self.transx = (self.x - self.lastx)*self.zoom/3.0
			self.transy = -(self.y - self.lasty)*self.zoom/3.0
			self.Refresh(False)
		
	def OnWheel(self, evt):
		z = evt.GetWheelRotation()
		if z < 0:
			zoom = self.zoom*0.9
		else:
			zoom = self.zoom*1.1
				
		self.setZoom(zoom)
		self.Refresh(False)
		
	def InitGL(self):
		glClearColor(0.5, 0.5, 0.5, 1)
		glColor3f(1, 0, 0)
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_CULL_FACE)

		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glEnable(GL_LIGHT1)

		glLightfv(GL_LIGHT0, GL_POSITION, vec(.5, .5, 1, 0))
		glLightfv(GL_LIGHT0, GL_SPECULAR, vec(.5, .5, 0.5, 1))
		glLightfv(GL_LIGHT0, GL_DIFFUSE, vec(1, 1, 1, 1))
		glLightfv(GL_LIGHT1, GL_POSITION, vec(1, 0, .5, 0))
		glLightfv(GL_LIGHT1, GL_DIFFUSE, vec(.5, .5, .5, 1))
		glLightfv(GL_LIGHT1, GL_SPECULAR, vec(1, 1, 1, 1))

		glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, vec(0.5, 0, 0.3, 1))
		glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, vec(1, 1, 1, 1))
		glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 80)
		glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(0.1, 0.1, 0.1, 0.9))
		
		glLightfv(GL_LIGHT0, GL_POSITION, vec(0.0, 200.0, 100.0, 1))
		glLightfv(GL_LIGHT1, GL_POSITION, vec(0.0, -200.0, 100.0, 1))
		
	def setDrawGrid(self, flag):
		self.drawGrid = flag
		self.Refresh(True)

	def setZoom(self, zoom):
		self.zoom = zoom

	def setStlObject(self, o):
		self.stlObject = o
		self.setArrays()
		self.Refresh(False)
		
		self.startTimer()
		
	def setOriginAtCenter(self, flag):
		self.originAtCenter = flag
		
	def setArrays(self):
		self.vertices = []
		self.normals = []

		o = self.stlObject
		for fx in range(len(o.facets)):
			if self.originAtCenter:
				self.vertices.extend(o.facets[fx][1])
			else:
				self.vertices.extend([[x[0]-self.adjPt[0], x[1]-self.adjPt[1], x[2]] for x in o.facets[fx][1]])
				
			self.normals.extend([o.facets[fx][0], o.facets[fx][0], o.facets[fx][0]])

		self.npverts = np.array(self.vertices, dtype='f')
		self.npnorms = np.array(self.normals,  dtype='f')
		self.vertexPositions = vbo.VBO(self.npverts)
		self.normalPositions = vbo.VBO(self.npnorms)
				
	def setGridArrays(self):
		rows = int(self.buildarea[0]/20)
		cols = int(self.buildarea[1]/20)
		
		self.gridVertices = []
		self.gridColors = []
		
		for i in xrange(-rows, rows + 1):
			if i == -rows:
				c = [1.0, 0.0, 0.0, 1]
			elif i % 5 == 0:
				c = [0.1, 0.1, 0.1, 1]
			else:
				c = [0.4, 0.4, 0.4, 1]
			self.gridVertices.append([10 * -cols, 10 * i, 0, 10 * cols, 10 * i, 0])
			self.gridColors.append(c)
			
		for i in xrange(-cols, cols + 1):
			if i == -cols:
				c = [1.0, 0.0, 0.0, 1]
			elif i % 5 == 0:
				c = [0.1, 0.1, 0.1, 1]
			else:
				c = [0.4, 0.4, 0.4, 1]
			self.gridVertices.append([10 * i, 10 * -rows, 0, 10 * i, 10 * rows, 0])
			self.gridColors.append(c)

	def OnDraw(self):
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		glFrustum(-50.0*self.zoom, 50.0*self.zoom, -50.0*self.zoom, 50.0*self.zoom, 200, 800.0)
		#glTranslatef(0.0, 0.0, -400.0)
		gluLookAt (200.0, -200.0, 400.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0);

		glMatrixMode(GL_MODELVIEW)
		if self.resetView:
			glLoadIdentity()
			self.lastx = self.x = 0
			self.lasty = self.y = 0
			self.anglex = self.angley = self.anglez = 0
			self.transx = self.transy = 0
			self.resetView = False
			
		if self.size is None:
			self.size = self.GetClientSize()
		w, h = self.size
		w = max(w, 1.0)
		h = max(h, 1.0)
		xScale = 180.0 / w
		yScale = 180.0 / h
		glRotatef(self.angley * yScale, 1.0, 0.0, 0.0);
		glRotatef(self.anglex * xScale, 0.0, 1.0, 0.0);
		glRotatef(self.anglez, 0.0, 0.0, 1.0);
		glTranslatef(self.transx, self.transy, 0.0)

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE);
		glEnable(GL_COLOR_MATERIAL);

		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glEnable(GL_LIGHT1)
		
		self.drawGrid = True
		
		if self.drawGrid:
			glBegin(GL_LINES)
			for i in range(len(self.gridVertices)):
				glColor(self.gridColors[i])
				p = self.gridVertices[i]
				glVertex3f(p[0], p[1], p[2])
				glVertex3f(p[3], p[4], p[5])
			glEnd()
			
			
		glColor([0.0, 0.5, 0.25, 1])
			
		self.vertexPositions.bind()
		glEnableClientState(GL_VERTEX_ARRAY);
		glVertexPointer(3, GL_FLOAT, 0, self.vertexPositions);
		
		self.normalPositions.bind()
		glEnableClientState(GL_NORMAL_ARRAY)
		glNormalPointer(GL_FLOAT, 0, self.normalPositions);

		glDrawArrays(GL_TRIANGLES, 0, len(self.vertices));
				
		self.SwapBuffers()
		
		glDisable(GL_LIGHT0)
		glDisable(GL_LIGHT1)
		glDisable(GL_LIGHTING)
			
		self.anglex = self.angley = self.anglez = 0
		self.transx = self.transy = 0
		

class StlViewer(wx.Dialog):
	def __init__(self, parent, fn, title, mode, images, settings):
		self.settings = settings
		self.mode = mode
		wx.Dialog.__init__(self, parent, wx.ID_ANY, title, size=(200,200), style=wx.CAPTION)
		
		self.gl = StlCanvas(self, buildarea=self.settings.buildarea)
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.AddSpacer((10, 10))
		csizer = wx.BoxSizer(wx.HORIZONTAL)
		csizer.AddSpacer((10, 10))
		csizer.Add(self.gl)
		csizer.AddSpacer((10, 10))
		sizer.Add(csizer)
		sizer.AddSpacer((10, 10))
		
		bsizer = wx.BoxSizer(wx.HORIZONTAL)
		bsizer.AddSpacer((20, 10))
		
		self.bOK = wx.BitmapButton(self, wx.ID_ANY, images.pngOk, size=BUTTONDIM)
		if self.mode == VIEW_MODE_LOAD:
			self.bOK.SetToolTipString("Load the STL file")
		else:
			self.bOK.SetToolTipString("Dismiss dialog box")
		self.Bind(wx.EVT_BUTTON, self.onLoad, self.bOK)
		bsizer.Add(self.bOK)
		
		#bsizer.AddSpacer((600-BUTTONDIM[0]*2-20, 10))
		bsizer.AddSpacer((220, 10))
		
		self.cbSpin = wx.CheckBox(self, wx.ID_ANY, "Spin")
		f = self.settings.spinstlview
		self.cbSpin.SetValue(f)
		self.gl.setSpin(f)
		self.Bind(wx.EVT_CHECKBOX, self.onCbSpin, self.cbSpin)
		bsizer.Add(self.cbSpin)
		
		bsizer.AddSpacer((220, 10))
		
		if self.mode == VIEW_MODE_LOAD:
			self.bCancel = wx.BitmapButton(self, wx.ID_ANY, images.pngCancel, size=BUTTONDIM)
			self.bCancel.SetToolTipString("Do not load the STL file")
			self.Bind(wx.EVT_BUTTON, self.onDontLoad, self.bCancel)
			bsizer.Add(self.bCancel)
		
		sizer.Add(bsizer)

		sizer.AddSpacer((10, 10))
		
		self.SetSizer(sizer)
		self.Layout()
		self.Fit()
		if self.mode in [ VIEW_MODE_LOAD, VIEW_MODE_LOOK ]:
			stlObj = stl(filename=fn)
		else: # self.mode == VIEW_MODE_LOOK_HERE
			stlObj = fn
			self.gl.setOriginAtCenter(False)
		self.gl.setStlObject(stlObj)
		
	def onCbSpin(self, evt):
		f = self.cbSpin.GetValue()
		self.gl.setSpin(f)
		self.settings.spinstlview = f
		
	def onLoad(self, evt):
		self.gl.Destroy()
		self.EndModal(wx.ID_OK)
		
	def onDontLoad(self, evt):
		self.gl.Destroy()
		self.EndModal(wx.ID_CANCEL)
		

def cross(v1,v2):
	return [v1[1]*v2[2]-v1[2]*v2[1],v1[2]*v2[0]-v1[0]*v2[2],v1[0]*v2[1]-v1[1]*v2[0]]

def genfacet(v):
	veca=[v[1][0]-v[0][0],v[1][1]-v[0][1],v[1][2]-v[0][2]]
	vecb=[v[2][0]-v[1][0],v[2][1]-v[1][1],v[2][2]-v[1][2]]
	vecx=cross(veca,vecb)
	vlen=math.sqrt(sum(map(lambda x:x*x,vecx)))
	if vlen==0:
		vlen=1
	normal=map(lambda x:x/vlen, vecx)
	return [normal,v]

def is_ascii(s):
	if not all(ord(c) < 128 for c in s):
		return False
	
	return s.startswith("solid")	
		
class stl:
	def __init__(self, filename=None, name=None):
		self.facet=[[0,0,0],[[0,0,0],[0,0,0],[0,0,0]]]
		self.facets=[]
		
		self.name=name
		self.insolid=0
		self.filename = filename
		self.infacet=0
		self.inloop=0
		self.facetloc=0
		if filename is not None:
			self.f=list(open(filename))
			if not is_ascii(self.f[0]):
				f=open(filename,"rb")
				buf=f.read(84)
				while(len(buf)<84):
					newdata=f.read(84-len(buf))
					if not len(newdata):
						break
					buf+=newdata
				facetcount=struct.unpack_from("<I",buf,80)
				facetformat=struct.Struct("<ffffffffffffH")
				for i in xrange(facetcount[0]):
					buf=f.read(50)
					while(len(buf)<50):
						newdata=f.read(50-len(buf))
						if not len(newdata):
							break
						buf+=newdata
					fd=list(facetformat.unpack(buf))
					self.facet=[fd[:3],[fd[3:6],fd[6:9],fd[9:12]]]
					self.facets+=[self.facet]
				f.close()
			else:
				for i in self.f:
					self.parseline(i)
					
			for f in self.facets:
				f[0] = genfacet(f[1])[0]

			self.normalize()
	
	def normalize(self):
		minz = 99999
		maxx = -99999
		minx = 99999
		maxy = -99999
		miny = 99999
		for f in self.facets:
			for i in range(3):
				if f[1][i][0] < minx: minx = f[1][i][0]
				if f[1][i][0] > maxx: maxx = f[1][i][0]
				if f[1][i][1] < miny: miny = f[1][i][1]
				if f[1][i][1] > maxy: maxy = f[1][i][1]
				if f[1][i][2] < minz: minz = f[1][i][2]
		xCenter = (minx+maxx)/2.0
		yCenter = (miny+maxy)/2.0
		
		if xCenter != 0 or yCenter != 0:
			for i in range(len(self.facets)):
				for j in range(3):
					self.facets[i][1][j][0] -= xCenter
					self.facets[i][1][j][1] -= yCenter
		if minz != 0:
			for i in range(len(self.facets)):
				for j in range(3):
					self.facets[i][1][j][2] -= minz
					
				
	def parseline(self,l):
		l=l.strip()
		if l.startswith("solid"):
			self.insolid=1
			
		elif l.startswith("endsolid"):
			self.insolid=0
			return 0
		elif l.startswith("facet normal"):
			l=l.replace(",",".")
			self.infacet=11
			self.facetloc=0
			self.facet=[[0,0,0],[[0,0,0],[0,0,0],[0,0,0]]]
			self.facet[0]=map(float,l.split()[2:])
		elif l.startswith("endfacet"):
			self.infacet=0
			self.facets+=[self.facet]
			facet=self.facet
		elif l.startswith("vertex"):
			l=l.replace(",",".")
			self.facet[1][self.facetloc]=map(float,l.split()[1:])
			self.facetloc+=1
		return 1
