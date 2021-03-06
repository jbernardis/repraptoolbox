import wx, os

from sdenums import SdEventEnum, SdStatusEnum, SdTaskEnum

class SDDir:
	def __init__(self, name, path):
		self.name = name
		self.path = path
		self.files = []
		self.dirs = []
		self.dx = 0
		self.fx = 0
		
	def addFile(self, fn, fqn=None):
		if fqn:
			self.files.append([fn, fqn])
		else:
			self.files.append([fn, fn])
		
	def addDir(self, dn, pth):
		nd = SDDir(dn, pth)
		self.dirs.append(nd)
		return nd
		
	def getDir(self, dn):
		for d in self.dirs:
			if dn == d.dirName():
				return d
		return None
	
	def fileExists(self, fl):
		a=[ai.lower() for ai in fl]
		for f in self.files:
			b=[ai.lower() for ai in f]
			if a == b:
				return True
		
		for d in self.dirs:
			if d.fileExists(fl):
				return True
			
		return False
	
	def deleteFileByName(self, fn):
		self.files = [f for f in self.files if f[1] != fn]
		for d in self.dirs:
			d.deleteFileByName(fn)
	
	def sortAll(self):
		def cmpDirs(a, b):
			return cmp(a.dirName(), b.dirName())
		
		def cmpFiles(a, b):
			return cmp(a[0], b[0])
		
		s = sorted(self.dirs, cmpDirs)
		self.dirs = s

		for d in self.dirs:
			d.sortAll()
			
		s = sorted(self.files, cmpFiles)
		self.files = s

	def dirName(self):
		return self.name
		
	def dirPath(self):
		if len(self.path) > 1 and self.path.endswith('/'):
			return self.path[:-1]
		else:
			return self.path
		
	def resetDir(self):
		self.dx = 0
	
	def nextDir(self):
		x = self.dx
		if x >= len(self.dirs):
			return None
		
		self.dx += 1
		return self.dirs[x]
	
	def findDir(self, dn):
		dl = dn.split('/')
		return self.traverse(dl)

	def traverse(self, dl):
		if dl[0] != self.name:
			return None
		
		if len(dl) == 1:
			return self

		ndl = [x for x in dl[1:]]
		for sd in self.dirs:
			d = sd.traverse(ndl)
			if d:
				return d

		return None
		
	def resetFile(self):
		self.fx = 0
	
	def nextFile(self):
		x = self.fx
		if x >= len(self.files):
			return None
		
		self.fx += 1
		return self.files[x]
	
class SDCard:
	def __init__(self, app, prtmon, printer, logger):
		self.app = app
		self.prtmon = prtmon
		self.logger = logger
		self.printer = printer
		self.status = SdStatusEnum.SD_IDLE
		self.task = None
		
	def getStatus(self):
		return self.status
		
	def startPrintFromSD(self):
		if self.status != SdStatusEnum.SD_IDLE:
			self.logger("SD Checking already started")
			return
		
		self.status = SdStatusEnum.SD_CHECKING
		self.task = SdTaskEnum.SD_PRINT_FROM
		self.printer.sendNow("M21")
		
	def startPrintToSD(self):
		if self.status != SdStatusEnum.SD_IDLE:
			self.logger("SD Checking already started")
			return
		
		self.status = SdStatusEnum.SD_CHECKING
		self.task = SdTaskEnum.SD_PRINT_TO
		self.printer.sendNow("M21")
		
	def startDeleteFromSD(self):
		if self.status != SdStatusEnum.SD_IDLE:
			self.logger("SD Checking already started")
			return
		
		self.status = SdStatusEnum.SD_CHECKING
		self.task = SdTaskEnum.SD_DELETE
		self.printer.sendNow("M21")
		
	def sdEvent(self, evt):
		if evt.event == SdEventEnum.SD_CARD_OK:
			if self.status != SdStatusEnum.SD_CHECKING:
				return
			self.status = SdStatusEnum.SD_LISTING
			self.printer.sendNow("M20")
			return
		
		if evt.event == SdEventEnum.SD_CARD_FAIL:
			if self.status != SdStatusEnum.SD_CHECKING:
				return
			self.status = SdStatusEnum.SD_IDLE
			self.logger("Error initializing SD card")
			
			msgdlg = wx.MessageDialog(self.app, "SD Card not present/failed to initialize",
					'SD Card Error', wx.OK | wx.ICON_ERROR)
			msgdlg.ShowModal()
			msgdlg.Destroy()

			return
		
		if evt.event == SdEventEnum.SD_CARD_LIST:
			if self.status != SdStatusEnum.SD_LISTING:
				return
			self.status = SdStatusEnum.SD_IDLE
			self.sdListComplete(evt.data)
			
	def sdListComplete(self, sdlist):
		self.SDroot = SDDir('', "/")
		for item in sdlist:
			if item.startswith('/'):
				item = item[1:]
				
			cd = self.SDroot
			pth = "/"
				
			l = item.split('/')
			for d in l[:-1]:
				ncd = cd.getDir(d)
				pth += d + '/'
				if ncd == None:
					ncd = cd.addDir(d, pth)
		
				cd = ncd
			cd.addFile(l[-1], fqn='/' + item)
					
				
		self.SDroot.sortAll()
		
		if self.task == SdTaskEnum.SD_PRINT_FROM:
			dlg = SDChooseFileDlg(self.app, self.SDroot, "Choose a file to print")
			while True:
				okFlag = dlg.ShowModal()
				if okFlag != wx.ID_OK:
					self.prtmon.cancelSDPrintFrom()
					break
				
				fileList = dlg.getSelection()
				if isinstance(fileList, list):
					self.prtmon.resumeSDPrintFrom(fileList)
					break
				
				msgdlg = wx.MessageDialog(self.app, "Please choose a file - not a directory - or cancel",
					'Choose file', wx.OK | wx.CANCEL | wx.ICON_INFORMATION)
				rc = msgdlg.ShowModal()
				msgdlg.Destroy()
				
				if rc != wx.ID_OK:
					self.prtmon.cancelSDPrintFrom()
					break
					
			dlg.Destroy()

		elif self.task == SdTaskEnum.SD_PRINT_TO:
			dlg = SDChooseFileDlg(self.app, self.SDroot, "Choose a target file to print to", printTo=True)
			okFlag = dlg.ShowModal()
			if okFlag == wx.ID_OK:
				fileList = dlg.getSelection()
				newFile = dlg.getNewFileName()
				target = None
				if isinstance(fileList, list):
					target = fileList
				else:
					try:
						ext = os.path.splitext(newFile)[1]
						if ext == '':
							newFile += ".g"
						target = [newFile, os.path.join(fileList.dirPath(), newFile)]
					except:
						target = None
	
				if target:						
					if self.SDroot.fileExists(target):
						msgdlg = wx.MessageDialog(self.app, "Are you sure you want to overwrite this file",
											'Confirm Overwrite', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
						rc = msgdlg.ShowModal()
						msgdlg.Destroy()
					
						if rc == wx.ID_YES:
							self.prtmon.resumeSDPrintTo(target)
					else:
						self.prtmon.resumeSDPrintTo(target)
					
				else:
					msgdlg = wx.MessageDialog(self.app, "No target file specified",
						'No Selection', wx.OK | wx.ICON_ERROR)
					rc = msgdlg.ShowModal()
					msgdlg.Destroy()
			dlg.Destroy()
		

		elif self.task == SdTaskEnum.SD_DELETE:
			dlg = SDChooseFileDlg(self.app, self.SDroot, "Choose a file to delete")
			while True:
				okFlag = dlg.ShowModal()
				if okFlag != wx.ID_OK:
					break
				
				fileList = dlg.getSelection()
				if isinstance(fileList, list):
					msgdlg = wx.MessageDialog(self.app, "Are you sure you want to delete this file",
											'Confirm', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
					rc = msgdlg.ShowModal()
					msgdlg.Destroy()
					
					if rc == wx.ID_YES:
						self.printer.sendNow("M30 " + fileList[1].lower())
						msgdlg = wx.MessageDialog(self.app, "Delete command sent",
											'Deleted', wx.OK | wx.ICON_INFORMATION)
						msgdlg.ShowModal()
						msgdlg.Destroy()
						self.SDroot.deleteFileByName(fileList[1])
						dlg.Destroy()
						dlg = SDChooseFileDlg(self.app, self.SDroot, "Choose a file to delete")
				else:	
					msgdlg = wx.MessageDialog(self.app, "Please choose a file - not a directory - or cancel",
											'Choose file', wx.OK | wx.CANCEL | wx.ICON_INFORMATION)
					rc = msgdlg.ShowModal()
					msgdlg.Destroy()
				
					if rc != wx.ID_OK:
						break
					
			dlg.Destroy()
			
		self.task = None
		
	def SDChooseFileDlg(self, sddir):
		return False, None
	
class SDChooseFileDlg(wx.Dialog):
	def __init__(self, parent, sddir, title, printTo=False):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, title)
		
		self.win = parent
		self.selection = None
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		tID = wx.NewId()
		self.tree = wx.TreeCtrl(self, tID, wx.DefaultPosition, (300, 300),
							   wx.TR_DEFAULT_STYLE
							   #| wx.TR_HIDE_ROOT
							   )
		
		self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onSelChanged, self.tree)
		self.tree.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)

		isz = (16,16)
		il = wx.ImageList(isz[0], isz[1])
		self.fldridx	 = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,	  wx.ART_OTHER, isz))
		self.fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
		self.fileidx	 = il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))

		self.tree.SetImageList(il)
		self.il = il

		self.root = self.tree.AddRoot("/")
		self.tree.SetPyData(self.root, sddir)
		self.tree.SetItemImage(self.root, self.fldridx, wx.TreeItemIcon_Normal)
		self.tree.SetItemImage(self.root, self.fldropenidx, wx.TreeItemIcon_Expanded)

		self.loadDirIntoTree(sddir, self.root)
		
		self.tree.Expand(self.root)
		self.tree.SelectItem(self.root)
		self.selection = self.tree.GetPyData(self.root)
		
		sizer.Add(self.tree, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER, 5)
		
		if printTo:
			text = "Enter new file name:"
			dc = wx.WindowDC(self)
			f = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
			dc.SetFont(f)
			sz = dc.GetTextExtent(text)

			t = wx.StaticText(self, wx.ID_ANY, text, size=sz)
			t.SetFont(f)
			sizer.AddSpacer(20)
			sizer.Add(t, 0, wx.LEFT | wx.ALIGN_LEFT, 5)
			self.tbNewFile = wx.TextCtrl(self, wx.ID_ANY, "", size=(80, -1))
			sizer.Add(self.tbNewFile, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
		else:
			self.tbNewFile = None

		btnsizer = wx.StdDialogButtonSizer()
		
		btn = wx.Button(self, wx.ID_OK)
		btn.SetHelpText("Select the file and proceed")
		btn.SetDefault()
		btnsizer.AddButton(btn)

		btn = wx.Button(self, wx.ID_CANCEL)
		btn.SetHelpText("Cancel operation")
		btnsizer.AddButton(btn)
		btnsizer.Realize()

		sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		self.SetSizer(sizer)
		sizer.Fit(self)
		
	def getSelection(self):
		return self.selection
	
	def getNewFileName(self):
		if self.tbNewFile is None:
			return None
		
		fn = self.tbNewFile.GetValue().strip()
		if fn == "":
			return None
		
		return fn
	
	def onSelChanged(self, evt):
		item = evt.GetItem()
		if item:
			self.selection = self.tree.GetPyData(item)
		
	def OnLeftDClick(self, event):
		pt = event.GetPosition();
		item = self.tree.HitTest(pt)[0]
		if item:
			self.selection = self.tree.GetPyData(item)
			self.EndModal(wx.ID_OK)
	
	def loadDirIntoTree(self, direct, tnode):
		if direct is None:
			return

		direct.resetDir()
		dn = direct.nextDir()
		while dn is not None:
			child = self.tree.AppendItem(tnode, dn.dirPath())
			self.tree.SetPyData(child, dn)
			self.tree.SetItemImage(child, self.fldridx, wx.TreeItemIcon_Normal)
			self.tree.SetItemImage(child, self.fldropenidx, wx.TreeItemIcon_Expanded)
			self.loadDirIntoTree(dn, child)
			dn = direct.nextDir()
			
		direct.resetFile()
		fn = direct.nextFile()
		while fn is not None:
			child = self.tree.AppendItem(tnode, fn[0])
			self.tree.SetPyData(child, fn)
			self.tree.SetItemImage(child, self.fileidx, wx.TreeItemIcon_Normal)
			self.tree.SetItemImage(child, self.fileidx, wx.TreeItemIcon_Selected)
			fn = direct.nextFile()