import wx

BUTTONDIM = (48, 48)		

class GridParamsDlg(wx.Dialog):
	def __init__(self, parent, images, pos):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Grid Parameters", pos=pos)

		self.scRows = wx.SpinCtrl(self, wx.ID_ANY, "Rows", size=(40, -1))
		self.scRows.SetRange(1,99)
		self.scRows.SetValue(1)
		self.scRows.SetToolTip("Number of Rows")

		self.scColumns = wx.SpinCtrl(self, wx.ID_ANY, "Columns", size=(40, -1))
		self.scColumns.SetRange(1,99)
		self.scColumns.SetValue(1)
		self.scColumns.SetToolTip("Number of Columns")
		
		szLabels = wx.BoxSizer(wx.VERTICAL)
		szSpinners = wx.BoxSizer(wx.VERTICAL)
		
		szLabels.AddSpacer(10)
		szLabels.Add(wx.StaticText(self, wx.ID_ANY, "Rows:"))
		szLabels.AddSpacer(10)
		szLabels.Add(wx.StaticText(self, wx.ID_ANY, "Columns:"))
		
		szSpinners.Add(self.scRows)
		szSpinners.AddSpacer(10)
		szSpinners.Add(self.scColumns)
		
		szParams = wx.BoxSizer(wx.HORIZONTAL)
		szParams.AddSpacer(40)
		szParams.Add(szLabels)
		szParams.AddSpacer(20)
		szParams.Add(szSpinners)
		szParams.AddSpacer(20)
		
		szButtons = wx.BoxSizer(wx.HORIZONTAL)
		
		
		bOK = wx.BitmapButton(self, wx.ID_ANY, images.pngOk, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbOK, bOK)
		bCancel = wx.BitmapButton(self, wx.ID_ANY, images.pngCancel, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onbCancel, bCancel)

		szButtons.AddSpacer(30)		
		szButtons.Add(bOK)
		szButtons.AddSpacer(30)		
		szButtons.Add(bCancel)
		szButtons.AddSpacer(30)		
		
		szDlg = wx.BoxSizer(wx.VERTICAL)
		szDlg.AddSpacer(10)
		szDlg.Add(szParams)
		szDlg.AddSpacer(20)
		szDlg.Add(szButtons)
		szDlg.AddSpacer(10)
		
		self.SetSizer(szDlg)
		self.Fit()
	
	def onbOK(self, evt):
		self.EndModal(wx.ID_OK)
		
	def onbCancel(self, evt):
		self.EndModal(wx.ID_CANCEL)
		
	def getValues(self):
		return self.scRows.GetValue(), self.scColumns.GetValue()


