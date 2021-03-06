import wx
import wx.propgrid as wxpg

import os
import inspect

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))

from propenums import CategoryEnum, PropertyEnum
from printstateenum import PrintState


catOrder = [CategoryEnum.fileProp, CategoryEnum.layerInfo, CategoryEnum.printStats]
propertyMap = {
		CategoryEnum.fileProp : [ 
			PropertyEnum.fileName, PropertyEnum.slicerCfg, PropertyEnum.filamentSize, PropertyEnum.temperatures, PropertyEnum.sliceTime, PropertyEnum.printEstimate],
		CategoryEnum.layerInfo : [
			PropertyEnum.layerNum, PropertyEnum.minMaxXY, PropertyEnum.filamentUsed, PropertyEnum.gCodeRange,
			PropertyEnum.layerPrintTime, PropertyEnum.timeUntil],
		CategoryEnum.printStats : [PropertyEnum.position, PropertyEnum.startTime, PropertyEnum.origEta, PropertyEnum.elapsed,
			PropertyEnum.remaining, PropertyEnum.revisedEta]
		}

toolMap = [ PropertyEnum.filamentUsed0, PropertyEnum.filamentUsed1, PropertyEnum.filamentUsed2, PropertyEnum.filamentUsed3 ]

class PropertiesDlg(wx.Frame):
	def __init__(self, parent, wparent, printerName, cb=None):
		wx.Frame.__init__(self, wparent, wx.ID_ANY, size=(500, 500))
		ico = wx.Icon(os.path.join(cmdFolder, "images", "propsico.png"), wx.BITMAP_TYPE_PNG)
		self.SetIcon(ico)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.printerName = printerName
		self.parent = parent
		self.callback = cb
		self.log = self.parent.log
		self.fileName = None
		self.sdTargetfn = None
		self.nextruders = parent.settings.nextruders
		self.printStatus = PrintState.idle
		self.setTitle()

		pgFont = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		self.pg = pg = wxpg.PropertyGrid(self,
						style=wxpg.PG_PROP_READONLY |
							  wxpg.PG_TOOLBAR)

		pg.SetFont(pgFont)

		pg.SetCaptionBackgroundColour(wx.Colour(215, 255, 215))
		pg.SetCaptionTextColour(wx.Colour(0, 0, 0))
		pg.SetMarginColour(wx.Colour(215, 255, 215))
		pg.SetCellBackgroundColour(wx.Colour(255, 255, 191))
		pg.SetCellTextColour(wx.Colour(0, 0, 0))
		pg.SetCellDisabledTextColour(wx.Colour(0, 0, 0))
		pg.SetEmptySpaceColour(wx.Colour(215, 255, 215))
		pg.SetLineColour(wx.Colour(0, 0, 0))
		
		self.properties = {}

		lines = 0		
		for cat in catOrder:
			if self.printerName is None and cat == CategoryEnum.printStats:
				continue
			
			pg.Append(wxpg.PropertyCategory(CategoryEnum.label[cat]))
			lines += 1
			for k in propertyMap[cat]:
				if k == PropertyEnum.filamentUsed and self.nextruders > 1:
					for tx in range(self.nextruders):
						pgp = wxpg.StringProperty(PropertyEnum.label[toolMap[tx]],value="")
						pg.Append(pgp)
						lines += 1
						self.properties[toolMap[tx]] = pgp
						pg.DisableProperty(pgp)
				else:
					pgp = wxpg.StringProperty(PropertyEnum.label[k],value="")
					pg.Append(pgp)
					lines += 1
					self.properties[k] = pgp
					pg.DisableProperty(pgp)

		n = pg.GetRowHeight()
		dlgVsizer = wx.BoxSizer(wx.VERTICAL)
		dlgHsizer = wx.BoxSizer(wx.HORIZONTAL)
		dlgHsizer.AddSpacer(10)
		dlgHsizer.Add(pg, 1, wx.EXPAND)
		dlgHsizer.AddSpacer(10)

		dlgVsizer.AddSpacer(10)
		dlgVsizer.Add(dlgHsizer, 1, wx.EXPAND)
		dlgVsizer.AddSpacer(10)
		self.SetSizer(dlgVsizer)
		self.SetClientSize((600, n*lines+24))
		pg.SetSplitterLeft()
		
	def onClose(self, evt):
		if self.callback is not None:
			self.callback()
			self.Destroy()
	
	def setPrintStatus(self, status):
		self.printStatus = status
		self.setTitle()
		
	def setTitle(self):
		if self.printerName is not None:
			st = PrintState.label[self.printStatus]
			s = "Printer %s status (%s)" % (self.printerName, st)
			if self.fileName is not None:
				s += " - %s" % self.fileName
			if self.sdTargetfn is not None:
				s += " -> SD:%s" % self.sdTargetfn

		else:
			if self.fileName is not None:
				s = "G Code File %s" % self.fileName
			else:
				s = ""
			
		self.SetTitle(s)
		
	def setProperty(self, pid, value):
		if pid == PropertyEnum.filamentUsed and self.nextruders > 1:
			for tx in range(self.nextruders):
				self.pg.SetPropertyValueString(self.properties[toolMap[tx]], str(value[tx]))
			
			return

		if pid not in self.properties.keys():
			self.log("Unknown property key: %s" % pid)
			return
		
		if pid == PropertyEnum.fileName:
			self.fileName = value
			self.setTitle()
			self.updateFileName()
		else:
			self.pg.SetPropertyValueString(self.properties[pid], str(value))
			
	def setSDTargetFile(self, tfn):
		self.sdTargetfn = tfn
		self.updateFileName()
		self.setTitle()
		
	def updateFileName(self):
		if self.sdTargetfn is None:
			self.properties[PropertyEnum.fileName].SetValue(self.fileName)
		else:
			self.properties[PropertyEnum.fileName].SetValue("%s->%s" % (self.fileName, self.sdTargetfn))
			
	def getStatusReport(self):
		results = {}
		for cat in catOrder:
			catvals = {}
			for k in propertyMap[cat]:
				catvals[PropertyEnum.xmlLabel[k]] = self.properties[k].GetValue()
			results[CategoryEnum.xmlLabel[cat]] = catvals

		return results
			
	def clearAllProperties(self):
		self.sdTargetfn = None
		for cat in propertyMap.keys():
			for prop in propertyMap[cat]:
				self.pg.SetPropertyValueString(self.properties[prop], "")
