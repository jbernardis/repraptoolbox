'''
Created on Jun 24, 2017

@author: Jeff
'''
import wx

class NumValidator(wx.PyValidator):
	def __init__(self, pyVar=None):
		wx.PyValidator.__init__(self)
		self.Bind(wx.EVT_CHAR, self.OnChar)

	def Clone(self):
		return NumValidator()

	def Validate(self, win):
		tc = self.GetWindow()
		val = tc.GetValue()
		
		print "in validate for value (%s)" % val

		return True

	def OnChar(self, event):
		key = event.GetKeyCode()
		
		if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
			event.Skip()
			return
		
		if not chr(key) in "0123456789.":
			return
		
		val = self.GetWindow().GetValue()
		if "." in val and chr(key) == ".":
			return

		event.Skip()
		return

class NumListValidator(wx.PyValidator):
	def __init__(self, pyVar=None):
		wx.PyValidator.__init__(self)
		self.Bind(wx.EVT_CHAR, self.OnChar)

	def Clone(self):
		return NumListValidator()

	def Validate(self, win):
		tc = self.GetWindow()
		val = tc.GetValue()
		
		print "in validate for value (%s)" % val

		return True

	def OnChar(self, event):
		key = event.GetKeyCode()
		
		if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
			event.Skip()
			return
		
		if not chr(key) in "0123456789.,":
			return
		
		val = self.GetWindow().GetValue().split(",")[-1]
		if "." in val and chr(key) == ".":
			return

		event.Skip()
		return
	
class NumPctValidator(wx.PyValidator):
	def __init__(self, pyVar=None):
		wx.PyValidator.__init__(self)
		self.Bind(wx.EVT_CHAR, self.OnChar)

	def Clone(self):
		return NumPctValidator()

	def Validate(self, win):
		tc = self.GetWindow()
		val = tc.GetValue()
		
		print "in validate for value (%s)" % val

		return True

	def OnChar(self, event):
		key = event.GetKeyCode()
		
		if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
			event.Skip()
			return
		
		if not chr(key) in "0123456789.%":
			return
		
		val = self.GetWindow().GetValue()
		if val == "" and chr(key) == "%":
			return
		
		if "%" in val:
			return
		
		if "." in val and chr(key) == ".":
			return

		event.Skip()
		return

class IntValidator(wx.PyValidator):
	def __init__(self, pyVar=None):
		wx.PyValidator.__init__(self)
		self.Bind(wx.EVT_CHAR, self.OnChar)

	def Clone(self):
		return IntValidator()

	def Validate(self, win):
		tc = self.GetWindow()
		val = tc.GetValue()
		
		print "in validate for value (%s)" % val

		return True

	def OnChar(self, event):
		key = event.GetKeyCode()
		
		if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
			event.Skip()
			return
		
		if not chr(key) in "0123456789":
			return

		event.Skip()
		return

class OvTypeBase:
	def __init__(self):
		pass
	
	def setTag(self, tag):
		self.tag = tag
	
	def createWidget(self, win, sz):
		self.win = win
		self.widget = wx.TextCtrl(self.win, wx.ID_ANY, "", size=sz)
		self.bindEvent = wx.EVT_TEXT
		return self.widget
	
	def enableBinding(self):
		self.win.Bind(self.bindEvent, self.setModified, self.widget)
	
	def setModified(self, evt):
		self.win.setModified()
	
	def setValue(self, v):
		self.widget.SetValue(v)
		return False
	
	def getValue(self):
		return self.widget.GetValue()
	
class OvTypeCB(OvTypeBase):
	def createWidget(self, win, sz):
		self.win = win
		self.widget = wx.CheckBox(self.win, wx.ID_ANY, "", size=sz)
		self.bindEvent = wx.EVT_CHECKBOX
		return self.widget
	
	def setValue(self, v):
		if v == 0:
			self.widget.SetValue(False)
		else:
			self.widget.SetValue(True)
		return False

	def getValue(self):
		if self.widget.GetValue():
			return "1"
		else:
			return "0"
	
class OvTypeInt(OvTypeBase):
	def createWidget(self, win, sz):
		self.win = win
		self.widget = wx.TextCtrl(self.win, wx.ID_ANY, "", size=sz, validator = IntValidator())
		self.bindEvent = wx.EVT_TEXT
		return self.widget

class OvTypeNumPct(OvTypeBase):
	def createWidget(self, win, sz):
		self.win = win
		self.widget = wx.TextCtrl(self.win, wx.ID_ANY, "", size=sz, validator = NumPctValidator())
		self.bindEvent = wx.EVT_TEXT
		return self.widget
	
class OvTypeNum(OvTypeBase):
	def createWidget(self, win, sz):
		self.win = win
		self.widget = wx.TextCtrl(self.win, wx.ID_ANY, "", size=sz, validator = NumValidator())
		self.bindEvent = wx.EVT_TEXT
		return self.widget
	
class OvTypeNumList(OvTypeBase):
	def createWidget(self, win, sz):
		self.win = win
		self.widget = wx.TextCtrl(self.win, wx.ID_ANY, "", size=sz, validator = NumListValidator())
		self.bindEvent = wx.EVT_TEXT
		return self.widget
	
class OvTypeString(OvTypeBase):
	pass
	
class OvTypeChoice(OvTypeBase):
	def __init__(self, choices):
		OvTypeBase.__init__(self)
		self.choices = choices
		
	def createWidget(self, win, sz):
		self.win = win
		self.widget = wx.Choice(self.win, wx.ID_ANY, choices=self.choices, size=sz)
		self.bindEvent = wx.EVT_CHOICE

		return self.widget
	
	def setValue(self, v):
		rc = False
		try:
			vx = self.choices.index(v)
		except:
			vx = 0
			dlg = wx.MessageDialog(self.win, "Invalid value (%s) for %s.\nSubstituting (%s)" % (v, self.tag, self.choices[0]),
					'Illegal Value?', wx.OK | wx.ICON_EXCLAMATION)
			dlg.ShowModal()
			dlg.Destroy()

			rc = True
			
		self.widget.SetSelection(vx)
			
		return rc
	
	def getValue(self):
		vx = self.widget.GetSelection()
		if vx == wx.NOT_FOUND:
			return None
		
		return self.widget.GetString(vx)



