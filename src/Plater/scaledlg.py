import wx

BUTTONDIM = (48, 48)

class ScaleDlg(wx.Dialog):
	def __init__(self, parent, stlframe, images, pos):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "", style=0, pos=pos)
		self.stlFrame = stlframe
		self.parent = parent
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.uniform = False
				
		f = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		t = wx.StaticText(self, wx.ID_ANY, "X")
		t.SetFont(f)
		
		sizer.AddSpacer(10)
		sizer.Add(t, 1, wx.TOP, 14)
		
		self.scXFactor = wx.SpinCtrl(self, wx.ID_ANY, "ScaleX", size=(60, -1))
		self.scXFactor.SetRange(1, 200)
		self.scXFactor.SetValue(100)
		self.scXFactor.SetToolTip("Scaling factor (%) for the X axis")
		self.Bind(wx.EVT_SPINCTRL, self.onscXFactor, self.scXFactor)
		sizer.Add(self.scXFactor, 5, wx.TOP, 12)
		sizer.AddSpacer(10)
		
		t = wx.StaticText(self, wx.ID_ANY, "Y")
		t.SetFont(f)
		
		sizer.AddSpacer(10)
		sizer.Add(t, 1, wx.TOP, 14)
		
		self.scYFactor = wx.SpinCtrl(self, wx.ID_ANY, "ScaleY", size=(60, -1))
		self.scYFactor.SetRange(1, 200)
		self.scYFactor.SetValue(100)
		self.scYFactor.SetToolTip("Scaling factor (%) for the Y axis")
		sizer.Add(self.scYFactor, 5, wx.TOP, 12)
		sizer.AddSpacer(10)
		
		t = wx.StaticText(self, wx.ID_ANY, "Z")
		t.SetFont(f)
		
		sizer.AddSpacer(10)
		sizer.Add(t, 1, wx.TOP, 14)
		
		self.scZFactor = wx.SpinCtrl(self, wx.ID_ANY, "ScaleZ", size=(60, -1))
		self.scZFactor.SetRange(1, 200)
		self.scZFactor.SetValue(100)
		self.scZFactor.SetToolTip("Scaling factor (%) for the Z axis")
		sizer.Add(self.scZFactor, 5, wx.TOP, 12)
		sizer.AddSpacer(20)
		
		self.cbUniform = wx.CheckBox(self, wx.ID_ANY, "Uniform Scaling")
		self.cbUniform.SetValue(False)
		self.cbUniform.SetToolTip("Scale uniformly along all 3 axes")
		sizer.Add(self.cbUniform, 10, wx.TOP, 16)
		self.Bind(wx.EVT_CHECKBOX, self.oncbUniform, self.cbUniform)
		sizer.AddSpacer(10)
		
		bScale = wx.BitmapButton(self, wx.ID_ANY, images.pngScale, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbScale, bScale)
		bScale.SetToolTip("Scale the selected object by the specified scaling factors")
		sizer.Add(bScale)
		sizer.AddSpacer(10)
		
		bView = wx.BitmapButton(self, wx.ID_ANY, images.pngView, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbView, bView)
		bView.SetToolTip("3D view of the object")
		sizer.AddSpacer(20)
		sizer.Add(bView)
		
		bExit = wx.BitmapButton(self, wx.ID_ANY, images.pngExit, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbExit, bExit)
		bExit.SetToolTip("Exit Dialog Box")
		sizer.AddSpacer(20)
		sizer.Add(bExit)
		
		self.SetSizer(sizer)
		self.Fit()
		
	def oncbUniform(self, evt):
		self.uniform = self.cbUniform.GetValue()
		if self.uniform:
			v = self.scXFactor.GetValue()
			self.scYFactor.SetValue(v)
			self.scZFactor.SetValue(v)
			self.scYFactor.Enable(False)
			self.scZFactor.Enable(False)
			self.scXFactor.SetToolTip("Scaling factor (%) for the X, Y, and Z axes")
		else:
			self.scYFactor.Enable(True)
			self.scZFactor.Enable(True)
			self.scXFactor.SetToolTip("Scaling factor (%) for the X axis")
			
	def onscXFactor(self, evt):
		if self.uniform:
			v = self.scXFactor.GetValue()
			self.scYFactor.SetValue(v)
			self.scZFactor.SetValue(v)
		
	def onbScale(self, evt):
		sx = self.scXFactor.GetValue() / 100.0
		sy = self.scYFactor.GetValue() / 100.0
		sz = self.scZFactor.GetValue() / 100.0
		
		if sx != 1 or sy != 1 or sz != 1:
			self.stlFrame.scalexyz(sx, sy, sz)
			self.parent.modified = True
				
	def onbView(self, evt):
		self.parent.viewObject()
		
	def onbExit(self, evt):
		self.EndModal(wx.ID_OK)
