import wx

BUTTONDIM = (48, 48)


class MirrorDlg(wx.Dialog):
	def __init__(self, parent, stlframe, images, pos):
		self.stlframe = stlframe
		self.parent = parent
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "", style=0, pos=pos)
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		bX = wx.BitmapButton(self, wx.ID_ANY, images.pngXaxis, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbX, bX)
		bX.SetToolTipString("Mirror on YZ plane")
		sizer.Add(bX)
		
		bY = wx.BitmapButton(self, wx.ID_ANY, images.pngYaxis, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbY, bY)
		bY.SetToolTipString("Mirror on XZ plane")
		sizer.Add(bY)
		
		bZ = wx.BitmapButton(self, wx.ID_ANY, images.pngZaxis, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbZ, bZ)
		bZ.SetToolTipString("Mirror on XY plane")
		sizer.Add(bZ)
		
		bView = wx.BitmapButton(self, wx.ID_ANY, images.pngView, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbView, bView)
		bView.SetToolTipString("3D view of the object")
		sizer.AddSpacer((20, 20))
		sizer.Add(bView)
		
		bExit = wx.BitmapButton(self, wx.ID_ANY, images.pngExit, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbExit, bExit)
		bExit.SetToolTipString("Dismiss dialog")
		sizer.AddSpacer((20, 20))
		sizer.Add(bExit)
		
		self.SetSizer(sizer)
		self.Fit()
		
	def onbX(self, evt):
		self.stlframe.yzMirror()
		self.parent.modified = True
		
	def onbY(self, evt):
		self.stlframe.xzMirror()
		self.parent.modified = True
		
	def onbZ(self, evt):
		self.stlframe.xyMirror()
		self.parent.modified = True
				
	def onbView(self, evt):
		self.parent.viewObject()
		
	def onbExit(self, evt):
		self.EndModal(wx.ID_CANCEL)
			
