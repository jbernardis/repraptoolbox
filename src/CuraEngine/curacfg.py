import os.path
import sys, inspect
import wx

cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
	sys.path.insert(0, cmd_folder)

from images import Images
from categorycfg import CategoryCfg	

NBWIDTH = 600
NBHEIGHT = 600
bkgd = wx.Colour(229, 214, 169)

class ProfileMap:
	CategoryOrder = ["Quality", "Shell", "Infill", "Speed", "Travel", "Bed Adhesion", "Support"]
	PropertyOrder = {
		"Quality": ["layer_height", "layer_height_0", "outer_inset_first", "fill_perimeter_gaps",
				"z_seam_type", "infill_overlap", "skin_overlap", "infill_before_walls",
				"line_width", "wall_line_width", "skin_line_width", "infill_line_width",
				"skirt_brim_line_width", "support_line_width", "support_interface_line_width" ],
		"Shell": ["wall_line_count", "top_layers", "bottom_layers"],
		"Infill": ["infill_sparse_density", "infill_pattern"],
		"Speed": [ "speed_print", "speed_print_layer_0", "speed_travel", "speed_travel_layer_0",
				"speed_topbottom", "speed_wall", "speed_infill", "skirt_brim_speed", "speed_support",
				"acceleration_enabled", "acceleration_print", "acceleration_print_layer_0", 
				"acceleration_topbottom", "acceleration_layer_0"],
		"Travel": ["travel_avoid_other_parts", "start_layers_at_same_position", "retraction_combing",
				"travel_avoid_distance", "retraction_hop_enabled", "retraction_hop",
				"retraction_hop_only_when_collides", "retraction_hop_after_extruder_switch"],
		"Bed Adhesion": ["adhesion_type", "adhesion_extruder_nr", "skirt_line_count", "skirt_gap", 
				"skirt_brim_minimal_length", "brim_line_count", "brim_outside_only",
				"raft_airgap", "raft_surface_layers"],
		"Support": ["support_enable", "support_type", "support_extruder_nr", "support_angle",
				"support_pattern", "support_z_distance", "support_join_distance",
				"support_xy_distance", "support_interface_height", "support_interface_enable",
				"support_interface_density", "support_interface_pattern"]
		}
	Directory = "C:\\tmp\\profiles"


class MaterialMap:
	CategoryOrder = ["Characteristics", "Temperatures", "Cooling", "Retraction"]
	PropertyOrder = {
		"Characteristics": ["material_diameter", "material_flow"],
		"Temperatures": ["material_print_temperature", "material_print_temperature_layer_0", "material_bed_temperature",
						"material_bed_temperature_layer_0", "material_standby_temperature"],
		"Cooling": ["cool_fan_enabled", "cool_fan_speed", "cool_fan_speed_max", "cool_min_layer_time_fan_speed_max",
				"cool_min_layer_time", "cool_min_speed"],
		"Retraction": ["retraction_enable", "retract_at_layer_change", "retraction_amount", "retraction_speed",
					"retraction_extra_prime_amount", "retraction_min_travel", "retraction_combing"]
		}
	Directory = "C:\\tmp\\materials"

class PrinterMap:
	CategoryOrder = ["Printer", "Dual Extrusion"]
	PropertyOrder = {
		"Printer" : [ 
			"machine_start_gcode", "machine_end_gcode", "machine_width", "machine_depth", "machine_height",
			"machine_center_is_zero", "machine_heated_bed", "machine_extruder_count",
			"machine_nozzle_size", "machine_nozzle_size_1", "machine_nozzle_size_2", "machine_nozzle_size_3",
			"machine_max_acceleration_x", "machine_max_acceleration_y", "machine_acceleration"],
		"Dual Extrusion" : [
			"prime_tower_enable", "prime_tower_size", "prime_tower_position_x", "prime_tower_position_y"]
		}
	Directory = "C:\\tmp\\printers"

class NotebookPage:
	profile = 0
	material = 1
	printer = 2

class CuraCfgDlg(wx.Frame):
	def __init__(self, settings, curasettings, cb=None):
		wx.Frame.__init__(self, None, title="Cura Engine Configuration")
		self.Bind(wx.EVT_CLOSE, self.onClose)
		
		self.settings = settings
		self.callback = cb
		
		ico = wx.Icon(os.path.join(cmd_folder, "images", "curacfg.png"), wx.BITMAP_TYPE_PNG)
		self.SetIcon(ico)

		self.images = Images(os.path.join(cmd_folder, "images"))
		self.nbil = wx.ImageList(16, 16)
		self.nbilModifiedIdx = self.nbil.Add(self.images.pngModified)
		self.nbilUnmodifiedIdx = self.nbil.Add(self.images.pngUnmodified)

		sizer = wx.BoxSizer(wx.VERTICAL)
		
		nbFont = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		self.nb = wx.Notebook(self, style=wx.NB_TOP, size=(600, 400))
		self.nb.SetBackgroundColour(bkgd)
		self.nb.SetFont(nbFont)
		self.nb.AssignImageList(self.nbil)
		self.Show()
		
		ProfileMap.Directory = os.path.join(self.settings.cfgdirectory, "profile")
		MaterialMap.Directory = os.path.join(self.settings.cfgdirectory, "material")
		PrinterMap.Directory = os.path.join(self.settings.cfgdirectory, "printer")

		self.profileCfg = CategoryCfg(self, self.nb, NotebookPage.profile, self.images, ProfileMap, curasettings)
		self.nb.AddPage(self.profileCfg, "Profile", imageId=self.nbilUnmodifiedIdx)

		self.materialCfg = CategoryCfg(self, self.nb, NotebookPage.material, self.images, MaterialMap, curasettings)
		self.nb.AddPage(self.materialCfg, "Material", imageId=self.nbilUnmodifiedIdx)
		
		self.printerCfg = CategoryCfg(self, self.nb, NotebookPage.printer, self.images, PrinterMap, curasettings)
		self.nb.AddPage(self.printerCfg, "Printer", imageId=self.nbilUnmodifiedIdx)
		
		self.profileCfg.initialSelection(settings.profilechoice)
		self.materialCfg.initialSelection(settings.materialchoice[0])
		self.printerCfg.initialSelection(settings.printerchoice)

		sizer.Add(self.nb)
		self.SetSizer(sizer)
		self.Fit()
		
		if self.settings.cfgdlgposition is not None:
			self.SetPosition(self.settings.cfgdlgposition)
		
	def onClose(self, evt):
		self.nb.SetFocus()
		wx.CallLater(10, self.checkForClosure)
		
	def checkForClosure(self):
		if self.profileCfg.hasBeenModified() or self.materialCfg.hasBeenModified() or self.printerCfg.hasBeenModified():
			dlg = wx.MessageDialog(self, "Are you sure you want to exit?\n"
				"You have unsaved changes on one or more of the tabs",
				"Confirm Lose unsaved changes", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
			rc = dlg.ShowModal()
			dlg.Destroy()
			
			if rc == wx.ID_NO:
				return

		if self.callback is not None:
			self.callback()
			
		self.terminate()
		
	def terminate(self):
		self.settings.cfgdlgposition = self.GetPosition()
		self.Destroy()
		
	def updateTab(self, pageid, modflag):
		if modflag:
			self.nb.SetPageImage(pageid, imageId=self.nbilModifiedIdx)
		else:
			self.nb.SetPageImage(pageid, imageId=self.nbilUnmodifiedIdx)



