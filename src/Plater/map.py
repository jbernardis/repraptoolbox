def validPt(x, y, tx, ty, nx, ny):
	if x < 0 or y < 0:
		return False
	if x > tx-nx or y > ty-ny:
		return False
	
	return True

def spiral(needx, needy, totalx, totaly):
	cx = totalx/2
	cy = totaly/2
	loops = max(cx, cy) + 1
	
	if validPt(cx, cy, totalx, totaly, needx, needy):
		yield cx, cy
	
	for d in range(1, loops):
		for dx in range(-d, d):
			if validPt(cx+dx, cy+d, totalx, totaly, needx, needy):
				yield cx+dx, cy+d
			
		for dy in range(d, -d, -1):
			if validPt(cx+d, cy+dy, totalx, totaly, needx, needy):
				yield cx+d, cy+dy
			
		for dx in range(d, -d, -1):
			if validPt(cx+dx, cy-d, totalx, totaly, needx, needy):
				yield cx+dx, cy-d
			
		for dy in range(-d, d):
			if validPt(cx-d, cy+dy, totalx, totaly, needx, needy):
				yield cx-d, cy+dy

def row(needx, needy, totalx, totaly):
	by = totaly - needy
	bx = totalx - needx
	for y in range(by):
		for x in range(bx):
			yield x,y

def column(needx, needy, totalx, totaly):
	by = totaly - needy
	bx = totalx - needx
	for x in range(bx):
		for y in range(by):
			yield x,y


class Map:
	def __init__(self, buildarea, strategy):
		self.width = int(buildarea[0])
		self.height = int(buildarea[1])
		self.strategy = strategy
		self.map = [[0 for j in range(self.width)] for i in range(self.height)]
		
	def mark(self, sx, sy, width, height):
		for x in range(int(width)):
			for y in range(int(height)):
				if sx+x >= 0 and sx+x < self.width and sy+y >= 0 and sy+y <self.height:
					self.map[sx+x][sy+y] = 1
					
	def fits(self, x, y, width, height):
		for dx in range(int(width)):
			for dy in range(int(height)):
				try:
					if self.map[x+dx][y+dy] != 0:
						return False
				except:
					return False
		return True
	
					
	def find(self, width, height):
		if self.strategy == "row":
			gen = row
		elif self.strategy == "spiral":
			gen = spiral
		else: # strategy assumed to be "column"
			gen = column
			
		for x,y in gen(int(width), int(height), self.width, self.height):
			if self.fits(x, y, width, height):
				return (x,y)

		return (None, None)