class RepRapEventEnums:
	PRINT_COMPLETE = 10
	PRINT_STOPPED = 11
	PRINT_STARTED = 13
	PRINT_RESUMED = 14
	PRINT_MESSAGE = 15
	QUEUE_DRAINED = 16
	RECEIVED_MSG = 17
	CONNECTED = 20
	DISCONNECTED = 21
	PRINT_ERROR = 99

class RepRapCmdEnums:
	CMD_GCODE = 1
	CMD_STARTPRINT = 2
	CMD_STOPPRINT = 3
	CMD_DRAINQUEUE = 4
	CMD_ENDOFPRINT = 5
	CMD_RESUMEPRINT = 6