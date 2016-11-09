# This file is part of the Printrun suite.
# 
# Printrun is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Printrun is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Printrun.  If not, see <http://www.gnu.org/licenses/>.

import sys, struct, math, numpy

def cross(v1,v2):
	return [v1[1]*v2[2]-v1[2]*v2[1],v1[2]*v2[0]-v1[0]*v2[2],v1[0]*v2[1]-v1[1]*v2[0]]

def genfacet(v):
	veca=[v[1][0]-v[0][0],v[1][1]-v[0][1],v[1][2]-v[0][2]]
	vecb=[v[2][0]-v[1][0],v[2][1]-v[1][1],v[2][2]-v[1][2]]
	vecx=cross(veca,vecb)
	vlen=math.sqrt(sum(map(lambda x:x*x,vecx)))
	if vlen==0:
		vlen=1
	normal=map(lambda x:x/vlen, vecx)
	return [normal,v]

I=[
	[1,0,0,0],
	[0,1,0,0],
	[0,0,1,0],
	[0,0,0,1]
]

def transpose(matrix):
	return zip(*matrix)
	#return [[v[i] for v in matrix] for i in xrange(len(matrix[0]))]
	
def multmatrix(vector,matrix):
	return map(sum, transpose(map(lambda x:[x[0]*p for p in x[1]], zip(vector, transpose(matrix)))))
	
def applymatrix(facet,matrix=I):
	#return facet
	#return [map(lambda x:-1.0*x,multmatrix(facet[0]+[1],matrix)[:3]),map(lambda x:multmatrix(x+[1],matrix)[:3],facet[1])]
	return genfacet(map(lambda x:multmatrix(x+[1],matrix)[:3],facet[1]))
	
f=[[0,0,0],[[-3.022642, 0.642482, -9.510565],[-3.022642, 0.642482, -9.510565],[-3.022642, 0.642482, -9.510565]]]
m=[
	[1,0,0,0],
	[0,1,0,0],
	[0,0,1,1],
	[0,0,0,1]
]

def emitstl(filename,facets=[],objname="stltool_export",binary=False):
	if filename is None:
		return
	if binary:
		f=open(filename,"wb")
		buf="".join(["\0"]*80)
		buf+=struct.pack("<I",len(facets))
		facetformat=struct.Struct("<ffffffffffffH")
		for i in facets:
			l=list(i[0][:])
			for j in i[1]:
				l+=j[:]
			l+=[0]
			buf+=facetformat.pack(*l)
		f.write(buf)
		f.close()
		return
		

	f=open(filename,"w")
	f.write("solid "+objname+"\n")
	for i in facets:
		f.write("  facet normal "+" ".join(map(str,i[0]))+"\n   outer loop\n")
		for j in i[1]:
			f.write("	vertex "+" ".join(map(str,j))+"\n")
		f.write("   endloop"+"\n")
		f.write("  endfacet"+"\n")
	f.write("endsolid "+objname+"\n")
	f.close()

def is_ascii(s):
	if not all(ord(c) < 128 for c in s):
		return False
	
	return s.startswith("solid")	
		
class stl:
	def __init__(self, filename=None, name=None):
		self.facet=[[0,0,0],[[0,0,0],[0,0,0],[0,0,0]]]
		self.facets=[]
		
		self.name=name
		if name is None:
			self.name = filename
		self.insolid=0
		self.filename = filename
		self.infacet=0
		self.inloop=0
		self.facetloc=0
		self.translatex = 0
		self.translatey = 0
		self.rotation = 0
		self.filename = filename
		if filename is not None:
			self.f=list(open(filename))
			if not is_ascii(self.f[0]):
				f=open(filename,"rb")
				buf=f.read(84)
				while(len(buf)<84):
					newdata=f.read(84-len(buf))
					if not len(newdata):
						break
					buf+=newdata
				facetcount=struct.unpack_from("<I",buf,80)
				facetformat=struct.Struct("<ffffffffffffH")
				for i in xrange(facetcount[0]):
					buf=f.read(50)
					while(len(buf)<50):
						newdata=f.read(50-len(buf))
						if not len(newdata):
							break
						buf+=newdata
					fd=list(facetformat.unpack(buf))
					self.facet=[fd[:3],[fd[3:6],fd[6:9],fd[9:12]]]
					self.facets+=[self.facet]
					facet=self.facet
				f.close()
			else:
				for i in self.f:
					self.parseline(i)
					
			for f in self.facets:
				f[0] = genfacet(f[1])[0]

			self.setHull()
			self.normalize()
			
	def setFacets(self, facets):
		self.facets = facets
		self.setHull()
			
	def setName(self, name):
		self.name = name
	
	def setHull(self):
		self.projection = numpy.array([])
		self.minz = 99999
		self.maxz = -99999
		for f in self.facets:
			if f[1][0][2] < self.minz: self.minz = f[1][0][2]
			if f[1][1][2] < self.minz: self.minz = f[1][1][2]
			if f[1][2][2] < self.minz: self.minz = f[1][2][2]
			if f[1][0][2] > self.maxz: self.maxz = f[1][0][2]
			if f[1][1][2] > self.maxz: self.maxz = f[1][1][2]
			if f[1][2][2] > self.maxz: self.maxz = f[1][2][2]
			if [f[1][0][0], f[1][0][1]] not in self.projection:
				self.projection=numpy.concatenate((self.projection, [f[1][0][0], f[1][0][1]]))
			if [f[1][1][0], f[1][1][1]] not in self.projection:
				self.projection=numpy.concatenate((self.projection, [f[1][1][0], f[1][1][1]]))
			if [f[1][2][0], f[1][2][1]] not in self.projection:
				self.projection=numpy.concatenate((self.projection, [f[1][2][0], f[1][2][1]]))

		n = len(self.projection)			
		self.projection = self.projection.reshape(n/2,2)
		self.hull = self.qhull(self.projection)
		hMin = self.hull.min(axis=0)
		hMax = self.hull.max(axis=0)
		self.hxCenter = (hMin[0] + hMax[0])/2.0
		self.hyCenter = (hMin[1] + hMax[1])/2.0
		self.hxSize = hMax[0]-hMin[0]
		self.hySize = hMax[1]-hMin[1]
		self.hArea = self.hxSize * self.hySize
		self.minx = hMin[0]
		self.miny = hMin[1]
		self.maxx = hMax[0]
		self.maxy = hMax[1]

	def normalize(self):
		self.setZZero()
		self.center()
		
	def setZZero(self):		
		# drop/raise to minz == 0
		if self.minz != 0:
			for i in range(len(self.facets)):
				for j in range(3):
					self.facets[i][1][j][2] -= self.minz

	def center(self):					
		# center to 100,100
		dx = 100 - self.hxCenter
		dy = 100 - self.hyCenter
		
		for f in self.facets:
			for j in range(3):
				f[1][j][0] += dx
				f[1][j][1] += dy
				
		for h in self.hull:
			h[0] += dx
			h[1] += dy
			
		self.hxCenter += dx
		self.hyCenter += dy
			
		
	def deltaTranslation(self, dx, dy):
		self.translatex += dx
		self.translatey += dy
		
	def deltaRotation(self, da):
		self.rotation += da
		
	def applyDeltas(self):
		mods = False
		if self.rotation != 0:
			mods = True
			s = self.translate(v=[-self.hxCenter, -self.hyCenter, 0])
			s2 = s.rotate(v=[0, 0, self.rotation])
			s = s2.translate(v=[self.hxCenter, self.hyCenter, 0])
			self.facets = [f for f in s.facets]
			self.insolid = s.insolid
			self.infacet = s.infacet
			self.inloop = s.inloop
			self.facetloc = s.facetloc
			
		if self.translatex != 0 or self.translatey != 0:
			mods = True
			s = self.translate(v=[self.translatex, self.translatey, 0])
			self.facets = [f for f in s.facets]
			self.insolid = s.insolid
			self.infacet = s.infacet
			self.inloop = s.inloop
			self.facetloc = s.facetloc
	
		self.rotation = 0
		self.translatex = 0
		self.translatey = 0	
		if mods:
			self.setHull()
			
	def yzmirror(self):
		correction = self.hxCenter * 2
		nf = []
		for f in self.facets:
			for i in range(3):
				f[1][i][0] = - f[1][i][0] + correction
			a = f[1][0]
			b = f[1][1]
			c = f[1][2]
			nf.append(genfacet([b,a,c]))
		self.facets = nf
		self.setHull()
			
	def xzmirror(self):
		correction = self.hyCenter * 2
		nf = []
		for f in self.facets:
			for i in range(3):
				f[1][i][1] = - f[1][i][1] + correction
			a = f[1][0]
			b = f[1][1]
			c = f[1][2]
			nf.append(genfacet([b,a,c]))
		self.facets = nf
		self.setHull()
			
	def xymirror(self):
		nf = []
		for f in self.facets:
			for i in range(3):
				f[1][i][2] = - f[1][i][2]
			a = f[1][0]
			b = f[1][1]
			c = f[1][2]
			nf.append(genfacet([b,a,c]))
		self.facets = nf
		self.setHull()
		self.setZZero()
		
	def scalexyz(self, sx, sy, sz):
		nf = []
		cx = self.hxCenter
		cy = self.hyCenter
		for f in self.facets:
			nv = []
			for v in range(3):
				nx = (f[1][v][0] - cx) * sx + cx
				ny = (f[1][v][1] - cy) * sy + cy
				nz = f[1][v][2] * sz
				nv.append([nx, ny, nz])
			nf.append([f[0], nv])
		
		self.facets = nf
		self.setHull()
		
	def rotatexy(self, ax, ay):
		s = self.translate([-self.hxCenter, -self.hyCenter, -self.maxz/2]).rotate([ax, ay, 0]).translate([self.hxCenter, self.hyCenter, 0])
		self.facets = [f for f in s.facets]
		self.insolid = s.insolid
		self.infacet = s.infacet
		self.inloop = s.inloop
		self.facetloc = s.facetloc
		self.setHull()
		self.setZZero()
			
	def translate(self,v=[0,0,0]):
		matrix=[
		[1,0,0,v[0]],
		[0,1,0,v[1]],
		[0,0,1,v[2]],
		[0,0,0,1]
		]
		return self.transform(matrix)
	
	def rotate(self,v=[0,0,0]):
		z=v[2]
		matrix1=[
		[math.cos(math.radians(z)),-math.sin(math.radians(z)),0,0],
		[math.sin(math.radians(z)),math.cos(math.radians(z)),0,0],
		[0,0,1,0],
		[0,0,0,1]
		]
		y=v[0]
		matrix2=[
		[1,0,0,0],
		[0,math.cos(math.radians(y)),-math.sin(math.radians(y)),0],
		[0,math.sin(math.radians(y)),math.cos(math.radians(y)),0],
		[0,0,0,1]
		]
		x=v[1]
		matrix3=[
		[math.cos(math.radians(x)),0,-math.sin(math.radians(x)),0],
		[0,1,0,0],
		[math.sin(math.radians(x)),0,math.cos(math.radians(x)),0],
		[0,0,0,1]
		]
		return self.transform(matrix1).transform(matrix2).transform(matrix3)
	
	def scale(self,v=[0,0,0]):
		matrix=[
		[v[0],0,0,0],
		[0,v[1],0,0],
		[0,0,v[2],0],
		[0,0,0,1]
		]
		return self.transform(matrix)
		
		
	def transform(self,m=I):
		s=stl()
		s.filename = self.filename
		
		s.facets=[applymatrix(i,m) for i in self.facets]
		s.insolid=0
		s.infacet=0
		s.inloop=0
		s.facetloc=0
		s.name=self.name
		return s
		
		
	def clone(self, name=None):
		s=stl()
		s.filename = self.filename
		
		s.facets=[i for i in self.facets]
		s.insolid=0
		s.infacet=0
		s.inloop=0
		s.facetloc=0
		if name is None:
			s.name=self.name
		else:
			s.name = name
		s.setHull()
		return s
		
	def export(self,f=sys.stdout):
		f.write("solid "+self.name+"\n")
		for i in self.facets:
			f.write("  facet normal "+" ".join(map(str,i[0]))+"\n")
			f.write("   outer loop"+"\n")
			for j in i[1]:
				f.write("	vertex "+" ".join(map(str,j))+"\n")
			f.write("   endloop"+"\n")
			f.write("  endfacet"+"\n")
		f.write("endsolid "+self.name+"\n")
		f.flush()
		
	def parseline(self,l):
		l=l.strip()
		if l.startswith("solid"):
			self.insolid=1
			
		elif l.startswith("endsolid"):
			self.insolid=0
			return 0
		elif l.startswith("facet normal"):
			l=l.replace(",",".")
			self.infacet=11
			self.facetloc=0
			self.facet=[[0,0,0],[[0,0,0],[0,0,0],[0,0,0]]]
			self.facet[0]=map(float,l.split()[2:])
		elif l.startswith("endfacet"):
			self.infacet=0
			self.facets+=[self.facet]
			facet=self.facet
		elif l.startswith("vertex"):
			l=l.replace(",",".")
			self.facet[1][self.facetloc]=map(float,l.split()[1:])
			self.facetloc+=1
		return 1

	def qhull(self, sample):
		link = lambda a,b: numpy.concatenate((a,b[1:]))
		edge = lambda a,b: numpy.concatenate(([a],[b]))
	
		def dome(sample,base): 
			h, t = base
			dists = numpy.dot(sample-h, numpy.dot(((0,-1),(1,0)),(t-h)))
			outer = numpy.repeat(sample, dists>0, axis=0)
			
			if len(outer):
				pivot = sample[numpy.argmax(dists)]
				return link(dome(outer, edge(h, pivot)),
							dome(outer, edge(pivot, t)))
			else:
				return base
	
		if len(sample) > 2:
			axis = sample[:,0]
			base = numpy.take(sample, [numpy.argmin(axis), numpy.argmax(axis)], axis=0)
			return link(dome(sample, base),
						dome(sample, base[::-1]))
		else:
			return sample