import wx

from managemacros import ManageMacros

BUTTONDIMWIDE = (96, 48)
BASE_ID = 2000

class MacroDialog(wx.Frame):
	def __init__(self, parent, wparent, reprap, prtName):
		self.parent = parent
		self.wparent = wparent
		self.log = self.parent.log
		self.reprap = reprap
		self.settings = self.parent.settings
		self.mmdlg = None
		self.macroList = MacroList(self.settings)
		
		wx.Frame.__init__(self, wparent, wx.ID_ANY, title="%s macros" % prtName)
		self.Show()
		
		self.Bind(wx.EVT_CLOSE, self.onClose)
		sizer = wx.BoxSizer(wx.VERTICAL)
		hsizer = None

		i = 0
		self.macroMap = []		
		for k in self.macroList:
			if (i % 3) == 0:
				if hsizer:
					sizer.AddSpacer(10)
					hsizer.AddSpacer(10)
					sizer.Add(hsizer)
				hsizer = wx.BoxSizer(wx.HORIZONTAL)
				
			self.macroMap.append(k)
			b = wx.Button(self, BASE_ID + i, k, size=BUTTONDIMWIDE)
			i += 1
			self.Bind(wx.EVT_BUTTON, self.runMacro, b)
			hsizer.AddSpacer(10)
			hsizer.Add(b)
			
		sizer.AddSpacer(10)
		sizer.Add(hsizer)
		
		sizer.AddSpacer(30)
		bsz = [x for x in BUTTONDIMWIDE]
		bsz[0] *= 2
		self.bManage = wx.Button(self, wx.ID_ANY, "Manage Macros", size=bsz)
		sizer.Add(self.bManage, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		sizer.AddSpacer(10)
		self.Bind(wx.EVT_BUTTON, self.manageMacros, self.bManage)

		self.SetSizer(sizer)
		sizer.Fit(self)
		
	def manageMacros(self, evt):
		if self.mmdlg is None:
			self.mmdlg = ManageMacros(self, self.settings, self.parent.images, self.settings.macroOrder, self.settings.macroList, self.manageDone)
			self.mmdlg.Show()
			self.bManage.Enable(False)

	def manageDone(self, rc):
		if rc:
			mo, mfn = self.mmdlg.getData()
		self.mmdlg.Destroy()
		self.mmdlg = None
		self.bManage.Enable(True)
		if rc:
			self.settings.macroOrder = mo
			self.settings.macroList = mfn
		
	def onClose(self, evt):
		self.parent.onMacroExit()
		
	def runMacro(self, evt):
		kid = evt.GetId() - BASE_ID
		if kid < 0 or kid >= len(self.macroMap):
			self.log("Invalid ID in runmacro: %d" % kid)
			return
	
		mn = self.macroMap[kid]	
		self.log("Running macro \"%s\"" % mn)

		fn = self.macroList.getFileName(mn)		
		try:
			l = list(open(fn))
		except:
			self.log("Unable to open macro file: " + fn)
			return
		
		for ln in l:
			self.reprap.sendNow(ln)

		
class MacroList:
	def __init__(self, settings):
		self.ml = settings.macroList
		self.keyList = settings.macroOrder
				
	def __iter__(self):
		self.__mindex__ = 0
		return self
	
	def next(self):
		if self.__mindex__ < self.__len__():
			i = self.__mindex__
			self.__mindex__ += 1
			return self.keyList[i]

		raise StopIteration
	
	def __len__(self):
		return len(self.keyList)
	
	def getFileName(self, key):
		if key in self.ml.keys():
			return self.ml[key]
		else:
			return None
	


