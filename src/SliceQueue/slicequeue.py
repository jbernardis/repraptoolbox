#!/bin/env python
import os
import wx
import inspect
import pickle
import time

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))

from images import Images
from settings import Settings

BUTTONDIM = (48, 48)

wildcard = "STL (*.stl)|*.stl;*STL|AMF (*.amf.xml, *.amf)|*.amf.xml;*.AMF.XML;*.amf;*.AMF|All files (*.*)|*.*"

VISIBLEQUEUESIZE = 15

class SliceFileObject:
	def __init__(self, fn):
		self.fn = fn
		self.refresh()
		
	def refresh(self):
		self.mt = time.strftime('%y/%m/%d-%H:%M:%S', time.localtime(os.path.getmtime(self.fn)))
		
	def getFn(self):
		return self.fn
	
	def getModTime(self):
		return self.mt

class SliceQueue:
	def __init__(self):
		self.fn = os.path.join(cmdFolder, "slice.queue")
		self.reload()
		self.save()
		
	def reload(self):
		try:		
			fp = open(self.fn, "rb")
			self.files = pickle.load(fp)
			fp.close()
			self.refreshAll()
		except:
			self.files = []
		
	def getList(self):
		return self.files
	
	def peek(self):
		if len(self.files) == 0:
			return None
		
		return self.files[0]
	
	def refreshPath(self, path):
		for f in self.files:
			if path == f.getFn():
				f.refresh()

	def refreshAll(self):
		for f in self.files:
			f.refresh()

	def deQueue(self, save=True):
		if len(self.files) == 0:
			return None
		
		rv = self.files[0]
		self.files = self.files[1:]
		if save:
			self.save()
		return rv
	
	def enQueuePath(self, fn, save=True):				
		pathList = [x.getFn() for x in self.files]
		if fn in pathList:
			self.refreshPath(fn)
		else:
			self.files.append(SliceFileObject(fn))
		if save:
			self.save()
		
	def delete(self, ix):
		if ix < 0 or ix >= self.__len__():
			return
		del self.files[ix]
	
	def swap(self, i, j):
		if i < 0 or i >= self.__len__():
			return
		if j < 0 or j >= self.__len__():
			return
		t = self.files[i]
		self.files[i] = self.files[j]
		self.files[j] = t
		
	def save(self):
		fp = open(self.fn, 'wb')
		pickle.dump(self.files, fp)
		fp.close()
	
	def __getitem__(self, ix):
		if ix < 0 or ix >= self.__len__():
			return None
		
		return self.files[ix]
	
	def __iter__(self):
		self.__lindex__ = 0
		return self
	
	def next(self):
		if self.__lindex__ < self.__len__():
			i = self.__lindex__
			self.__lindex__ += 1
			return self.files[i]

		raise StopIteration
	
	def __len__(self):
		return len(self.files)

class SliceQueueDlg(wx.Frame):
	def __init__(self, parent, sq):
		self.parent = parent
		self.sq = sq
		self.sq.refreshAll()
		self.sq.save()
		wx.Frame.__init__(self, None, wx.ID_ANY, "Slicing Queue", size=(800, 804))
		self.SetBackgroundColour("white")

		self.images = Images(os.path.join(cmdFolder, "images"))
		self.settings = Settings(cmdFolder)
		self.Bind(wx.EVT_CLOSE, self.doCancel)

		dsizer = wx.BoxSizer(wx.VERTICAL)
		dsizer.AddSpacer((10, 10))
		
		lbsizer = wx.BoxSizer(wx.HORIZONTAL)
		lbsizer.AddSpacer((10, 10))
		self.lbQueue = SliceQueueListCtrl(self, self.sq, self.images, self.settings.showstlbasename)
		lbsizer.Add(self.lbQueue);
		lbsizer.AddSpacer((10, 10))
		
		lbbtns = wx.BoxSizer(wx.VERTICAL)
		lbbtns.AddSpacer((10, 10))
		self.bAdd = wx.BitmapButton(self, wx.ID_ANY, self.images.pngAdd, size=BUTTONDIM)
		self.bAdd.SetToolTipString("Add new files to the slicing queue")
		self.Bind(wx.EVT_BUTTON, self.doAdd, self.bAdd)
		lbbtns.Add(self.bAdd)
		
		self.bDel = wx.BitmapButton(self, wx.ID_ANY, self.images.pngDel, size=BUTTONDIM)
		self.bDel.SetToolTipString("Remove selected file(s) from the queue")
		lbbtns.Add(self.bDel)
		self.Bind(wx.EVT_BUTTON, self.doDel, self.bDel)
		self.bDel.Enable(False)
		
		lbbtns.AddSpacer((20, 20))
		
		self.bUp = wx.BitmapButton(self, wx.ID_ANY, self.images.pngUp, size=BUTTONDIM)
		self.bUp.SetToolTipString("Move selected item up in queue")
		lbbtns.Add(self.bUp)
		self.Bind(wx.EVT_BUTTON, self.doUp, self.bUp)
		self.bUp.Enable(False)
		
		self.bDown = wx.BitmapButton(self, wx.ID_ANY, self.images.pngDown, size=BUTTONDIM)
		self.bDown.SetToolTipString("Move selected item down in queue")
		lbbtns.Add(self.bDown)
		self.Bind(wx.EVT_BUTTON, self.doDown, self.bDown)
		self.bDown.Enable(False)
		
		lbbtns.AddSpacer((20, 20))
		
		self.bView = wx.BitmapButton(self, wx.ID_ANY, self.images.pngView, size=BUTTONDIM)
		self.bView.SetToolTipString("View STL/AMF file")
		lbbtns.Add(self.bView)
		self.Bind(wx.EVT_BUTTON, self.stlView, self.bView)
		self.bView.Enable(False)
		
		lbsizer.Add(lbbtns)
		lbsizer.AddSpacer((10, 10))
		
		dsizer.Add(lbsizer)
		dsizer.AddSpacer((10,10))
		
		btnsizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.bSave = wx.BitmapButton(self, wx.ID_ANY, self.images.pngOk, size=BUTTONDIM)
		self.bSave.SetToolTipString("Save changes to queue")
		btnsizer.Add(self.bSave)
		self.Bind(wx.EVT_BUTTON, self.doSave, self.bSave)
		self.bSave.Enable(False)
		
		btnsizer.AddSpacer((20, 20))

		self.bCancel = wx.BitmapButton(self, wx.ID_ANY, self.images.pngCancel, size=BUTTONDIM)
		self.bCancel.SetToolTipString("Exit without saving")
		btnsizer.Add(self.bCancel)
		self.Bind(wx.EVT_BUTTON, self.doCancel, self.bCancel)
		
		btnsizer.AddSpacer((20, 20))
		
		self.cbBasename = wx.CheckBox(self, wx.ID_ANY, "Show basename only")
		self.cbBasename.SetToolTipString("Show only the basename of files")
		self.Bind(wx.EVT_CHECKBOX, self.checkBasename, self.cbBasename)
		self.cbBasename.SetValue(self.settings.showstlbasename)
		btnsizer.Add(self.cbBasename, 1, wx.TOP, 15)
		
		dsizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		self.SetSizer(dsizer)  
		dsizer.Fit(self)
	
	def checkBasename(self, evt):
		self.settings.showstlbasename = evt.IsChecked()
		self.lbQueue.setBaseNameOnly(self.settings.showstlbasename)
		
	def doAdd(self, evt):
		dlg = wx.FileDialog(
						self, message="Choose a file",
						defaultDir=self.settings.laststldirectory, 
						defaultFile="",
						wildcard=wildcard,
						style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR)

		if dlg.ShowModal() == wx.ID_OK:
			paths = dlg.GetPaths()
			if len(paths) > 0:
				self.bSave.Enable(True)
				nd = os.path.split(paths[0])[0]
				if nd != self.settings.laststldirectory:
					self.settings.laststldirectory = nd
				
			for path in paths:
				self.sq.enQueuePath(path, False)
					
			if len(paths) > 0:
				self.bSave.Enable(True)
				self.lbQueue.refreshAll()

	def doDel(self, evt):
		lx = self.lbQueue.getSelection()
		self.sq.delete(lx)
			
		self.lbQueue.refreshAll()			
		self.lbQueue.setSelection(None)
		self.bDel.Enable(False)
		self.bUp.Enable(False)
		self.bDown.Enable(False)
		self.bSave.Enable(True)
		
	def doUp(self, evt):
		lx = self.lbQueue.getSelection()
		self.sq.swap(lx, lx-1)
		self.lbQueue.refreshAll()
		
		self.lbQueue.setSelection(lx-1)
		self.lbQueue.EnsureVisible(lx-1)
		self.bUp.Enable((lx-1) != 0)
		self.bDown.Enable(True)
		self.bSave.Enable(True)
		
	def doDown(self, evt):
		lx = self.lbQueue.getSelection()
		self.sq.swap(lx, lx+1)
		self.lbQueue.refreshAll()

		self.lbQueue.setSelection(lx+1)
		self.lbQueue.EnsureVisible(lx+1)
		self.bUp.Enable(True)
		self.bDown.Enable((lx+2) != len(self.sq))
		self.bSave.Enable(True)
		
	def doQueueSelect(self, lx):
		if lx is None:
			self.bView.Enable(False)
			self.bDel.Enable(False)
			self.bUp.Enable(False)
			self.bDown.Enable(False)
		else:
			self.bView.Enable(True)
			self.bDel.Enable(True)
			if lx == 0:
				self.bUp.Enable(False)
			else:
				self.bUp.Enable(True)
				
			if lx == len(self.sq) - 1:
				self.bDown.Enable(False)
			else:
				self.bDown.Enable(True)
		
	def stlView(self, evt):
		lx = self.lbQueue.getSelection()
		if lx is not None:
			self.parent.displayStlFile(self.sq[lx].getFn())
					
	def doSave(self, evt):
		self.sq.save()
		self.settings.save()
		self.parent.closeStlQueue(wx.ID_OK)
		
	def doCancel(self, evt):
		if self.bSave.IsEnabled():
			dlg = wx.MessageDialog(self, "Exit without saving changes?",
					'Slicing Queue', wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
			
			rc = dlg.ShowModal()
			dlg.Destroy()

			if rc == wx.ID_YES:
				self.settings.save()
				self.sq.reload()
				self.parent.closeStlQueue(wx.ID_CANCEL)
		else:
			self.settings.save()
			self.sq.reload()
			self.parent.closeStlQueue(wx.ID_CANCEL)

class SliceQueueListCtrl(wx.ListCtrl):	
	def __init__(self, parent, sq, images, basenameonly):
		
		f = wx.Font(8,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		dc = wx.ScreenDC()
		dc.SetFont(f)
		fontHeight = dc.GetTextExtent("Xy")[1]
		
		colWidths = [500, 130]
		colTitles = ["File", "Modified"]
		
		totwidth = 20;
		for w in colWidths:
			totwidth += w
			
		
		self.attrEven = wx.ListItemAttr()
		self.attrEven.SetBackgroundColour(wx.Colour(255, 255, 255))

		self.attrOdd = wx.ListItemAttr()
		self.attrOdd.SetBackgroundColour(wx.Colour(220, 220, 220))
		
		wx.ListCtrl.__init__(self, parent, wx.ID_ANY, size=(totwidth, fontHeight*(VISIBLEQUEUESIZE+1)),
			style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES|wx.LC_SINGLE_SEL
			)

		self.parent = parent		
		self.sq = sq
		self.basenameonly = basenameonly
		self.selectedItem = None
		self.il = wx.ImageList(16, 16)
		self.il.Add(images.pngSelected)
		self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

		self.SetFont(f)
		for i in range(len(colWidths)):
			self.InsertColumn(i, colTitles[i])
			self.SetColumnWidth(i, colWidths[i])
			
		self.setArraySize()
		
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.doListSelect)

	def setArraySize(self):		
		self.SetItemCount(len(self.sq))
		
	def getSelection(self):
		return self.selectedItem
	
	def setSelection(self, lx):
		if lx is not None:
			if lx < 0 or lx >= len(self.sq):
				return
		
		self.selectedItem = lx
		self.refreshAll()
		self.parent.doQueueSelect(self.selectedItem)
		
	def getSelectedFile(self):
		if self.selectedItem is None:
			return None
		
		return self.sq[self.selectedItem].getFn()
		
	def doListSelect(self, evt):
		x = self.selectedItem
		self.selectedItem = evt.m_itemIndex
		if x is not None:
			self.RefreshItem(x)
		if self.selectedItem is not None:
			self.parent.doQueueSelect(self.selectedItem)
			
	def setBaseNameOnly(self, flag):
		if self.basenameonly == flag:
			return
		
		self.basenameonly = flag
		
		self.refreshAll()
		
	def refreshAll(self):
		self.SetItemCount(len(self.sq))
		for i in range(len(self.sq)):
			self.RefreshItem(i)

	def OnGetItemText(self, item, col):
		if col == 0:
			if self.basenameonly:
				return os.path.basename(self.sq[item].getFn())
			else:
				return self.sq[item].getFn()
		else:
			return self.sq[item].getModTime()

	def OnGetItemImage(self, item):
		if item == self.selectedItem:
			return 0
		else:
			return -1
	
	def OnGetItemAttr(self, item):
		if item % 2 == 0:
			return self.attrEven
		else:
			return self.attrOdd


		
