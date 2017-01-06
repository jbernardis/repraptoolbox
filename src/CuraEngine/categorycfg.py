#!/bin/env python
import wx
import os
import json

from propertiesgrid import PropertiesGrid 

class SaveDlg(wx.Dialog):
	def __init__(self, parent, images, flist, dftx, cfgdir):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Save Configuration")
		
		self.parent = parent
		self.cfgdir = cfgdir
		
		if dftx < 0:
			dftx = 0
			
		if len(flist) == 0:
			dftVal = ""
		else:
			dftVal = flist[dftx]
		
		self.cbFileList = wx.ComboBox(self, wx.ID_ANY, dftVal,
				size=(160, -1), choices=flist,
				style = wx.CB_DROPDOWN | wx.CB_SORT)
		
		bkgd = self.parent.GetBackgroundColour()

		self.bSave = wx.BitmapButton(self, wx.ID_ANY, images.pngSave, size=(32, 32), style=wx.NO_BORDER)
		self.bSave.SetBackgroundColour(bkgd)
		self.bSave.SetToolTipString("Save the current configuration values")
		self.Bind(wx.EVT_BUTTON, self.onBSave, self.bSave)
		
		self.bCancel = wx.BitmapButton(self, wx.ID_ANY, images.pngCancel, size=(32, 32), style=wx.NO_BORDER)
		self.bCancel.SetBackgroundColour(bkgd)
		self.bCancel.SetToolTipString("Cancel save operation")
		self.Bind(wx.EVT_BUTTON, self.onBCancel, self.bCancel)
		
		sz = wx.BoxSizer(wx.HORIZONTAL)
		sz.AddSpacer((10, 10))
		sz.Add(self.cbFileList, 1, wx.TOP, 5)
		sz.AddSpacer((10, 10))
		sz.Add(self.bSave)
		sz.AddSpacer((5, 5))
		sz.Add(self.bCancel)
		sz.AddSpacer((10, 10))
		
		self.SetSizer(sz)
		self.Fit()
		
	def getFn(self):
		return self.cbFileList.GetValue()
		
	def onBCancel(self, evt):
		self.EndModal(wx.ID_CANCEL)
		
	def onBSave(self, evt):
		cfgfn = self.cbFileList.GetValue()
		fn = os.path.join(self.cfgdir, cfgfn + ".ini")
		if os.path.exists(fn):
			dlg = wx.MessageDialog(self, "Configuration file\n\n"
				" %s\n\n"
				"Already exists.  Do you want to over-write?" % fn,
				"Confirm file over-write", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
			rc = dlg.ShowModal()
			dlg.Destroy()
			
			if rc == wx.ID_NO:
				return

		self.EndModal(wx.ID_SAVE)

class CategoryCfg(wx.Panel):
	def __init__(self, gparent, parent, pageid, images, pmap, definitions):
		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(600, 400))
		self.Bind(wx.EVT_CLOSE, self.onClose)
		
		self.cfgDir = pmap.Directory
		self.pageid = pageid
		self.images = images
		self.gparent = gparent
		self.parent = parent
		
		bkgd = self.parent.GetBackgroundColour()
		
		self.buildFileLists()
		self.chCfgFile = wx.Choice(self, wx.ID_ANY, choices=self.cfgNameList, size=(150, -1))
		self.Bind(wx.EVT_CHOICE, self.onChCfgFile, self.chCfgFile)
		self.chCfgFile.SetSelection(0)
		self.currentChoice = 0
		
		self.bSave = wx.BitmapButton(self, wx.ID_ANY, images.pngSave, size=(32, 32), style=wx.NO_BORDER)
		self.bSave.SetBackgroundColour(bkgd)
		self.bSave.SetToolTipString("Save the current configuration values")
		self.Bind(wx.EVT_BUTTON, self.onBSave, self.bSave)
		
		self.bDelete = wx.BitmapButton(self, wx.ID_ANY, images.pngDel, size=(32, 32), style=wx.NO_BORDER)
		self.bDelete.SetBackgroundColour(bkgd)
		self.bDelete.SetToolTipString("Delete the currently selected configuration file")
		self.Bind(wx.EVT_BUTTON, self.onBDelete, self.bDelete)
		self.bDelete.Enable(False)
		
		self.props = PropertiesGrid(self, pmap.CategoryOrder, pmap.PropertyOrder, definitions)
		
		sz = wx.BoxSizer(wx.VERTICAL)
		sz.AddSpacer((10, 10))
		
		sztb = wx.BoxSizer(wx.HORIZONTAL)
		sztb.AddSpacer((10, 10))
		sztb.Add(self.chCfgFile, 1, wx.TOP, 5)
		sztb.Add(self.bSave)
		sztb.Add(self.bDelete)
		sz.Add(sztb)
		sz.AddSpacer((10, 10))
		
		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer((10, 10))
		hsz.Add(self.props, 1, wx.EXPAND)
		hsz.AddSpacer((10, 10))
		sz.Add(hsz, 1, wx.EXPAND)
		sz.AddSpacer((10, 10))
		
		self.SetSizer(sz)
		
	def buildFileLists(self):
		cf = os.listdir(self.cfgDir)
		self.cfgFileList = [os.path.splitext(os.path.basename(fn))[0] for fn in cf if fn.lower().endswith(".ini")]
		self.cfgNameList = ["<default>"] + self.cfgFileList
		
	def hasBeenModified(self):
		return self.props.hasBeenModified()
		
	def onChCfgFile(self, evt):
		chx = self.chCfgFile.GetSelection()
		if chx == wx.NOT_FOUND:
			return
		
		if chx == self.currentChoice:
			return
		
		if self.props.hasBeenModified():
			dlg = wx.MessageDialog(self, "If you change configuration files\n"
				"you will lose unsaved changes to this configuration.\n\nContinue?",
				"Confirm configuration change", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
			rc = dlg.ShowModal()
			dlg.Destroy()
			
			if rc == wx.ID_NO:
				self.chCfgFile.SetSelection(self.currentChoice)
				return
		
		self.currentChoice = chx
		if chx == 0:
			self.props.setOverlay(None)
			self.bDelete.Enable(False)
		else:
			self.props.setOverlay(os.path.join(self.cfgDir, self.cfgNameList[chx] + ".ini"))
			self.bDelete.Enable(True)
			
	def setModified(self, flag):
		self.gparent.updateTab(self.pageid, flag)
		
	def onBSave(self, evt):
		dlg = SaveDlg(self, self.images, self.cfgFileList, self.currentChoice-1, self.cfgDir)
		rc = dlg.ShowModal()
		
		if rc == wx.ID_SAVE:
			fn = dlg.getFn()
			cfgFn = os.path.join(self.cfgDir, fn + ".ini")
			
		dlg.Destroy()
		
		if rc == wx.ID_CANCEL:
			return
		
		cfg = self.props.getNonDefaultProperties()
		
		with open(cfgFn, 'w') as outfile:
			json.dump(cfg, outfile)
		
		self.buildFileLists()
		self.chCfgFile.SetItems(self.cfgNameList)
		
		try:
			self.currentChoice = self.cfgNameList.index(fn)
		except:
			self.currentChoice = 0
		self.bDelete.Enable(self.currentChoice != 0)
		self.chCfgFile.SetSelection(self.currentChoice)
		self.props.setModified(False)
		
	def onBDelete(self, evt):
		fn = self.cfgNameList[self.currentChoice]
		
		dlg = wx.MessageDialog(self, "Are you sure you want to delete\nconfiguration file \"%s\"" % fn,
			"Delete Confirmation", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
		rc = dlg.ShowModal()
		dlg.Destroy()
		
		if rc == wx.ID_NO:
			return

		os.unlink(os.path.join(self.cfgDir, fn + ".ini"))
		self.buildFileLists()
		self.chCfgFile.SetItems(self.cfgNameList)
		self.props.setOverlay(None)
		self.currentChoice = 0
		self.chCfgFile.SetSelection(0)
		self.bDelete.Enable(False)
			
	def onClose(self, evt):
		self.Destroy()
		
	def log(self, msg):
		dlg = wx.MessageDialog(self, msg, "Program error", wx.OK | wx.ICON_ERROR)
		dlg.ShowModal()
		dlg.Destroy()
