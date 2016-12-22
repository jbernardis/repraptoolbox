'''
Created on Dec 10, 2016

@author: Jeff
'''
PREFIX = ";@#@# "

def buildGCSuffix(slCfg, filSiz, tempsHE, tempsBed):
	s = []
	s.append("%s CFG:%s" % (PREFIX, slCfg))
	
	if filSiz is not None:
		s.append("%s FIL:%s " % (PREFIX, filSiz))
		
	if tempsHE is not None:
		s.append("%s THE:%s " % (PREFIX, tempsHE))
		
	if tempsBed is not None:
		s.append("%s TBED:%s " % (PREFIX, tempsBed))

	return s

def modifyGCSuffix(gc, slCfg, filSiz, tempsHE, tempsBed):
	sx = len(gc) - 10
	if sx < 0:
		sx = 0
		
	while sx < len(gc):
		if gc[sx].startswith(PREFIX):
			if "CFG:" in gc[sx] and slCfg is not None:
				s = gc[sx].split("CFG:")[0] + "CFG:" + slCfg
				gc[sx] = s
			elif "FIL:" in gc[sx] and filSiz is not None:
				s = gc[sx].split("FIL:")[0] + "FIL:" + filSiz
				gc[sx] = s
			elif "THE:" in gc[sx] and tempsHE is not None:
				s = gc[sx].split("THE:")[0] + "THE:" + tempsHE
				gc[sx] = s
			elif "TBED:" in gc[sx] and tempsBed is not None:
				s = gc[sx].split("TBED:")[0] + "TBED:" + tempsBed
				gc[sx] = s
		sx += 1

def parseGCSuffix(gc):
	if len(gc) < 10:
		sx = 0
	else:
		sx = -9
	suffix = [s for s in gc[sx:] if s.startswith(PREFIX)]

	slCfg = "??"
	filSiz = "??"
	tempsHE = "??"
	tempsBed = "??"
	
	for s in suffix:
		if "CFG:" in s:
			slCfg = s.split("CFG:")[1].strip()
		elif "FIL:" in s:
			filSiz = s.split("FIL:")[1].strip()
		elif "THE:" in s:
			tempsHE = s.split("THE:")[1].strip()
		elif "TBED:" in s:
			tempsBed = s.split("TBED:")[1].strip()
			
	return slCfg, filSiz, tempsHE, 	tempsBed

		
