import wx


class GcodeListCtrl(wx.ListCtrl):	
	def __init__(self, parent, gcode, images):
		
		f = wx.Font(8,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		dc = wx.ScreenDC()
		dc.SetFont(f)
		self.gcode = gcode
		fontHeight = dc.GetTextExtent("Xy")[1]
		
		self.useLineNumbers = False
		
		colWidths = [300]
		colTitles = [""]
		
		totwidth = 20;
		for w in colWidths:
			totwidth += w
			
		wx.ListCtrl.__init__(self, parent, wx.ID_ANY, size=(totwidth, fontHeight*40),
			style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_SINGLE_SEL|wx.LC_NO_HEADER
			)

		self.parent = parent		
		self.selectedItem = None
		self.bracketStart = None
		self.bracketEnd = None
		self.selectedExists = False
		
		self.attrEven = wx.ListItemAttr()
		self.attrEven.SetBackgroundColour(wx.Colour(255, 255, 255))

		self.attrOdd = wx.ListItemAttr()
		self.attrOdd.SetBackgroundColour(wx.Colour(220, 220, 220))
		
		self.il = wx.ImageList(16, 16)
		self.il.Add(images.pngEmpty)
		self.il.Add(images.pngSelected)
		self.il.Add(images.pngBrstart)
		self.il.Add(images.pngBrstartsel)
		self.il.Add(images.pngBrstartend)
		self.il.Add(images.pngBrstartendsel)
		self.il.Add(images.pngBrend)
		self.il.Add(images.pngBrendsel)
		self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

		self.SetFont(f)
		for i in range(len(colWidths)):
			self.InsertColumn(i, colTitles[i])
			self.SetColumnWidth(i, colWidths[i])
			
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.doListSelect)
		self.startLine = 0
		self.endLine = None
		self.SetItemCount(0)
		
	def setBracketStart(self):
		if self.selectedItem is None:
			return self.getBracket()
		
		self.bracketStart = self.selectedItem
		if self.bracketEnd is None or self.bracketEnd < self.bracketStart:
			self.bracketEnd = self.selectedItem
		self.refreshList()
		return self.getBracket()
		
	def setBracketEnd(self):
		if self.selectedItem is None:
			return self.getBracket()
		
		self.bracketEnd = self.selectedItem
		if self.bracketStart is None or self.bracketEnd < self.bracketStart:
			self.bracketStart = self.selectedItem
		self.refreshList()
		return self.getBracket()
	
	def getBracket(self):
		if self.bracketStart is None or self.bracketEnd is None or self.startLine is None:
			return (None, None)
		
		return (self.bracketStart+self.startLine, self.bracketEnd+self.startLine)
		
	def setLineNumbers(self, flag=True):
		self.useLineNumbers = flag
		self.refreshList()
		
	def doListSelect(self, evt):
		x = self.selectedItem
		self.selectedItem = evt.GetIndex()
		if x is not None:
			self.RefreshItem(x)
		self.parent.reportSelectedLine(self.startLine+evt.GetIndex())
		
	def getSelectedLine(self):
		if self.selectedItem is None:
			return self.startLine
		else:
			return self.startLine + self.selectedItem
		
	def setGCode(self, gcode):
		self.gcode = gcode
		
	def setLayerBounds(self, bounds):
		self.selectedItem = None
		self.bracketStart = None
		self.bracketEnd = None
		self.startLine = bounds[0]
		self.endLine = bounds[1]
		self.refreshList()
		
	def refreshList(self):
		if self.endLine is None:
			return
			
		count = self.endLine-self.startLine+1
		self.SetItemCount(count)
		self.RefreshItems(0, count-1)

	def OnGetItemText(self, item, col):
		if self.useLineNumbers:
			txt = "%6d: " % (self.startLine+item+1)
		else:
			txt = ""
		return txt + self.gcode[self.startLine+item].rstrip()

	def OnGetItemImage(self, item):
		if item == self.selectedItem:
			if item == self.bracketStart:
				if item == self.bracketEnd:
					return 5
				else:
					return 3
			else:
				if item == self.bracketEnd:
					return 7
				else:
					return 1
		else:
			if item == self.bracketStart:
				if item == self.bracketEnd:
					return 4
				else:
					return 2
			else:
				if item == self.bracketEnd:
					return 6
				else:
					return 0
	
	def OnGetItemAttr(self, item):
		if item % 2 == 0:
			return self.attrEven
		else:
			return self.attrOdd

