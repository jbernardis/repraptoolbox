import wx
import wx.propgrid as wxpg

from propenums import CategoryEnum, PropertyEnum


catOrder = [CategoryEnum.fileProp, CategoryEnum.layerInfo, CategoryEnum.printStats]
propertyMap = {
		CategoryEnum.fileProp : [ 
			PropertyEnum.fileName, PropertyEnum.slicerCfg, PropertyEnum.filamentSize, PropertyEnum.temperatures, PropertyEnum.sliceTime],
		CategoryEnum.layerInfo : [
			PropertyEnum.layerNum, PropertyEnum.minMaxXY, PropertyEnum.filamentUsed, PropertyEnum.gCodeRange,
			PropertyEnum.layerPrintTime, PropertyEnum.timeUntil],
		CategoryEnum.printStats : [PropertyEnum.position, PropertyEnum.startTime, PropertyEnum.origEta, PropertyEnum.elapsed,
			PropertyEnum.remaining, PropertyEnum.revisedEta]
		}

class PropertiesDlg(wx.Frame):
	def __init__(self, parent, wparent, printerName):
		wx.Frame.__init__(self, wparent, wx.ID_ANY, size=(500, 500))
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.printerName = printerName
		self.parent = parent
		self.log = self.parent.log
		self.fileName = None
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
		pg.SetEmptySpaceColour(wx.Colour(255, 255, 191))
		pg.SetLineColour(wx.Colour(0, 0, 0))
		
		self.properties = {}

		lines = 0		
		for cat in catOrder:
			pg.Append(wxpg.PropertyCategory(CategoryEnum.label[cat]))
			lines += 1
			for k in propertyMap[cat]:
				pgp = wxpg.StringProperty(PropertyEnum.label[k],value="")
				pg.Append(pgp)
				lines += 1
				self.properties[k] = pgp
				pg.DisableProperty(pgp)

		n = pg.GetRowHeight()
		dlgVsizer = wx.BoxSizer(wx.VERTICAL)
		dlgHsizer = wx.BoxSizer(wx.HORIZONTAL)
		dlgHsizer.AddSpacer((10, 10))
		dlgHsizer.Add(pg, 1, wx.EXPAND)
		dlgHsizer.AddSpacer((10, 10))

		dlgVsizer.AddSpacer((10, 10))
		dlgVsizer.Add(dlgHsizer, 1, wx.EXPAND)
		dlgVsizer.AddSpacer((10, 10))
		self.SetSizer(dlgVsizer)
		self.SetClientSize((600, n*lines+24))
		pg.SetSplitterLeft()
		
	def onClose(self, evt):
		return
		
	def setTitle(self):
		s = "Printer %s data" % self.printerName
		if self.fileName is not None:
			s += " - %s" % self.fileName
			
		self.SetTitle(s)
		
	def setProperty(self, pid, value):
		if pid not in self.properties.keys():
			self.log("Unknown property key: %s" % pid)
			return
		
		self.properties[pid].SetValue(value)
		
		if pid == PropertyEnum.fileName:
			self.fileName = value
			self.setTitle()
			
	def clearAllProperties(self):
		for cat in propertyMap.keys():
			for prop in propertyMap[cat]:
				self.properties[prop].SetValue("")
