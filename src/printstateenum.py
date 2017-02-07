
class PrintState:
	idle = 0
	printing = 1
	paused = 2
	sdprintingto = 3
	sdprintingfrom = 4
	label = { idle: "Idle", printing: "Printing", paused: "Paused",
			sdprintingto: "Printing to SD", sdprintingfrom: "Printing from SD" }
