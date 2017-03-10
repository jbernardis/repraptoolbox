'''
Created on Mar 9, 2017

@author: ejefber
'''
import os
import wx
import time
from historyeventenum import HistoryEventEnum

VISIBLEQUEUESIZE = 15
BUTTONDIM = (48, 48)

class HistoryDlg(wx.Frame):
	def __init__(self, parent, history):
		wx.Frame.__init__(self, None, wx.ID_ANY, "Printing History")
		self.SetBackgroundColour("white")

		self.parent = parent		
		self.history = history
		self.history.refreshAll()
		
		self.gcFn = None
		self.stlFn = None

		self.images = self.history.images
		self.settings = self.history.settings

		self.Bind(wx.EVT_CLOSE, self.onClose)
		
		self.hcHistory = HistoryCtrl(self, self.history);
		
		self.bReprint = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPrinter, size=BUTTONDIM)
		self.bReprint.SetToolTipString("Export the selected G Code file")
		self.Bind(wx.EVT_BUTTON, self.onReprint, self.bReprint)
		self.bReprint.Enable(False)
		
		self.bReslice = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSlice, size=BUTTONDIM)
		self.bReslice.SetToolTipString("Export the selected STL file")
		self.Bind(wx.EVT_BUTTON, self.onReslice, self.bReslice)
		self.bReslice.Enable(False)
		
		self.bRefresh = wx.BitmapButton(self, wx.ID_ANY, self.images.pngRefresh, size=BUTTONDIM)
		self.bRefresh.SetToolTipString("Refresh the printing history")
		self.Bind(wx.EVT_BUTTON, self.onRefresh, self.bRefresh)
		self.bRefresh.Enable(True)
		
		self.cbBasename = wx.CheckBox(self, wx.ID_ANY, "Show basename only")
		self.cbBasename.SetToolTipString("Show only the basename of G Code files")
		self.Bind(wx.EVT_CHECKBOX, self.checkBasename, self.cbBasename)
		self.cbBasename.SetValue(self.settings.basenameonly)
		
		sz = wx.BoxSizer(wx.VERTICAL)
		sz.AddSpacer((10, 10))
		
		szh = wx.BoxSizer(wx.HORIZONTAL)
		szh.AddSpacer((10, 10))
		szh.Add(self.hcHistory)
		szh.AddSpacer((10, 10))
		sz.Add(szh)
		
		sz.AddSpacer((10, 10))
		
		sz.Add(self.cbBaseName, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		
		sz.AddSpacer((10, 10))
		
		szh = wx.BoxSizer(wx.HORIZONTAL)
		szh.Add(self.bReprint)
		szh.AddSpacer((10, 10))
		szh.Add(self.bReslice)
		szh.AddSpacer((20, 10))
		szh.Add(self.bRefresh)
		sz.Add(szh, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		
		sz.AddSpacer((10, 10))
		
		self.SetSizer(sz)
		self.Fit()
		
	def onClose(self, evt):
		self.parent.closeHistory()
		
	def onReprint(self, evt):
		self.parent.exportGcFile(self.gcFn)
		
	def onReslice(self, evt):
		self.parent.exportStlFile(self.stlFn)
		
	def onRefresh(self, evt):
		self.history.refreshAll()
		self.hcHistory.refresh()
		
	def checkBaseName(self, evt):
		self.settings.basenameonly = evt.IsChecked()
		self.hcHistory.setBaseNameOnly(self.settings.basenameonly)
		
	def GCodeFileExists(self, flag, evt):
		self.bReprint.Enable(flag)
		if flag:
			self.gcFn = evt.getFns()[0]
		
	def StlFileExists(self, flag, evt):
		self.bReslice.Enable(flag)
		if flag:
			self.gcFn = evt.getFns()[1]

class HistoryCtrl(wx.ListCtrl):	
	def __init__(self, parent, history):
		self.parent = parent
		self.history = history
		self.images = history.images
		self.settings = history.settings
		
		f = wx.Font(8,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		dc = wx.ScreenDC()
		dc.SetFont(f)
		fontHeight = dc.GetTextExtent("Xy")[1]
		
		colWidths = [400, 130, 100, 300]
		colTitles = ["File", "Time", "Event", "Config"]
		
		totwidth = 20;
		for w in colWidths:
			totwidth += w
			
		self.attrStale = wx.ListItemAttr()
		self.attrStale.SetBackgroundColour(wx.Colour(135, 206, 236))

		self.attrDeletedGc = wx.ListItemAttr()
		self.attrDeletedGc.SetBackgroundColour(wx.Colour(255, 153, 153))

		self.attrDeletedStl = wx.ListItemAttr()
		self.attrDeletedStl.SetBackgroundColour(wx.Colour(255, 153, 3))
		
		wx.ListCtrl.__init__(self, parent, wx.ID_ANY, size=(totwidth, fontHeight*(VISIBLEQUEUESIZE+1)),
			style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES|wx.LC_SINGLE_SEL
			)

		self.basenameonly = self.settings.basenameonly
		self.selectedItem = None
		self.selectedExists = False
		self.il = wx.ImageList(16, 16)
		self.il.Add(self.images.pngSelected)
		self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

		self.SetFont(f)
		for i in range(len(colWidths)):
			self.InsertColumn(i, colTitles[i])
			self.SetColumnWidth(i, colWidths[i])
			
		self.eventFlags = []
		for e in self.history:
			et = e.getEventType()
			fns = e.getFns()
			try:
				gcTime = os.path.getmtime(fns[0])
			except:
				gcTime = 0
				
			if et == HistoryEventEnum.SliceComplete:
				try:
					stlTime = os.path.getmtime(fns[1])
				except:
					stlTime = 0
			else:
				stlTime = None
				
			if gcTime == 0:
				self.eventFlags.append("delgc")
			elif stlTime == 0:
				self.eventFlags.append("delstl")
			elif stlTime is None:
				self.eventFlags.append("")
			elif stlTime > gcTime:
				self.eventFlags.append("stale")
			else:
				self.eventFlags.append("")
				
		self.setArraySize()
		
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.doListSelect)

	def setArraySize(self):		
		self.SetItemCount(len(self.history))
		
	def refreshAll(self):
		self.SetItemCount(len(self.history))
		for i in range(len(self.history)):
			self.RefreshItem(i)
		
	def getSelectedFile(self):
		if self.selectedItem is None:
			return None
		
		return self.history[self.selectedItem][0]
		
	def doListSelect(self, evt):
		x = self.selectedItem
		self.selectedItem = evt.m_itemIndex
		if x is not None:
			self.RefreshItem(x)
			
		e = self.history[self.selectedItem]
		fn = e.getFns()[0]
		if os.path.exists(fn):
			self.selectedExists = True
			print " %s exists" % fn
		else:
			self.selectedExists = False
			print "%s does not exist" % fn
		
		self.parent.GCodeFileExists(self.selectedExists, e)
		
		ex = False
		if e.getEventType() == HistoryEventEnum.SliceComplete:
			print "check for stl file"
			fn = e.getFns()[1]
			if os.path.exists(fn):
				ex = True
				
		self.parent.StlFileExists(ex, e)
				
		
	def doesSelectedExist(self):
		return self.selectedExists
			
	def setBaseNameOnly(self, flag):
		if self.basenameonly == flag:
			return
		
		self.basenameonly = flag
		for i in range(len(self.history)):
			self.RefreshItem(i)

	def OnGetItemText(self, item, col):
		e = self.history[item]
		if e is None:
			return "????"
		
		if col == 0:
			fn = e.getFns()[0]
			if item != 0:
				ofn = self.history[item-1].getFns()[0]
				if ofn == fn:
					return ""
				
			if self.basenameonly:
				return os.path.basename(fn)
			else:
				return fn
			
		elif col == 1:
			return time.strftime('%y/%m/%d-%H:%M:%S', time.localtime(e.getTimeStamp()))
		
		elif col == 2:
			return e.getEventTypeString()
		
		else:
			s = e.getString()
			
			return s

	def OnGetItemImage(self, item):
		if item == self.selectedItem:
			return 0
		else:
			return -1
	
	def OnGetItemAttr(self, item):
		if item < 0 or item > len(self.eventFlags):
			return None
		
		if self.eventFlags[item] == "stale":
			return self.attrStale
		elif self.eventFlags[item] == "delgc":
			return self.attrDeletedGc
		elif self.eventFlags[item] == "delstl":
			return self.attrDeletedStl
		else:
			return None

