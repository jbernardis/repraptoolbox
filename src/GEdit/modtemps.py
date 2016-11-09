import wx

MINBED = -100
MAXBED = 100
MINHE = -200
MAXHE = 200

SLIDER_BASEID = 1000

class ModifyTempsDlg(wx.Dialog):
	def __init__(self, parent, model, platemp, abstemp):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Modify Temperatures")
		
		ipfont = wx.Font(16,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

		self.app = parent
		self.model = model
		
		self.plaTemp = platemp
		self.absTemp = abstemp
		
		self.bed, self.hotends = self.model.getTemps()

		self.bedDelta = 0
		self.heDelta = [0, 0, 0, 0]
		
		self.nHe = 0
		self.heX = []
		for hx in range(len(self.hotends)):
			if self.hotends[hx] is not None:
				self.heX.append(hx)
				self.nHe += 1
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		slidesizer = wx.GridSizer(rows=self.nHe+1, cols=2)
		btnsizer = wx.BoxSizer(wx.HORIZONTAL)

		self.modBed = wx.Slider(
			self, wx.ID_ANY, 0, MINBED, MAXBED, size=(150, -1),
			style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		self.modBed.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinBed)
		self.modBed.Bind(wx.EVT_MOUSEWHEEL, self.onMouseBed)
		self.modBed.SetPageSize(1);

		b = wx.StaticBox(self, wx.ID_ANY, "Bed Temperature Delta")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		sbox.Add(self.modBed, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
		slidesizer.Add(sbox, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
		
		self.bedTemp = wx.StaticText(self, wx.ID_ANY, "");
		self.bedTemp.SetFont(ipfont)
		slidesizer.Add(self.bedTemp, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 40)

		self.modHE = [None, None, None, None]
		self.heTemp = [None, None, None, None]
		for he in range(self.nHe):
			self.modHE[he] = wx.Slider(
				self, SLIDER_BASEID + he, 0, MINHE, MAXHE, size=(150, -1),
				style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
			self.modHE[he].Bind(wx.EVT_SCROLL_CHANGED, self.onSpinHE)
			self.modHE[he].Bind(wx.EVT_MOUSEWHEEL, self.onMouseHE)
			self.modHE[he].SetPageSize(1);
	
			b = wx.StaticBox(self, wx.ID_ANY, "Hot End %d Delta" % self.heX[he])
			sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
			sbox.Add(self.modHE[he], 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
			slidesizer.Add(sbox, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
	
			self.heTemp[he] = wx.StaticText(self, wx.ID_ANY, "");
			self.heTemp[he].SetFont(ipfont)
			slidesizer.Add(self.heTemp[he], 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 40)

		btn = wx.Button(self, wx.ID_ANY, "PLA->ABS")
		btn.SetHelpText("Change from PLA profile to ABS")
		self.Bind(wx.EVT_BUTTON, self.profilePLA2ABS, btn)
		btnsizer.Add(btn);

		btn = wx.Button(self, wx.ID_ANY, "ABS->PLA")
		btn.SetHelpText("Change from ABS profile to PLA")
		self.Bind(wx.EVT_BUTTON, self.profileABS2PLA, btn)
		btnsizer.Add(btn);
		
		self.btnOK = wx.Button(self, wx.ID_OK)
		self.btnOK.SetHelpText("Save the changes")
		self.btnOK.SetDefault()
		btnsizer.Add(self.btnOK)
		self.btnOK.Enable(False)

		self.btnCancel = wx.Button(self, wx.ID_CANCEL)
		self.btnCancel.SetHelpText("Exit without saving")
		self.btnCancel.SetLabel("Close")
		btnsizer.Add(self.btnCancel)

		self.showTemps()

		sizer.Add(slidesizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		self.SetSizer(sizer)
		sizer.Fit(self)

	def profilePLA2ABS(self, evt):
		self.bedDelta = self.absTemp[0] - self.plaTemp[0]
		self.heDelta = [0, 0, 0, 0]
		for he in range(self.nHe):
			self.heDelta[self.heX[he]] = self.absTemp[1] - self.plaTemp[1]
		self.showTemps()

	def profileABS2PLA(self, evt):
		self.bedDelta = self.plaTemp[0] - self.absTemp[0]
		self.heDelta = [0, 0, 0, 0]
		for he in range(self.nHe):
			self.heDelta[self.heX[he]] = self.plaTemp[1] - self.absTemp[1]
		self.showTemps()

	def showTemps(self):
		changes = False
		if self.bedDelta != 0:
			changes = True
		s = "%.1f / %.1f" % (self.bed, self.bed+self.bedDelta)
		self.bedTemp.SetLabel(s)
		self.modBed.SetValue(self.bedDelta)

		for he in range(self.nHe):
			hx = self.heX[he]
			if self.heDelta[hx] != 0:
				changes = True
			s = "%.1f / %.1f" % (self.hotends[hx], self.hotends[hx]+self.heDelta[hx])
			self.heTemp[he].SetLabel(s)
			self.modHE[he].SetValue(self.heDelta[hx])

		if changes:
			self.btnOK.Enable(True)
			self.btnCancel.SetLabel("Cancel")
		else:
			self.btnOK.Enable(False)
			self.btnCancel.SetLabel("Close")
		
	def onSpinBed(self, evt):
		self.bedDelta = evt.EventObject.GetValue()
		self.showTemps()
	
	def onSpinHE(self, evt):
		heid = evt.GetId() - SLIDER_BASEID
		hx = self.heX[heid]
		self.heDelta[hx] = evt.EventObject.GetValue()
		self.showTemps()
	
	def onMouseBed(self, evt):
		l = self.modBed.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= MINBED and l <= MAXBED:
			self.bedDelta = l
			self.showTemps()
	
	def onMouseHE(self, evt):
		heid = evt.GetId() - SLIDER_BASEID
		hx = self.heX[heid]
		l = self.modHE[heid].GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= MINHE and l <= MAXHE:
			self.heDelta[hx] = l
			self.showTemps()
			
	def getResult(self):
		return (self.bedDelta, self.heDelta)

