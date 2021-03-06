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
		self.filterEvent = None
		self.filtering = False

		self.images = self.history.images
		self.settings = self.history.settings

		self.Bind(wx.EVT_CLOSE, self.onClose)
		
		self.hcHistory = HistoryCtrl(self, self.history);
		
		self.bReprint = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPrinter, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onReprint, self.bReprint)
		self.bReprint.Enable(False)
		
		self.bReslice = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSlice, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.onReslice, self.bReslice)
		self.bReslice.Enable(False)
		
		self.bRefresh = wx.BitmapButton(self, wx.ID_ANY, self.images.pngRefresh, size=BUTTONDIM)
		self.bRefresh.SetToolTip("Refresh the printing history")
		self.Bind(wx.EVT_BUTTON, self.onRefresh, self.bRefresh)
		self.bRefresh.Enable(True)
		
		self.bFilter = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFilter, size=BUTTONDIM)
		self.bFilter.SetToolTip("Filter the output to show a single file")
		self.Bind(wx.EVT_BUTTON, self.onFilter, self.bFilter)
		self.bFilter.Enable(False)
		
		self.tcFilterFile = wx.TextCtrl(self, wx.ID_ANY, "", size=(200, -1), style=wx.TE_READONLY)
		
		self.cbBasename = wx.CheckBox(self, wx.ID_ANY, "Show basename only")
		self.cbBasename.SetToolTip("Show only the basename of G Code files")
		self.Bind(wx.EVT_CHECKBOX, self.checkBasename, self.cbBasename)
		self.cbBasename.SetValue(self.settings.basenameonly)
		
		self.cbEnqueueGC = wx.CheckBox(self, wx.ID_ANY, "Enqueue G Code file")
		self.cbEnqueueGC.SetToolTip("Add the G Code file to the print queue when exporting")
		self.Bind(wx.EVT_CHECKBOX, self.checkEnqueueGC, self.cbEnqueueGC)
		self.cbEnqueueGC.SetValue(self.settings.enqueuegc)
		
		self.cbEnqueueStl = wx.CheckBox(self, wx.ID_ANY, "Enqueue STL file")
		self.cbEnqueueStl.SetToolTip("Add the STL file to the slice queue when exporting")
		self.Bind(wx.EVT_CHECKBOX, self.checkEnqueueStl, self.cbEnqueueStl)
		self.cbEnqueueStl.SetValue(self.settings.enqueuestl)
		
		self.updateGcHelpText()
		self.updateStlHelpText()
		
		sz = wx.BoxSizer(wx.VERTICAL)
		sz.AddSpacer(10)
		
		szh = wx.BoxSizer(wx.HORIZONTAL)
		szh.AddSpacer(10)
		szh.Add(self.hcHistory)
		szh.AddSpacer(10)
		sz.Add(szh)
		
		sz.AddSpacer(10)
		
		sz.Add(self.cbBasename, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		
		sz.AddSpacer(10)
		
		szh = wx.BoxSizer(wx.HORIZONTAL)
		szh.Add(self.bReslice)
		szh.AddSpacer(5)
		szh.Add(self.cbEnqueueStl, 1, wx.TOP, 12)
		szh.AddSpacer(30)
		szh.Add(self.bReprint)
		szh.AddSpacer(5)
		szh.Add(self.cbEnqueueGC, 1, wx.TOP, 12)
		szh.AddSpacer(30)
		szh.Add(self.bRefresh)
		szh.AddSpacer(30)
		szh.Add(self.bFilter)
		szh.AddSpacer(5)
		szh.Add(self.tcFilterFile, 1, wx.TOP, 12)
		sz.Add(szh, 0, wx.ALIGN_CENTER_HORIZONTAL, 1)
		
		sz.AddSpacer(10)
		
		self.SetSizer(sz)
		self.Fit()
		
	def onClose(self, evt):
		self.parent.closeHistory()
		
	def onReprint(self, evt):
		self.parent.exportGcFile(self.gcFn, True, self.settings.enqueuegc)
		
	def onReslice(self, evt):
		self.parent.exportStlFile(self.stlFn, True, self.settings.enqueuestl)
		
	def onRefresh(self, evt):
		self.history.refreshAll()
		self.hcHistory.refreshAll()
		
	def checkBasename(self, evt):
		self.settings.basenameonly = evt.IsChecked()
		self.hcHistory.setBasenameOnly(self.settings.basenameonly)
		
	def checkEnqueueGC(self, evt):
		self.settings.enqueuegc = evt.IsChecked()
		self.updateGcHelpText()
		
	def checkEnqueueStl(self, evt):
		self.settings.enqueuestl = evt.IsChecked()
		self.updateStlHelpText()
		
	def GCodeFileExists(self, flag, evt=None):
		if flag and evt is not None:
			self.bReprint.Enable(True)
			self.gcFn = evt.getFns()[0]
		else:
			self.bReprint.Enable(False)
			self.gcFn = None
			
		self.updateGcHelpText()
		
	def StlFileExists(self, flag, evt=None):
		if flag and evt is not None:
			self.bReslice.Enable(True)
			self.stlFn = evt.getFns()[1]
		else:
			self.bReslice.Enable(False)
			self.stlFn = None
			
		self.updateStlHelpText()
		
	def updateGcHelpText(self):
		if self.bReprint.IsEnabled():
			ht = "Export "
			if self.settings.enqueuegc:
				ht += "(and enqueue) "
			ht += "G Code file (%s)" % self.gcFn
			self.bReprint.SetToolTip(ht)
		else:
			self.bReprint.SetToolTip("")
		
	def updateStlHelpText(self):
		if self.bReslice.IsEnabled():
			ht = "Export "
			if self.settings.enqueuestl:
				ht += "(and enqueue) "
			ht += "STL file (%s)" % self.stlFn
			self.bReslice.SetToolTip(ht)
		else:
			self.bReslice.SetToolTip("")
			
	def onFilter(self, evt):
		if self.filterEvent is None:
			return
		
		if self.filtering:
			self.filtering = False
			self.hcHistory.setFilter(None)
			self.tcFilterFile.SetValue("")
		else:
			self.filtering = True
			fn = self.filterEvent.getFns()[0]
			self.hcHistory.setFilter(fn)
			self.tcFilterFile.SetValue(os.path.basename(fn))
			
	def itemSelected(self, flag, evt=None):
		self.bFilter.Enable(flag)
		self.filterEvent = evt

class HistoryCtrl(wx.ListCtrl):	
	def __init__(self, parent, history):
		self.parent = parent
		self.history = history
		self.images = history.images
		self.settings = history.settings
		
		self.filtFn = None
		
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
			
		self.refreshAll()

		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.doListSelect)
		
	def setFilter(self, filtFn):
		self.filtFn = filtFn
		self.refreshAll()

	def applyFilter(self):
		if self.filtFn is None:
			fe =  [e for e in self.history]
		else:
			fe =  [e for e in self.history if e.getFns()[0] == self.filtFn]
			
		self.filteredEvents = list(reversed(fe))

		self.listAttrs = []
		for e in self.filteredEvents:
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
				self.listAttrs.append(self.attrDeletedGc)
			elif stlTime == 0:
				self.listAttrs.append(self.attrDeletedStl)
			elif stlTime is None:
				self.listAttrs.append(None)
			elif stlTime > gcTime:
				self.listAttrs.append(self.attrStale)
			else:
				self.listAttrs.append(None)
				
		self.SetItemCount(len(self.filteredEvents))
		
	def refreshAll(self):
		self.applyFilter()
		self.SetItemCount(len(self.filteredEvents))
		for i in range(len(self.filteredEvents)):
			self.RefreshItem(i)
		
	def doListSelect(self, evt):
		x = self.selectedItem
		self.selectedItem = evt.GetIndex()
		if x is not None:
			self.RefreshItem(x)
			
		if self.selectedItem is None:
			self.parent.itemSelected(False)
			self.parent.GCodeFileExists(False)
			self.parent.StlFileExists(False)
			return
			
		e = self.filteredEvents[self.selectedItem]
		self.parent.itemSelected(True, e)
		
		fn = e.getFns()[0]
		if os.path.exists(fn):
			self.selectedExists = True
		else:
			self.selectedExists = False
		
		self.parent.GCodeFileExists(self.selectedExists, e)
		
		ex = False
		if e.getEventType() == HistoryEventEnum.SliceComplete:
			fn = e.getFns()[1]
			if os.path.exists(fn):
				ex = True
				
		self.parent.StlFileExists(ex, e)
				
		
	def doesSelectedExist(self):
		return self.selectedExists
			
	def setBasenameOnly(self, flag):
		if self.basenameonly == flag:
			return
		
		self.basenameonly = flag
		for i in range(len(self.filteredEvents)):
			self.RefreshItem(i)

	def OnGetItemText(self, item, col):
		e = self.filteredEvents[item]
		if e is None:
			return "????"
		
		if col == 0:
			fn = e.getFns()[0]
			if item != 0:
				ofn = self.filteredEvents[item-1].getFns()[0]
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
		if item < 0 or item > len(self.listAttrs):
			return None
		
		return self.listAttrs[item]

