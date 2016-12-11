
class CategoryEnum:
	fileProp = 1
	layerInfo = 2
	printStats = 3
	label = {fileProp: "File Properties", layerInfo: "Layer Information", printStats: "Print Statistics"}
	xmlLabel = {fileProp: "FileProperties", layerInfo: "LayerInformation", printStats: "PrintStatistics"}
	
class PropertyEnum:
	fileName = 11
	slicerCfg = 12
	filamentSize = 13
	temperatures = 14
	sliceTime = 15
	printEstimate = 16
	
	layerNum = 21
	minMaxXY = 22
	filamentUsed = 23
	filamentUsed0 = 230
	filamentUsed1 = 231
	filamentUsed2 = 232
	filamentUsed3 = 233
	gCodeRange = 24
	layerPrintTime = 25
	timeUntil = 26
	
	position = 31
	startTime = 32
	origEta = 33
	elapsed = 34
	remaining = 35
	revisedEta = 36
	label = {fileName : "File Name", slicerCfg: "Slicer Cfg", filamentSize: "Filament Size", temperatures: "Temperatures", sliceTime: "Slice Time", printEstimate: "Print Time Estimate",
			layerNum: "Layer Number", minMaxXY: "Min/Max X/Y", filamentUsed: "Filament Used", gCodeRange: "G Code Lines", layerPrintTime: "Layer Print Time", timeUntil: "Time Until",
			position: "Print Position", startTime: "Start Time", origEta: "Original ETA", elapsed: "Time Elapsed", remaining: "Time Remaining", revisedEta: "Revised ETA",
			filamentUsed0: "Filament Used Tool 0:", filamentUsed1: "              Tool 1:", filamentUsed2: "              Tool 2:", filamentUsed3: "              Tool 3:"}
	xmlLabel = {fileName : "FileName", slicerCfg: "SlicerCfg", filamentSize: "FilamentSize", temperatures: "Temperatures", sliceTime: "SliceTime", printEstimate: "PrintTimeEstimate",
			layerNum: "LayerNumber", minMaxXY: "MinMaxXY", filamentUsed: "FilamentUsed", gCodeRange: "GCodeLines", layerPrintTime: "LayerPrintTime", timeUntil: "TimeUntil",
			position: "PrintPosition", startTime: "StartTime", origEta: "OriginalETA", elapsed: "TimeElapsed", remaining: "TimeRemaining", revisedEta: "RevisedETA",
			filamentUsed0: "FilamentUsedTool0", filamentUsed1: "FilamentUsedTool1", filamentUsed2: "FilamentUsedTool2", filamentUsed3: "FilamentUsedTool3"}
