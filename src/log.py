import os
import wx
import time
import string
import inspect

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))

BUTTONDIM = (48, 48)

class Logger(wx.Frame):
	def __init__(self, parent):
		self.parent = parent
		wx.Frame.__init__(self, None, wx.ID_ANY, "RepRap Log")
		self.Bind(wx.EVT_CLOSE, self.onClose)
		ico = wx.Icon(os.path.join(cmdFolder, "images", "logbook.png"), wx.BITMAP_TYPE_PNG)
		self.SetIcon(ico)

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
		
		self.t = wx.TextCtrl(self, wx.ID_ANY, size=(600, 600), style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY)
		sz.Add(self.t, flag=wx.EXPAND | wx.ALL, border=10)

		self.SetSizer(sz)
		self.Layout()
		self.Fit()
		self.Show()
		
	def onClose(self, evt):
		pass

	def toggleVisibility(self):
		if self.IsShown():
			self.Hide()
		else:
			self.Show()

	def doClear(self):
		self.t.Clear()
		
	def doSave(self):
		wildcard = "Log File |*.log;*.LOG"
		dlg = wx.FileDialog(
			self, message="Save as ...", defaultDir=self.settings.lastlogdirectory, 
			defaultFile="", wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		
		val = dlg.ShowModal()

		if val == wx.ID_OK:
			path = dlg.GetPath()
	
			if self.t.SaveFile(path):
				self.LogMessage("Log successfully saved to %s" % path)
				self.settings.lastlogdirectory = os.path.dirname(path)
			else:
				self.LogError("Save of log to %s failed" % path)
				
		dlg.Destroy()

	def setTraceLevel(self, l):
		self.traceLevel = l

	def LogMessage(self, text, level=None, category=None):
		pre = time.strftime('%H:%M:%S ', time.localtime(time.time()))
		if not level is None and level <= self.traceLevel:
			pre += "Trace[%d] - " % level
		if not category is None:
			pre += "%s - " % category
			
		msg = pre + string.rstrip(text) + "\n"
		try:
			self.t.AppendText(msg)
			self.nLines += 1
			if self.maxLines is not None and self.nLines > self.maxLines:
				self.t.Remove(0L, self.t.XYToPosition(0, self.chunk))
				self.nLines -= self.chunk
		except:
			print "Unable to add (%s) to log" % text
