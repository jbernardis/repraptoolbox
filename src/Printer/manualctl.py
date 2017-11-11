import wx
from imagemap import ImageMap
	
BUTTONDIM = (48,48)

imageMapXY = [[10,10,50,50,"XH"], [201,192,239,230,"YH"], [201,10,239,50,"ZH"], [10,192,50,230,"AH"],
	[216,86,235,156,"X+4"], [193,86,212,156,"X+3"], [168,86,190,156,"X+2"], [143,104,164,136,"X+1"],
	[83,104,105,136,"X-1"], [58,86,79,156,"X-2"], [33,86,56,156,"X-3"], [11,86,29,156,"X-4"],
	[98,214,152,231,"Y-4"], [98,188,152,209,"Y-3"], [98,163,152,185,"Y-2"], [110,139,140,161,"Y-1"],
	[110,79,140,101,"Y+1"], [98,53,152,78,"Y+2"], [98,28,152,52,"Y+3"], [98,7,152,27,"Y+4"]]

imageMapZ = [[11,39,47,62,"Z+3"], [11,67,47,88,"Z+2"], [11,91,47,109,"Z+1"],
	[11,126,47,145,"Z-1"], [11,148,47,170,"Z-2"], [11,172,47,197,"Z-3"]]

imageMapE = [[11,10,46,46,"Retr"], [11,93,46,129,"Extr"]]

imageMapStopM = [[6,2,51,44,"STOP"]]


dispatch = { "XH": "G28 X0", "YH": "G28 Y0", "ZH": "G28 Z0", "AH": "G28",
	"X-4": "G1 X-100", "X-3": "G1 X-10", "X-2": "G1 X-1", "X-1": "G1 X-0.1",
	"X+1": "G1 X0.1", "X+2": "G1 X1",	"X+3": "G1 X10",  "X+4": "G1 X100",
	"Y-4": "G1 Y-100", "Y-3": "G1 Y-10", "Y-2": "G1 Y-1", "Y-1": "G1 Y-0.1",
	"Y+1": "G1 Y0.1",	"Y+2": "G1 Y1",	"Y+3": "G1 Y10",  "Y+4": "G1 Y100",
	"Z-3": "G1 Z-10", "Z-2": "G1 Z-1",  "Z-1": "G1 Z-0.1",
	"Z+1": "G1 Z0.1",  "Z+2": "G1 Z1", "Z+3": "G1 Z10",
	"Extr": "Extrude", "Retr": "Retract",
	"STOP": "M84"}

class ManualCtl(wx.Window): 
	def __init__(self, parent, reprap, prtName):
		self.model = None
		self.parent = parent
		self.log = self.parent.log
		self.images = parent.images
		self.settings = self.parent.settings
		self.reprap = reprap
		self.prtName = prtName
		
		self.currentTool = 1

		wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.SIMPLE_BORDER)		

		self.axesXY = ImageMap(self, self.images.pngControl_xy)
		self.axesXY.SetToolTip("Move X/Y axes")
		self.axesXY.setHotSpots(self.onImageClick, imageMapXY)
		self.axisZ = ImageMap(self, self.images.pngControl_z)
		self.axisZ.SetToolTip("Move Z axis")
		self.axisZ.setHotSpots(self.onImageClick, imageMapZ)
		self.axisE = ImageMap(self, self.images.pngControl_e)
		self.axisE.SetToolTip("Extrude/Retract")
		self.axisE.setHotSpots(self.onImageClick, imageMapE)
		self.stopMotors = ImageMap(self, self.images.pngStopmotors)
		self.stopMotors.SetToolTip("Stop all motors")
		self.stopMotors.setHotSpots(self.onImageClick, imageMapStopM)
		
		szWindow = wx.BoxSizer(wx.VERTICAL)
		
		szManualCtl = wx.BoxSizer(wx.HORIZONTAL)
		szManualCtl.AddSpacer(20)
		szManualCtl.Add(self.axesXY)
		szManualCtl.AddSpacer(10)
		szManualCtl.Add(self.axisZ)
		szManualCtl.AddSpacer(10)
		
		sz = wx.BoxSizer(wx.VERTICAL)
		
		if self.settings.nextruders > 1:
			sz.AddSpacer(10)
			self.chTool = wx.Choice(self, wx.ID_ANY, choices=["Tool %d" % i for i in range(self.settings.nextruders)])
			self.Bind(wx.EVT_CHOICE, self.onToolChoice, self.chTool)
			sz.Add(self.chTool)
			self.chTool.SetSelection(0)
			
		sz.Add(self.axisE)
		
		self.cbCold = wx.CheckBox(self, wx.ID_ANY, "Cold")
		self.cbCold.SetToolTip("Allow cold extrusion")
		sz.Add(self.cbCold, 1, wx.ALIGN_CENTER_HORIZONTAL, 1)
		self.cbCold.SetValue(False)
		self.Bind(wx.EVT_CHECKBOX, self.onCbCold, self.cbCold)
		
		if self.settings.nextruders == 1:
			sz.AddSpacer(33)
			
		sz.Add(self.stopMotors)
		szManualCtl.Add(sz)
		szManualCtl.AddSpacer(10)

		self.font12bold = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		self.font12 = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		
		self.tXYSpeed = wx.TextCtrl(self, wx.ID_ANY, str(self.settings.xyspeed), size=(80, -1), style=wx.TE_RIGHT)
		self.tXYSpeed.SetToolTip("Set speed of X/Y movements")
		self.tXYSpeed.SetFont(self.font12)
		htc = self.tXYSpeed.GetSize()[1]
		
		sizerT = wx.BoxSizer(wx.VERTICAL)
		t = wx.StaticText(self, wx.ID_ANY, "XY Speed:")
		t.SetFont(self.font12bold)
		htt = t.GetSize()[1]

		sizerT.AddSpacer(20+htt+4)
		sizerT.Add(t, 1, wx.ALIGN_RIGHT, 0)
		sizerT.AddSpacer(htc+10-htt+4)
		#t = wx.StaticText(self, wx.ID_ANY, "Z Speed:", style=wx.ALIGN_RIGHT, size=(110, -1))
		t = wx.StaticText(self, wx.ID_ANY, "Z Speed:")
		t.SetFont(self.font12bold)
		sizerT.Add(t, 0, wx.ALIGN_RIGHT, 0)
		sizerT.AddSpacer(htc+10-htt+4)
		t = wx.StaticText(self, wx.ID_ANY, "E Speed:")
		t.SetFont(self.font12bold)
		sizerT.Add(t, 1, wx.ALIGN_RIGHT, 1)
		
		sizerT.AddSpacer(htc+20+4)
		t = wx.StaticText(self, wx.ID_ANY, "E Length:")
		t.SetFont(self.font12bold)
		sizerT.Add(t, 1, wx.ALIGN_RIGHT, 1)
		
		szManualCtl.Add(sizerT)
		szManualCtl.AddSpacer(10)
		
		sizerTC = wx.BoxSizer(wx.VERTICAL)
		t = wx.StaticText(self, wx.ID_ANY, "mm/min", style=wx.ALIGN_LEFT, size=(80, -1))
		t.SetFont(self.font12bold)
		sizerTC.AddSpacer(20)
		sizerTC.Add(t)

		sizerTC.Add(self.tXYSpeed)
		sizerTC.AddSpacer(10)
		self.tXYSpeed.Bind(wx.EVT_KILL_FOCUS, self.evtXYSpeedKillFocus)
		
		self.tZSpeed = wx.TextCtrl(self, wx.ID_ANY, str(self.settings.zspeed), size=(80, -1), style=wx.TE_RIGHT)
		self.tZSpeed.SetToolTip("Set speed of Z movements")
		self.tZSpeed.SetFont(self.font12)
		sizerTC.Add(self.tZSpeed)
		sizerTC.AddSpacer(10)
		self.tZSpeed.Bind(wx.EVT_KILL_FOCUS, self.evtZSpeedKillFocus)
		
		self.tESpeed = wx.TextCtrl(self, wx.ID_ANY, str(self.settings.espeed), size=(80, -1), style=wx.TE_RIGHT)
		self.tESpeed.SetToolTip("Set speed of Extrusion/Retraction")
		self.tESpeed.SetFont(self.font12)
		sizerTC.Add(self.tESpeed)
		
		t = wx.StaticText(self, wx.ID_ANY, "mm", style=wx.ALIGN_LEFT, size=(80, -1))
		t.SetFont(self.font12bold)
		sizerTC.AddSpacer(20)
		sizerTC.Add(t)
		
		self.tEDist = wx.TextCtrl(self, wx.ID_ANY, str(self.settings.edistance), size=(80, -1), style=wx.TE_RIGHT)
		self.tEDist.SetToolTip("Length of Extrusion/Retraction")
		self.tEDist.SetFont(self.font12)
		sizerTC.Add(self.tEDist)
		
		szManualCtl.Add(sizerTC)
		szManualCtl.AddSpacer(10)
		
		szWindow.Add(szManualCtl)
		
		szSpeed = wx.BoxSizer(wx.HORIZONTAL)
		
		self.bFanSpeed = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFan, size=BUTTONDIM, style=wx.NO_BORDER)
		self.bFanSpeed.SetToolTip("Control Fan Speed")
		self.Bind(wx.EVT_BUTTON, self.doBFanSpeed, self.bFanSpeed)
		
		self.slFanSpeed = wx.Slider(self, wx.ID_ANY, value=0, size=(180, -1),
				minValue=0, maxValue=255,
				style=wx.SL_HORIZONTAL | wx.SL_VALUE_LABEL)
		self.slFanSpeed.SetToolTip("Choose fan speed")
		
		self.bPrintSpeed = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPrintspeed, size=BUTTONDIM, style=wx.NO_BORDER)
		self.bPrintSpeed.SetToolTip("Apply Print Speed Multiplier")
		self.Bind(wx.EVT_BUTTON, self.doBPrintSpeed, self.bPrintSpeed)
		
		self.slPrintSpeed = wx.Slider(self, wx.ID_ANY, value=100, size=(180, -1),
				minValue=50, maxValue=200,
				style=wx.SL_HORIZONTAL | wx.SL_VALUE_LABEL)
		self.slPrintSpeed.SetToolTip("Choose print speed multiplier")

		szSpeed.Add(self.bFanSpeed)
		szSpeed.Add(self.slFanSpeed, 0, wx.ALIGN_CENTER_VERTICAL, 1)
		szSpeed.AddSpacer(20)
		szSpeed.Add(self.bPrintSpeed)
		szSpeed.Add(self.slPrintSpeed, 0, wx.ALIGN_CENTER_VERTICAL, 1)
		
		if self.settings.speedquery is not None:
			self.bQuery = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSpeedquery, size=BUTTONDIM, style=wx.NO_BORDER)
			self.bQuery.SetToolTip("Query the printer for Print and Fan Speeds")
			self.Bind(wx.EVT_BUTTON, self.doBQuery, self.bQuery)
			szSpeed.AddSpacer(20)
			szSpeed.Add(self.bQuery)

		szWindow.AddSpacer(10)
		szWindow.Add(szSpeed, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		
		self.SetSizer(szWindow)
		self.Layout()
		self.Fit()
		
		self.reprap.registerSpeedHandler(self.updateSpeed)
		self.reprap.registerToolHandler(self.updateTool)

		
	def doBFanSpeed(self, evt):
		self.reprap.sendNow("M106 S%d" % self.slFanSpeed.GetValue())
		
	def doBPrintSpeed(self, evt):
		self.reprap.sendNow("M220 S%d" % self.slPrintSpeed.GetValue())
		
	def doBQuery(self, evt):
		self.reprap.sendNow(self.settings.speedquery)

	def updateSpeed(self, fan, feed, flow):
		self.slFanSpeed.SetValue(int(fan))	
		self.slPrintSpeed.SetValue(int(feed))	
			
	def updateTool(self, tool):
		print "update tool: ", tool
		
	def onToolChoice(self, evt):
		t = self.chTool.GetSelection()
		if t == wx.NOT_FOUND:
			return
		
		self.currentTool = t+1
		self.reprap.sendNow("T%d" % self.currentTool)
		
	def onCbCold(self, evt):
		if self.cbCold.GetValue():
			self.reprap.sendNow("M302 S0")
		else:
			self.reprap.sendNow("M302 S170")
	
	def onImageClick(self, label):
		if label in dispatch.keys():
			cmd = dispatch[label]
			if cmd.startswith("G1 "):
				if "X" in label or "Y" in label:
					try:
						v = float(self.tXYSpeed.GetValue())
					except:
						self.log("Invalid value for XY Speed: %s" % self.tXYSpeed.GetValue())
						v = 0.0
					speed = " F%.3f" % v
				elif "Z" in label:
					try:
						v = float(self.tZSpeed.GetValue())
					except:
						self.log("Invalid value for Z Speed: %s" % self.tZSpeed.GetValue())
						v = 0.0
					speed = " F%.3f" % v
				else:
					speed = ""
				if self.settings.moveabsolute:
					self.reprap.sendNow("G91")
				self.reprap.sendNow(cmd + speed)
				if self.settings.moveabsolute:
					self.reprap.sendNow("G90")
				
			elif cmd in [ "Extrude", "Retract" ]:
				try:
					v = float(self.tESpeed.GetValue())
				except:
					self.log("Invalid value for E Speed: %s" % self.tESpeed.GetValue())
					v = 0.0
				speed = " F%.3f" % v
				try:
					d = float(self.tEDist.GetValue())
				except:
					self.log("Invalid value for E Distance: %s" % self.tEDist.GetValue())
					d = 0.0
				if cmd == "Retract":
					d = -d
				dist = " E%.3f" % d
				if self.settings.extrudeabsolute:
					if self.settings.useM82:
						self.reprap.sendNow("M83")
					else:
						self.reprap.sendNow("G91")
				self.reprap.sendNow("G1" + dist + speed)
				if self.settings.extrudeabsolute:
					if self.settings.useM82:
						self.reprap.sendNow("M82")
					else:
						self.reprap.sendNow("G90")
			else:
				self.reprap.sendNow(cmd)
			
	def evtXYSpeedKillFocus(self, evt):
		try:
			float(self.tXYSpeed.GetValue())
		except:
			self.log("Invalid value for XY Speed: %s" % self.tXYSpeed.GetValue())
			
	def evtZSpeedKillFocus(self, evt):
		try:
			float(self.tZSpeed.GetValue())
		except:
			self.log("Invalid value for Z Speed: %s" % self.tZSpeed.GetValue())
