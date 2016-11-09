import wx

BUTTONDIM = (48, 48)

class RotateDlg(wx.Dialog):
	def __init__(self, parent, stlframe, images, pos):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "", style=0, pos=pos)
		self.stlFrame = stlframe
		self.parent = parent
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		vsizer = wx.BoxSizer(wx.VERTICAL)
		
		bRot45CCW = wx.BitmapButton(self, wx.ID_ANY, images.pngRot45ccw, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbRot45CCW, bRot45CCW)
		bRot45CCW.SetToolTipString("Rotate 45 degrees around the Z axis - CCW")
		sizer.Add(bRot45CCW)
		
		bRot45CW = wx.BitmapButton(self, wx.ID_ANY, images.pngRot45cw, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbRot45CW, bRot45CW)
		bRot45CW.SetToolTipString("Rotate 45 degrees around the Z axis - CW")
		sizer.Add(bRot45CW)
		
		f = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		t = wx.StaticText(self, wx.ID_ANY, "Z")
		t.SetFont(f)
		
		sizer.AddSpacer((10, 10))
		sizer.Add(t, 1, wx.TOP, 14)
		
		self.scDegZ = wx.SpinCtrl(self, wx.ID_ANY, "Degreesz", size=(60, -1))
		self.scDegZ.SetRange(-359, 359)
		self.scDegZ.SetValue(0)
		self.scDegZ.SetToolTipString("Angle of rotation around Z axis(<0 => CW rotation)")
		sizer.Add(self.scDegZ, 5, wx.TOP, 12)
		sizer.AddSpacer((10, 10))
		
		bRot = wx.BitmapButton(self, wx.ID_ANY, images.pngRotatez, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbRotate, bRot)
		bRot.SetToolTipString("Rotate the specified number of degrees around the Z axis")
		sizer.Add(bRot)
		
		bView = wx.BitmapButton(self, wx.ID_ANY, images.pngView, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbView, bView)
		bView.SetToolTipString("3D view of the object")
		sizer.AddSpacer((20, 20))
		sizer.Add(bView)
		
		vsizer.Add(sizer)
		
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		sizer.AddSpacer((4, 4))
		
		t = wx.StaticText(self, wx.ID_ANY, "X")
		t.SetFont(f)
		
		sizer.AddSpacer((10, 10))
		sizer.Add(t, 1, wx.TOP, 14)
		
		self.scDegX = wx.SpinCtrl(self, wx.ID_ANY, "Degreesx", size=(60, -1))
		self.scDegX.SetRange(-359, 359)
		self.scDegX.SetValue(0)
		self.scDegX.SetToolTipString("Angle of rotation around the X axis")
		sizer.Add(self.scDegX, 5, wx.TOP, 12)
		sizer.AddSpacer((10, 10))

		
		t = wx.StaticText(self, wx.ID_ANY, "Y")
		t.SetFont(f)
		
		sizer.AddSpacer((10, 10))
		sizer.Add(t, 1, wx.TOP, 14)
		
		self.scDegY = wx.SpinCtrl(self, wx.ID_ANY, "Degreesy", size=(60, -1))
		self.scDegY.SetRange(-359, 359)
		self.scDegY.SetValue(0)
		self.scDegY.SetToolTipString("Angle of rotation around the Y axis")
		sizer.Add(self.scDegY, 5, wx.TOP, 12)
		sizer.AddSpacer((10, 10))
		
		bRot = wx.BitmapButton(self, wx.ID_ANY, images.pngRotatexy, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbRotatexy, bRot)
		bRot.SetToolTipString("Rotate the specified number of degrees around the X and/or Y axes")
		sizer.Add(bRot)
		
		bExit = wx.BitmapButton(self, wx.ID_ANY, images.pngExit, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbExit, bExit)
		bExit.SetToolTipString("Exit Dialog Box")
		sizer.AddSpacer((20, 20))
		sizer.Add(bExit)
		
		vsizer.Add(sizer)
		
		self.SetSizer(vsizer)
		self.Fit()
		
	def onbRot45CCW(self, evt):
		self.stlFrame.rotate(45)
		self.parent.modified = True
		
	def onbRot45CW(self, evt):
		self.stlFrame.rotate(-45)
		self.parent.modified = True
		
	def onbRotate(self, evt):
		degrees = self.scDegZ.GetValue()
		if degrees != 0:
			self.stlFrame.rotate(degrees)
			self.parent.modified = True
		
	def onbRotatexy(self, evt):
		degreesx = self.scDegX.GetValue()
		degreesy = self.scDegY.GetValue()
		if degreesx != 0 or degreesy != 0:
			self.stlFrame.xyRotate(degreesx, degreesy)
			self.parent.modified = True
				
	def onbView(self, evt):
		self.parent.viewObject()
		
	def onbExit(self, evt):
		self.EndModal(wx.ID_OK)
