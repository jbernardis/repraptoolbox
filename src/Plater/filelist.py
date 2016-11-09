import wx

class FileItem:
	def __init__(self, userData):
		self.userData = userData
		
class FileList(wx.ListBox):
	def __init__(self, parent):
		self.files = []
		self.parent = parent
		f = wx.Font(8,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		dc = wx.ScreenDC()
		dc.SetFont(f)
		fontHeight = dc.GetTextExtent("Xy")[1]

		wx.ListBox.__init__(self, parent, wx.ID_ANY, size=(400, fontHeight*10), style=wx.LB_SINGLE + wx.LB_NEEDED_SB)
		self.Bind(wx.EVT_LISTBOX, self.doClick)

		self.SetFont(f)
		
	def doClick(self, evt):
		s = self.GetSelection()
		if s != wx.NOT_FOUND:
			self.parent.setHullSelection(self.files[s].userData.getSeqNbr())
		
	def addFile(self, userData):
		self.Append(userData.getName())
		self.files.append(FileItem(userData))
		self.SetSelection(len(self.files)-1)
		
	def refreshFilesList(self, seq):
		for fx in range(len(self.files)):
			if self.files[fx].userData.getSeqNbr() == seq:
				self.SetString(fx, self.files[fx].userData.getName())
				break
		
	def getStlObjects(self):
		objs = []
		for f in self.files:
			objs.append(f.userData.getStlObj())
		return objs
		
	def countFiles(self):
		return len(self.files)
	
	def delFileByIndex(self, fx):
		if fx < 0 or fx >= len(self.files):
			return
		
		self.Delete(fx)
		
		del(self.files[fx])
		self.SetSelection(wx.NOT_FOUND)
	
	def getUserDataByIndex(self, fx):
		if fx < 0 or fx >= len(self.files):
			return None
		return self.files[fx].userData
	
	def findUserDataBySeq(self, seq):
		for fi in self.files:
			if fi.userData.getSeqNbr() == seq:
				return fi.userData
			
		return None
	
	def setSelection(self, seq):
		for fx in range(len(self.files)):
			if self.files[fx].userData.getSeqNbr() == seq:
				self.SetSelection(fx)
		
	def delAll(self):
		self.Clear()
		self.files = []
	
	def getSelection(self):
		fx = self.GetSelection()
		if fx == wx.NOT_FOUND:
			return None
		
		fi = self.files[fx]
		return fi.userData
	
	def getSelectionIndex(self):
		return self.GetSelection()
