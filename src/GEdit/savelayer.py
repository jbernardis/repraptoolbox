import wx
from wx.lib.masked import NumCtrl

class SaveLayerDlg(wx.Dialog):
	def __init__(self, parent, model):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Save Layer(s)")
		
		self.app = parent
		self.model = model
		self.layerText = self.getLayers()

		sizer = wx.BoxSizer(wx.VERTICAL)
		
		box = wx.BoxSizer(wx.HORIZONTAL)
		box.AddSpacer(10)
		
		self.lbStart = wx.ListBox(self, wx.ID_ANY, choices=self.layerText, style=wx.LB_SINGLE)
		self.lbStart.SetSelection(0)
		self.Bind(wx.EVT_LISTBOX, self.onLb, self.lbStart)
		b = wx.StaticBox(self, wx.ID_ANY, "Start Layer")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		sbox.Add(self.lbStart)
		box.Add(sbox)
		box.AddSpacer(10)
		
		self.lbEnd = wx.ListBox(self, wx.ID_ANY, choices=self.layerText, style=wx.LB_SINGLE)
		self.lbEnd.SetSelection(len(self.layerText)-1)
		self.Bind(wx.EVT_LISTBOX, self.onLb, self.lbEnd)
		b = wx.StaticBox(self, wx.ID_ANY, "End Layer")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		sbox.Add(self.lbEnd)
		box.Add(sbox)
		box.AddSpacer(10)
		
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(20)
		
		self.cbPreE = wx.CheckBox(self, wx.ID_ANY, "E Axis Reset")
		self.cbPreE.SetValue(True)
		vbox.Add(self.cbPreE)
		vbox.AddSpacer(20)
		
		self.cbZModify = wx.CheckBox(self, wx.ID_ANY, "Change height by")
		self.cbZModify.SetValue(True)
		self.Bind(wx.EVT_CHECKBOX, self.onCbZModify, self.cbZModify)
		self.cbZModify.SetValue(False)
		vbox.Add(self.cbZModify)
		vbox.AddSpacer(10)

		self.tcZDelta = NumCtrl(self, integerWidth=4, fractionWidth = 2)
		self.tcZDelta.Enable(False)
		vbox.Add(self.tcZDelta, 1, wx.ALIGN_CENTER_HORIZONTAL, 1)
		
		box.Add(vbox) #, 0, wx.GROW|wx.ALIGN_TOP)
		box.AddSpacer(10)

		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
		sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

		btnsizer = wx.BoxSizer(wx.HORIZONTAL)

		self.bOk = wx.Button(self, wx.ID_ANY, "OK")
		self.bOk.SetHelpText("Save the chosen layer range")
		self.Bind(wx.EVT_BUTTON, self.onOK, self.bOk)
		btnsizer.Add(self.bOk)
		
		btnsizer.AddSpacer(20)

		btn = wx.Button(self, wx.ID_ANY, "Cancel")
		btn.SetHelpText("Exit without saving")
		btnsizer.Add(btn)
		self.Bind(wx.EVT_BUTTON, self.onCancel, btn)

		sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		self.SetSizer(sizer)
		sizer.Fit(self)
		
	def onOK(self, evt):
		self.EndModal(wx.ID_OK)
		
	def onCancel(self, evt):
		self.EndModal(wx.ID_CANCEL)
		
	def onLb(self, evt):
		s = self.lbStart.GetSelection()
		e = self.lbEnd.GetSelection()
		self.bOk.Enable(s <= e)
		
	def onCbZModify(self, evt):
		self.tcZDelta.Enable(self.cbZModify.GetValue())
		
		
	def getValues(self):
		data = self.lbStart.GetSelection()
		try:
			slayer = int(data)
		except:
			slayer = 0
		
		data = self.lbEnd.GetSelection()
		try:
			elayer = int(data)
		except:
			elayer = 0
		
		return [slayer, elayer, self.cbPreE.GetValue(), self.cbZModify.GetValue(), self.tcZDelta.GetValue()]
		
	def getLayers(self):
		return ["%7.3f" % x.printHeight() for x in self.model]
