import wx

BUTTONDIM = (48, 48)

class HeaterInfo:
	def __init__(self, name, tool, info):
		self.name = name
		self.tool = tool
		self.mintemp = info[0]
		self.maxtemp = info[1]
		self.lowpreset = info[2]
		self.highpreset = info[3]
		self.setcmd = info[4]
		self.setwaitcmd = info[5]

class Heaters(wx.Window): 
	def __init__(self, parent, reprap):
		self.parent = parent
		self.images = parent.images
		self.settings = self.parent.settings
		self.reprap = reprap

		wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.SIMPLE_BORDER)		
		
		szHeaters = wx.BoxSizer(wx.VERTICAL)
		
		bedInfo = HeaterInfo("Bed", None, self.settings.bedinfo)
		hBed = Heater(self, bedInfo, self.reprap)
		szHeaters.Add(hBed)

		hHEs = []
		hHEInfo = []		
		for i in range(self.settings.nextruders):
			if self.settings.nextruders == 1:
				tool = None
				title = "HE"
			else:
				tool = i+1
				title = "HE%d" % tool

			hi = HeaterInfo(title, tool, self.settings.heinfo)	
			h = Heater(self, hi, self.reprap)
			szHeaters.Add(h)
			hHEs.append(h)
			hHEInfo.append(hi)
		
		
		
		szHeaters.AddSpacer((5, 5))
		self.SetSizer(szHeaters)
		self.Layout()
		self.Fit()
		

class Heater(wx.Window):
	def __init__(self, parent, hi, reprap):
		self.parent = parent
		self.images = parent.images
		self.settings = self.parent.settings
		self.reprap = reprap
		self.htrInfo = hi
		
		self.setting = None
		self.actual = None
		self.lowpreset = hi.lowpreset
		self.highpreset = hi.highpreset
		self.mintemp = hi.mintemp
		self.maxtemp = hi.maxtemp
		self.heaterOn = False
		wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.NO_BORDER)		
		
		szHeater = wx.BoxSizer(wx.HORIZONTAL)
		
		self.font12bold = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		self.font20bold = wx.Font(20, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		
		t = wx.StaticText(self, wx.ID_ANY, "%s:" % hi.name, size=(50, -1), style=wx.ALIGN_RIGHT)
		t.SetFont(self.font12bold)
		szHeater.Add(t, 0, wx.ALIGN_CENTER_VERTICAL, 1)
		
		szHeater.AddSpacer((10, 10))
		
		self.sbIndicator = wx.StaticBitmap(self, wx.ID_ANY, self.images.pngLedoff)
		szHeater.Add(self.sbIndicator, 0, wx.ALIGN_CENTER_VERTICAL, 1)
		
		self.bPower = wx.BitmapButton(self, wx.ID_ANY, self.images.pngHeatoff, size=BUTTONDIM, style = wx.NO_BORDER)
		self.bPower.SetToolTipString("Turn heater on/off")
		self.Bind(wx.EVT_BUTTON, self.onBPower, self.bPower)
		szHeater.Add(self.bPower)
		
		self.tcActual = wx.TextCtrl(self, wx.ID_ANY, "999", size=(50, -1), style=wx.TE_READONLY | wx.TE_RIGHT)
		self.tcActual.SetFont(self.font12bold)
		szHeater.Add(self.tcActual, 0, wx.ALIGN_CENTER_VERTICAL, 1)

		t = wx.StaticText(self, wx.ID_ANY, " / ")
		t.SetFont(self.font20bold)
		szHeater.Add(t, 0, wx.ALIGN_CENTER_VERTICAL, 1)

		self.tcSetting = wx.TextCtrl(self, wx.ID_ANY, "", size=(50, -1), style=wx.TE_READONLY | wx.TE_RIGHT)
		self.tcSetting.SetFont(self.font12bold)
		szHeater.Add(self.tcSetting, 0, wx.ALIGN_CENTER_VERTICAL, 1)
		
		self.slThermostat = wx.Slider(self, wx.ID_ANY, value=self.lowpreset, size=(180, -1),
				minValue=self.mintemp, maxValue=self.maxtemp,
				style=wx.SL_HORIZONTAL | wx.SL_VALUE_LABEL)
		self.slThermostat.SetToolTipString("Choose temperature setting for heater")
		szHeater.Add(self.slThermostat, 0, wx.ALIGN_CENTER_VERTICAL, 1)
		self.Bind(wx.EVT_SCROLL, self.doThermostat, self.slThermostat)
		
		szHeater.AddSpacer((10, 10))
		
		self.bLowPreset = wx.Button(self, wx.ID_ANY, "%d" % self.lowpreset, size=(40, 22))
		self.bLowPreset.SetToolTipString("Set heater to low preset value")
		self.Bind(wx.EVT_BUTTON, self.doLowPreset, self.bLowPreset)
		self.bHighPreset = wx.Button(self, wx.ID_ANY, "%d" % self.highpreset, size=(40, 22))
		self.bHighPreset.SetToolTipString("Set heater to high preset value")
		self.Bind(wx.EVT_BUTTON, self.doHighPreset, self.bHighPreset)
		
		sz = wx.BoxSizer(wx.VERTICAL)
		sz.AddSpacer((3,3))
		sz.Add(self.bHighPreset)
		sz.Add(self.bLowPreset)
		
		szHeater.Add(sz)
		
		szHeater.AddSpacer((10, 10))
		
		self.SetSizer(szHeater)
		self.Layout()
		self.Fit()
		
	def onBPower(self, evt):
		if self.heaterOn:
			self.heaterOn = False
			self.updateSetting(0)
			cmd = self.htrInfo.setcmd + " S0"
			self.sbIndicator.SetBitmap(self.images.pngLedoff)
			self.bPower.SetBitmap(self.images.pngHeatoff)
		else:
			self.heaterOn = True
			self.updateSetting(self.slThermostat.GetValue())
			cmd = self.htrInfo.setcmd + " S%d" % self.setting
			self.sbIndicator.SetBitmap(self.images.pngLedon)
			self.bPower.SetBitmap(self.images.pngHeaton)
			
		if self.htrInfo.tool is not None:
			cmd += " T%d" % self.htrInfo.tool
		self.reprap.sendNow(cmd)

	def updateSetting(self, newSetting):
		self.setting = newSetting
		self.tcSetting.SetValue("%d" % self.setting)
		
	def doLowPreset(self, evt):
		self.slThermostat.SetValue(self.lowpreset)	
				
	def doHighPreset(self, evt):
		self.slThermostat.SetValue(self.highpreset)	
				
	def doThermostat(self, evt):
		pass
