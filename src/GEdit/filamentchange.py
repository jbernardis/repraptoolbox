import wx
import re

EXISTING = "existing"
NEW = "new"

FMT = "%.5f"

reE = re.compile("(.*[eE])([0-9\.]+)(.*)")

class FilamentChangeDlg(wx.Dialog):
	def __init__(self, parent, gcode, model, ip, ipz):
		self.parent = parent
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Add Filament Change")
		
		self.model = model
		self.gcode = gcode
		self.insertPoint = ip
		self.ipZheight = ipz
		self.newGCode = []
		
		self.eStart = self.findEValue(self.insertPoint-1)

		sizer = wx.BoxSizer(wx.VERTICAL)
		box = wx.BoxSizer(wx.HORIZONTAL)
		box.AddSpacer(10)
	
		b = wx.StaticBox(self, wx.ID_ANY, "Parameters")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		
		self.cbAbsE = wx.CheckBox(self, wx.ID_ANY, "Absolute E")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbAbsE)
		self.cbAbsE.SetValue(True)
		
		self.cbRetr = wx.CheckBox(self, wx.ID_ANY, "Add Retraction")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbRetr)
		self.amtRetr = wx.TextCtrl(self, wx.ID_ANY, "2", size=(125, -1))
		self.amtRetr.Bind(wx.EVT_KILL_FOCUS, self.updateDlg)

		self.cbZLift = wx.CheckBox(self, wx.ID_ANY, "Add Z Lift")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbZLift)
		self.amtZLift = wx.TextCtrl(self, wx.ID_ANY, "10", size=(125, -1))
		self.amtZLift.Bind(wx.EVT_KILL_FOCUS, self.updateDlg)
		
		scMessage = wx.StaticText(self, wx.ID_ANY, "LCD Message")
		self.txtLcd = wx.TextCtrl(self, wx.ID_ANY, "Change Filament", size=(125, -1))
		self.txtLcd.Bind(wx.EVT_KILL_FOCUS, self.updateDlg)

		self.cbHomeX = wx.CheckBox(self, wx.ID_ANY, "X Axis Home")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbHomeX)
		self.cbHomeY = wx.CheckBox(self, wx.ID_ANY, "Y Axis Home")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbHomeY)
		self.cbHomeZ = wx.CheckBox(self, wx.ID_ANY, "Z Axis Home")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbHomeZ)
		self.cbResetE = wx.CheckBox(self, wx.ID_ANY, "E Axis Reset")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbResetE)

		self.cbEExtra = wx.CheckBox(self, wx.ID_ANY, "Extra filament")
		self.amtEExtra = wx.TextCtrl(self, wx.ID_ANY, "0.5", size=(125, -1))
		self.amtEExtra.Bind(wx.EVT_KILL_FOCUS, self.updateDlg)
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbEExtra)
		
		scText = wx.StaticText(self, wx.ID_ANY, "Lines of Context")
		self.scContext = wx.SpinCtrl(self, wx.ID_ANY, "")
		self.scContext.SetRange(1, 10)
		self.scContext.SetValue(5)
		self.Bind(wx.EVT_SPINCTRL, self.updateDlg, self.scContext)

		sbox.AddMany([self.cbAbsE, (10, 10), self.cbRetr, (10, 10), self.amtRetr, (20, 20),
					self.cbZLift, (10, 10), self.amtZLift, (20, 20),
					scMessage, self.txtLcd, (20, 20),
					self.cbHomeX, (10, 10), self.cbHomeY, (10, 10), self.cbHomeZ, (20, 20),
					self.cbEExtra, (10, 10), self.amtEExtra, (20, 20),
					self.cbResetE, (20, 20), 
					scText, self.scContext, (10,10)])
		
		box.Add(sbox, 0, wx.GROW|wx.ALIGN_TOP)
		
		self.text = wx.TextCtrl(self, -1, "", size=(300, 100), style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH2)
		box.Add(self.text, 0, wx.GROW|wx.ALIGN_LEFT, 5)
		box.AddSpacer(10)

		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		btnsizer = wx.BoxSizer(wx.HORIZONTAL)

		btn = wx.Button(self, wx.ID_ANY, "OK")
		btn.SetHelpText("Insert the new code")
		self.Bind(wx.EVT_BUTTON, self.onBOk, btn)
		btnsizer.Add(btn)
		btnsizer.AddSpacer(20)

		btn = wx.Button(self, wx.ID_ANY, "Cancel")
		btn.SetHelpText("Exit without changing code")
		self.Bind(wx.EVT_BUTTON, self.onBCancel, btn)
		btnsizer.Add(btn)

		sizer.Add(btnsizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.SetSizer(sizer)
		sizer.Fit(self)
		
		self.updateDlg()
		
	def onBOk(self, evt):
		self.EndModal(wx.ID_OK)
		
	def onBCancel(self, evt):
		self.EndModal(wx.ID_CANCEL)
		
	def getValues(self):
		return self.newGCode
	
	def updateDlg(self, *arg):
		absolute = self.cbAbsE.IsChecked()
		self.newGCode = []
		
		try:
			contextLines = int(self.scContext.GetValue())
		except:
			contextLines = 1
		
		try:
			retr = float(self.amtRetr.GetValue())
		except:
			retr = 2.0

		try:
			eextra = float(self.amtEExtra.GetValue())
		except:
			eextra = 0.5

		try:
			lift = float(self.amtZLift.GetValue())
		except:
			lift = 10.0

		restoreZ = False
		if self.cbRetr.GetValue():
			if absolute:
				self.newGCode.append("G1 E" + FMT % (self.eStart - retr))
			else:
				self.newGCode.append("G1 E" + FMT % (-retr))
				
		if self.cbZLift.GetValue():
			self.newGCode.append("G1 Z" + FMT % (self.ipZheight + lift))
			restoreZ = True
			
		self.newGCode.append("M117 %s" % self.txtLcd.GetValue())
		self.newGCode.append("M0")
		self.newGCode.append("M117 Proceeding...")
			
		fX = self.cbHomeX.GetValue()
		fY = self.cbHomeY.GetValue()
		fZ = self.cbHomeZ.GetValue()
		if fX or fY or fZ:
			axes = ""
			if fX:
				axes += " X0"
			if fY:
				axes += " Y0"
			if fZ:
				axes += " Z0"
			self.newGCode.append("G28%s" % axes)
			if fZ:
				restoreZ = True
				self.newGCode.append("G1 Z" + FMT % (self.ipZheight + 2))
				
		if self.cbEExtra.IsChecked():
			if absolute:
				self.newGCode.append("G92 E0")
			self.newGCode.append("G1 E" + FMT % eextra)
			
			if not self.cbResetE.IsChecked() and absolute:
				self.newGCode.append("G92 E" + FMT % self.eStart)

		if self.cbResetE.GetValue() and absolute:
			if self.cbRetr.GetValue():
				self.newGCode.append("G92 E" + FMT % (self.eStart - retr))
			else:
				self.newGCode.append("G92 E" + FMT % self.eStart)
			
		if self.cbRetr.GetValue():
			if absolute:
				self.newGCode.append("G1 E" + FMT % self.eStart)
			else:
				self.newGCode.append("G1 E" + FMT % retr)
			
		if restoreZ:
			self.newGCode.append("G1 Z" + FMT % self.ipZheight)
	
		self.text.Clear()
		bg = self.text.GetBackgroundColour()
		
		for dl in range(contextLines):
			l = self.insertPoint - contextLines + dl
			if l < -1:
				pass
			elif l == -1:
				self.text.AppendText("<beginning of file>\n")
			else:
				self.text.AppendText(self.gcode[l])
				
		v = self.text.GetInsertionPoint()
		self.text.SetStyle(0, v, wx.TextAttr("red", bg))
			
		for g in self.newGCode:
			self.text.AppendText(g+"\n")
			
		v = self.text.GetInsertionPoint()

		nlines = len(self.gcode)		
		for dl in range(contextLines):
			if self.insertPoint+dl == nlines:
				self.text.appendText("<end of file>\n")
			elif self.insertPoint+dl > nlines:
				pass
			else:
				self.text.AppendText(self.gcode[self.insertPoint+dl])
			
		self.text.SetStyle(v, self.text.GetInsertionPoint(), wx.TextAttr("red", bg))
	
	def findEValue(self, sp):
		ix = sp
		while ix > 0:
			e = reE.match(self.gcode[ix])
			if e is None or e.lastindex != 3: 
				ix -= 1
				continue
			
			return float(e.group(2))
		
		return 0

			