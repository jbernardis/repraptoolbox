import wx

dk_Gray = wx.Colour(224, 224, 224)
lt_Gray = wx.Colour(128, 128, 128)
black = wx.Colour(0, 0, 0)
blue = wx.Colour(0, 0, 255)
red = wx.Colour(255, 0, 0)

heColor = [red, red, red, red]

maxTemp = 300
minTemp = 10
ysize = maxTemp - minTemp
normaly = lambda y: ysize-y+minTemp
datapoints = 4*60
xsize = datapoints

yBottom = normaly(minTemp)
yTop = normaly(maxTemp)
xLeft = 0
xRight = xsize-1

class TempDlg(wx.Dialog):
	def __init__(self, parent, nextr, prtName):
		self.nextr = nextr
		self.parent = parent
		title = "%s temperatures" % prtName
		wx.Dialog.__init__(self, None, title=title)
		self.Show()
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.font12bold = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		self.font20bold = wx.Font(20, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		
		self.graph = TempGraph(self)
		
		szh = wx.BoxSizer(wx.HORIZONTAL)
		szv = wx.BoxSizer(wx.VERTICAL)

		szTimeLegend = wx.BoxSizer(wx.HORIZONTAL)		
		szTimeLegend.Add(wx.StaticText(self, wx.ID_ANY, "-4:00"))
		szTimeLegend.AddSpacer((34, 10))
		szTimeLegend.Add(wx.StaticText(self, wx.ID_ANY, "-3:00"))
		szTimeLegend.AddSpacer((34, 10))
		szTimeLegend.Add(wx.StaticText(self, wx.ID_ANY, "-2:00"))
		szTimeLegend.AddSpacer((34, 10))
		szTimeLegend.Add(wx.StaticText(self, wx.ID_ANY, "-1:00"))
		szTimeLegend.AddSpacer((34, 10))
		szTimeLegend.Add(wx.StaticText(self, wx.ID_ANY, "now"))
		
		szv.AddSpacer((10, 10))
		szv.Add(szTimeLegend)
		szv.Add(self.graph, 1, wx.ALIGN_CENTER_HORIZONTAL, 1)
		szv.AddSpacer((10, 10))
		
		szh.Add(szv)
		szh.AddSpacer((10, 10))
		
		szTempLegend = wx.BoxSizer(wx.VERTICAL)
		szTempLegend.AddSpacer((10, 20))
		szTempLegend.Add(wx.StaticText(self, wx.ID_ANY, "300"), 1, wx.ALIGN_RIGHT, 1)
		szTempLegend.AddSpacer((10, 33))
		szTempLegend.Add(wx.StaticText(self, wx.ID_ANY, "250"), 1, wx.ALIGN_RIGHT, 1)
		szTempLegend.AddSpacer((10, 33))
		szTempLegend.Add(wx.StaticText(self, wx.ID_ANY, "200"), 1, wx.ALIGN_RIGHT, 1)
		szTempLegend.AddSpacer((10, 33))
		szTempLegend.Add(wx.StaticText(self, wx.ID_ANY, "150"), 1, wx.ALIGN_RIGHT, 1)
		szTempLegend.AddSpacer((10, 33))
		szTempLegend.Add(wx.StaticText(self, wx.ID_ANY, "100"), 1, wx.ALIGN_RIGHT, 1)
		szTempLegend.AddSpacer((10, 33))
		szTempLegend.Add(wx.StaticText(self, wx.ID_ANY, "50"), 1, wx.ALIGN_RIGHT, 1)
		
		szdlg = wx.BoxSizer(wx.HORIZONTAL)
		szdlg.AddSpacer((10, 10))
		szdlg.Add(szTempLegend)
		szdlg.Add(szh)
		szdlg.AddSpacer((20, 20))
		
		self.heaters = {}
		szKeys = wx.BoxSizer(wx.VERTICAL)
		
		for i in range(self.nextr):
			name = "HE"
			if self.nextr > 1:
				name += "%d" % i
				
			h = GraphData(name, heColor[i])
			self.heaters[name] = h
			self.graph.addHeater(h)
			szKeys.Add(self.textFields(h))

		h = GraphData("Bed", blue)
		self.heaters["Bed"] = h
		self.graph.addHeater(h)
		szKeys.Add(self.textFields(h))
		
		szdlg.Add(szKeys)
		szdlg.AddSpacer((20, 20))
		
		self.SetSizer(szdlg)
		self.Fit()
		self.Layout()		

		self.graph.start()
		
	def textFields(self, gd):
		sz = wx.BoxSizer(wx.VERTICAL)
		sz.AddSpacer((20, 15))
		t = wx.StaticText(self, wx.ID_ANY, gd.getName())
		t.SetFont(self.font12bold)
		t.SetForegroundColour(gd.getColor())
		sz.Add(t)
		
		t = wx.StaticText(self, wx.ID_ANY, "", size=(130, -1))
		t.SetFont(self.font20bold)
		sz.Add(t)
		gd.setValueHandle(t)

		return sz
	
	def tempHandler(self, actualOrTarget, hName, tool, value):
		name = hName
		if tool is not None:
			name += "%d" % tool
			
		found = name in self.heaters.keys()
		if not found and hName == "HE" and tool == 0:
			name = "HE"
			found = name in self.heaters.keys()

		if found:
			h = self.heaters[name]
			if actualOrTarget == "actual":
				h.setValue(value)
				self.updateLabel(h)
				return
			elif actualOrTarget == "target":
				h.setSetting(value)
				self.updateLabel(h)
				return
				
		print "Unable to process temperature update: "
		print "(%s) (%s), " %(actualOrTarget, name), tool, value
		print self.heaters.keys()
		
	def updateLabel(self, h):
		v = h.getValue()
		if v is None:
			vAct = "???"
		else:
			vAct = "%.1f" % v
		v = h.getRawSetting()
		if v is None:
			vSet = "???"
		else:
			vSet = "%3d" % v
		h.getValueHandle().SetLabel("%s / %s" % (vAct, vSet))
		
	def onClose(self, evt):
		self.graph.stop()
		self.parent.closeGraph()
		self.Destroy()
		
class GraphData:
	def __init__(self, name, color):
		self.name = name
		self.color = color
		self.definePens()
		self.data = [None] * datapoints
		self.currentValue = None
		self.currentRawValue = None
		self.setting = None
		self.rawSetting = None
		self.valueHandle = None
		
	def nextPoint(self):
		self.data = self.data[1:] + [self.currentValue]
		
	def setValue(self, value):
		self.currentRawValue = value
		self.currentValue = normaly(value)
		
	def getValue(self):
		return self.currentRawValue
		
	def setValueHandle(self, vh):
		self.valueHandle = vh
		
	def getValueHandle(self):
		return self.valueHandle
		
	def getName(self):
		return self.name
	
	def setColor(self, color):
		self.color = color
		self.definePens()
		
	def getColor(self):
		return self.color
		
	def definePens(self):
		self.pen = wx.Pen(self.color, 2)
		self.penSetting = wx.Pen(self.color, 1, wx.DOT_DASH)
		
	def getPen(self):
		return self.pen
	
	def getSettingPen(self):
		return self.penSetting
	
	def setSetting(self, setting):
		self.rawSetting = setting
		self.setting = normaly(setting)
		
	def getSetting(self):
		return self.setting
		
	def getRawSetting(self):
		return self.rawSetting
	
	def getData(self):
		return [[tx, self.data[tx]] for tx in range(datapoints) if self.data[tx] is not None]
	
class TempGraph(wx.Window):
	def __init__(self, parent):
		self.parent = parent
		sz = [xsize, ysize]
		self.timer = None
		
		self.heaters = []
		
		wx.Window.__init__(self, parent, size=sz)
		
		self.initBuffer()
		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		
	def start(self):
		self.startTimer()
		
	def stop(self):
		self.stopTimer()
		
	def addHeater(self, gi):
		self.heaters.append(gi)
		
	def startTimer(self):
		print "starting timer"
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
		self.timer.Start(1000)

	def stopTimer(self):
		print "stopping timer"
		self.timer.Stop()
		self.timer = None

	def OnTimer(self, evt):
		print "tick"
		if len(self.heaters) > 0:
			for h in self.heaters:
				h.nextPoint()
				
			self.drawGraph()
		
	def onSize(self, evt):
		self.initBuffer()
			
	def onPaint(self, evt):
		dc = wx.BufferedPaintDC(self, self.buffer)

	def initBuffer(self):
		w, h = self.GetClientSize();
		self.buffer = wx.EmptyBitmap(w, h)
		self.drawGraph()
		
	def drawGraph(self):
		dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
		dc.SetBackground(wx.Brush(wx.Colour(255, 255, 230)))
		dc.Clear()
		
		self.drawGrid(dc)
		self.drawData(dc)
		
		del dc
		self.Refresh()
		self.Update()

	def drawGrid(self, dc):
		dc.SetPen(wx.Pen(dk_Gray, 1))
		for x in range(0, xsize, 10):
			if x%60 != 0:
				dc.DrawLine(x, yBottom, x, yTop)

		for yraw in range(minTemp, maxTemp+1, 10):
			y = normaly(yraw)
			if y%50 != 0:
				dc.DrawLine(xLeft, y, xRight, y)
			
		dc.SetPen(wx.Pen(lt_Gray, 1))
		for x in range(0, xsize, 10):
			if x%60 == 0:
				dc.DrawLine(x, yBottom, x, yTop)

		for yraw in range(minTemp, maxTemp+1, 10):
			y = normaly(yraw)
			if y%50 == 0:
				dc.DrawLine(xLeft, y, xRight, y)
			
	def drawData(self, dc):
		for h in self.heaters:
			d = h.getData()
			if len(d) > 0:
				dc.SetPen(h.getPen())
				dc.DrawLines(d)
				
			s = h.getSetting()
			if s is not None:
				dc.SetPen(h.getSettingPen())
				dc.DrawLine(xLeft, s, xRight, s)

			
class App(wx.App):
	def OnInit(self):
		self.dlg = TempDlg(self, 1)
		#self.dlg.Show()
		return True
			
if __name__ == '__main__':
	app = App(False)
	app.MainLoop()

