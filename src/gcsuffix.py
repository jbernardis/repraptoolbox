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

		
