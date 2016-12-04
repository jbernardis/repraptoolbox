import os
import wx
import time
import string

BUTTONDIM = (48, 48)

class Logger(wx.Frame):
	def __init__(self, parent):
		self.parent = parent
		wx.Frame.__init__(self, None, wx.ID_ANY, "", size=(400, 250))

		self.parent = parent
		self.settings = parent.settings
		self.images = parent.images
		
		self.setTraceLevel(99)
		
		self.nLines = 0
		self.maxLines = 1000;
		self.chunk = 100;
		if self.maxLines is not None and self.chunk > self.maxLines:
			self.chunk = self.maxLines/2
		
		sz = wx.BoxSizer(wx.VERTICAL)
		
		self.t = wx.TextCtrl(self, wx.ID_ANY, size=(300, 600), style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY)
		sz.Add(self.t, flag=wx.EXPAND | wx.ALL, border=10)
		
		bsz = wx.BoxSizer(wx.HORIZONTAL)
				
		self.bClear = wx.BitmapButton(self, wx.ID_ANY, self.images.pngClearlog, size=BUTTONDIM)
		self.bClear.SetToolTipString("Clear the log")
		bsz.Add(self.bClear, flag=wx.ALL, border=10)
		self.Bind(wx.EVT_BUTTON, self.doClear, self.bClear)
				
		self.bSave = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSavelog, size=BUTTONDIM)
		self.bSave.SetToolTipString("Save the log to a file")
		bsz.Add(self.bSave, flag=wx.ALL, border=10)
		self.Bind(wx.EVT_BUTTON, self.doSave, self.bSave)
		
		bsz.AddSpacer((20, 60))

		sz.Add(bsz, flag=wx.EXPAND | wx.ALL, border=10)

		self.SetSizer(sz)
		self.Layout()
		self.Fit()
		self.Show()

	def toggleVisibility(self):
		if self.IsShown():
			self.Hide()
		else:
			self.Show()

	def doClear(self, evt):
		self.t.Clear()
		
	def doSave(self, evt):
		wildcard = "Log File |*.log"
		dlg = wx.FileDialog(
			self, message="Save as ...", defaultDir=self.settings.lastlogdirectory, 
			defaultFile="", wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		
		val = dlg.ShowModal()

		if val == wx.ID_OK:
			path = dlg.GetPath()
	
			if self.t.SaveFile(path):
				self.LogMessage("Log successfully saved to %s" % path)
				self.settings.lastlogdirectory = os.path.dirname(path)
				self.settings.setModified()
			else:
				self.LogError("Save of log to %s failed" % path)
				
		dlg.Destroy()


	def setTraceLevel(self, l):
		self.traceLevel = l
		
	def LogTrace(self, level, text):
		if level <= self.traceLevel:
			self.LogMessage(("Trace[%d] - " % level) +string.rstrip(text)+"\n")

	def LogMessage(self, text):
		s = time.strftime('%H:%M:%S', time.localtime(time.time()))
		try:
			msg = s+" - "+string.rstrip(text)
				
			self.t.AppendText(msg+"\n")
			self.nLines += 1
			if self.maxLines is not None and self.nLines > self.maxLines:
				self.t.Remove(0L, self.t.XYToPosition(0, self.chunk))
				self.nLines -= self.chunk
		except:
			print "Unable to add (%s) to log" % text

	def LogCMessage(self, text):
		if self.logCommands:
			self.LogMessage("(c) - " + text)

	def LogGMessage(self, text):
		if self.logGCode:
			self.LogMessage("(g) - " + text)

	def LogMessageCR(self, text):
		self.LogMessage(text)

	def LogError(self, text):
		self.LogMessage("Error - " +string.rstrip(text))

	def LogWarning(self, text):
		self.LogMessage("Warning - " +string.rstrip(text))

