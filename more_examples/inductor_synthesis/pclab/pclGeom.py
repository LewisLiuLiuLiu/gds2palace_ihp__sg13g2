# Copyright 2026 Dušan Grujić (dusan.grujic@etf.bg.ac.rs)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
import gdspy
import pclab.pclTech

def versiontuple(v):
    return tuple(map(int, (v.split("."))))


###############################################################################
#
#
###############################################################################

class geomBase:
    """

    Geometry base class.
    To be inherited by inductor generating functions

    """
 
    _tech = None 

    # Flag to indicate whether the polygon is automatically closed. 
    # If set to False, last point of the polygon should be the same as the first.
    # Affects the functions which draw polygons
    closed = False  

    # Flag to indicate whether to draw via array as a single via for simplified EM model
    emVias = False
        
    def __init__(self,tech=None):
        self._tech = tech   # Set the technology
        
    def setTech(self, tech):
        self._tech = tech

    def setIsClosed(self, closed):
        self.closed = closed
    
    def getIsClosed(self):
        return self.closed
    
    def setEmVias(self, emVias):
        self.emVias = emVias
    
    def getEmVias(self, emVias):
        return self.emVias
    
    def roundToGrid(self, num):
        """
        Round the number to technology grid.
        If the technology is not defined, or the grid is 0, prints the warning message and returns the same number.
        """
        if self._tech==None:
            print("WARNING: roundToGrid called, but techonology is not defined")
            return num
        grid = self._tech.getGrid()
        if grid==0.0:
            print("WARNING: roundToGrid called, but techonology grid=0.0")
            return num
        return round(num/grid)*grid

    def addPoints(self,p1,p2):
        """
        Add two points.
        Parameters:
            p1 : (x1, y1)
                x1, y1 coordinates of the first point
            p2 : (x2, y2)
                x1, y1 coordinates of the second point
        Output:
            (x1+x2,y1+y2)
                
        """
        x1 = p1[0]
        y1 = p1[1]
        x2 = p2[0]
        y2 = p2[1]
        return (x1+x2,y1+y2)

    def mulPoints(self,p1,p2):
        """
        Produce dot product of two points
        Parameters:
            p1 : (x1, y1)
                x1, y1 coordinates of the first point
            p2 : (x2, y2)
                x1, y1 coordinates of the second point
        Output:
            (x1*x2,y1*y2)
                
        """
        x1 = p1[0]
        y1 = p1[1]
        x2 = p2[0]
        y2 = p2[1]
        return (x1*x2,y1*y2)
        
    def swapXY(self, p):
        """
        Swap x and y coordinates of point
        """
        x = p[0]
        y = p[1]
        return (y,x)
    
    def translateObjs(self, obj, offset):
        # Translate given object by given offset
        tobj = list()
        for structure in obj:
            tstructure = list()
            for point in structure:
                tpoint = self.addPoints(point, offset)
                tstructure.append(tpoint)
            tobj.append(tstructure)
        return tobj

    def rotate90deg(self, obj, quadrant):
        # Rotate objects to given quadrant
        # Sign of x coordinates
        if (quadrant == 0) or (quadrant == 3):
            xs = 1
        else:
            xs = -1
        # Sign of y coordinates
        if (quadrant == 0) or (quadrant == 1):
            ys = 1
        else:
            ys = -1
        quad = (xs, ys)
        tobj = list()
        for structure in obj:
            tstructure = list()
            for point in structure:
                tpoint = self.mulPoints(point, quad)
                tstructure.append(tpoint)
            tobj.append(tstructure)
        return tobj

    def appendPoly(self, polyc1, polyc2):
        """
            Append polygons from polyc2 to polyc1
        """
        for poly in polyc2:
            polyc1.append(poly)

    def appendVias(self, vias1, vias2):
        """
            Append vias from list of vias in vias2 to vias1
        """
        for vias in vias2:
            for via in vias:
                vias1.append(via)


    def fillVias(self, rect, viaEnc, viaSize, viaSpace):
        """
            Fills a given rectangle rect with vias.
            Rectangle is defined as a tuple of xy coordinates - ((x0,y0),(x1,y1))
            If emVias is set to True, a single large via is drawn to reduce EM simulation time.
            Parameters:
                rect : 2x2 tuple
                    rectangle to fill with vias
                viaEnc : float
                    Via enclosure.
                viaSize : float
                    Via size.
                viaSpace :float
                    Via spacing.
            
            Returns a list of rectangles.

        
        """
        viaList=list()  # initialize list of generated vias
        
        point1 = rect[0]
        point2 = rect[1]
        x1 = point1[0]
        y1 = point1[1]
        x2 = point2[0]
        y2 = point2[1]

        if self.emVias:
            if x1 < x2:
                x1 = x1 + viaEnc
                x2 = x2 - viaEnc
            else:
                x1 = x1 - viaEnc
                x2 = x2 + viaEnc
            if y1 < y2:
                y1 = y1 + viaEnc
                y2 = y2 - viaEnc
            else:
                y1 = y1 - viaEnc
                y2 = y2 + viaEnc

            viaList.append( ((x1,y1),(x2,y2)) )
            return viaList     # return original rectangle undersized by via enclosure in EM mode

        if (x2>x1):
            x0 = x1
            dx = x2-x1
        else:
            x0 = x2
            dx = x1 - x2

        if (y2>y1):
            y0 = y1
            dy = y2-y1
        else:
            y0 = y2
            dy = y1 - y2

        nrows = int(math.floor((dy-2*viaEnc+viaSpace+1e-9)/(viaSize+viaSpace)))
        ncols = int(math.floor((dx-2*viaEnc+viaSpace+1e-9)/(viaSize+viaSpace)))
        
        r_off = self.roundToGrid((dy-2*viaEnc+viaSpace-nrows*(viaSize+viaSpace))/2)
        c_off = self.roundToGrid((dx-2*viaEnc+viaSpace-ncols*(viaSize+viaSpace))/2)


        for i in range(nrows):
            for j in range(ncols):
                x1 = x0+viaEnc+c_off+j*(viaSize+viaSpace)
                y1 = y0+viaEnc+r_off+i*(viaSize+viaSpace)
                x2 = x1+viaSize
                y2 = y1+viaSize
                viaList.append(((x1,y1),(x2,y2)))

        return viaList

    def makeRect(self, pl, pr):
        """
            Return a rectangle drawn as polygon
        """
        x1 = pl[0]
        y1 = pl[1]
        x2 = pr[0]
        y2 = pr[1]
        p1=(x1,y1)
        p2=(x1,y2)
        p3=(x2,y2)
        p4=(x2,y1)
        
        if self.closed:
            polygon=(p1, p2, p3, p4, p1) # Last polygon point is equal to first
        else:
            polygon=(p1, p2, p3, p4)
        return polygon        

    def poly45Deg(self, w, l, quadrant, centerX, centerY, lIsDx = False):
        # If flag lIsDx is given, l is treated as dx, otherwise l is length of the segment centerline
        RG = self.roundToGrid
        sqrt = math.sqrt
        if lIsDx:
            dx = l
        else:
            dx = l/sqrt(2)
        # Sign of x coordinates
        if (quadrant == 0) or (quadrant == 3):
            xs = 1
        else:
            xs = -1
        
        # Sign of y coordinates
        if (quadrant == 0) or (quadrant == 1):
            ys = 1
        else:
            ys = -1
        P1 = self.addPoints((-xs*RG(w/2/sqrt(2)), ys*RG(w/2/sqrt(2)) ), (centerX, centerY))
        P2 = self.addPoints( P1, (xs*RG(w/sqrt(2)), -ys*RG(w/sqrt(2))) )
        P3 = self.addPoints( P2, (xs*RG(dx), ys*RG(dx)))
        P4 = self.addPoints( P3, (-xs*RG(w/sqrt(2)),ys*RG(w/sqrt(2))))
        if self.closed:
            return [P1, P2, P3, P4, P1]
        else:
            return [P1, P2, P3, P4]


    def rectSegment(self, w, r, e, quadrant, centerX, centerY, gndContact=False):
        """
        Returs a list of coordinates for rectangular segment.
        Parameters:
            w : float
                segment width
            r : float
                outer radius
            e : float
                spacing for bridges
            quadrant : integer
                quadrant to draw segment (0 - 3)
            centerX : float
                x coordinate of octagon
            centerY : float
                Y corrdinate of octagon
        """

        # Sign of x coordinates
        if (quadrant == 0) or (quadrant == 3):
            xs = 1
        else:
            xs = -1
        
        # Sign of y coordinates
        if (quadrant == 0) or (quadrant == 1):
            ys = 1
        else:
            ys = -1
                        
        # Start constructing points
        x=r 
        y=e
        p1=(xs*x+centerX,ys*y+centerY)

        y=r
        p2=(xs*x+centerX,ys*y+centerY)  # Corner

        x=e
        p3=(xs*x+centerX,ys*y+centerY)

        y=y-w
        p4=(xs*x+centerX,ys*y+centerY)

        x=r-w
        p5=(xs*x+centerX,ys*y+centerY)
    
        y=e
        p6=(xs*x+centerX,ys*y+centerY)

        if gndContact:
            x=r 
            y=r
            wold = self.roundToGrid(w*3.0*math.sqrt(2)/4)
            w = self.roundToGrid(w*math.sqrt(2))
            P1=(xs*x+centerX,ys*(y-w/2)+centerY)
            P2=(xs*(x-w/2)+centerX,ys*y+centerY)
            P3=(xs*(x+w/2)+centerX,ys*(y+w)+centerY)
            P4=(xs*(x+w)+centerX,ys*(y+w/2)+centerY)        
            label = ((xs*(x+wold)+centerX,ys*(y+wold)+centerY),'GND')
            if self.closed:
                gndPolygon = (P1, P2, P3, P4, P1)
            else:
                gndPolygon = (P1, P2, P3, P4)

        if self.closed:
            polygon=(p1, p2, p3, p4, p5, p6, p1) # Last polygon point is equal to first
        else:
            polygon=(p1, p2, p3, p4, p5, p6)

        if gndContact:
            return (polygon, gndPolygon, label)
        else:
            return polygon        

    def octSegment(self, w, r, e, quadrant, centerX, centerY, gndContact=False):
        """
        Returs a list of coordinates for octagonal segment.
        Parameters:
            w : float
                segment width
            r : float
                outer radius
            e : float
                spacing for bridges
            quadrant : integer
                quadrant to draw segment (0 - 3)
            centerX : float
                x coordinate of octagon
            centerY : float
                Y corrdinate of octagon
        """
        
        sqrt = math.sqrt
        
        # Sign of x coordinates
        if (quadrant == 0) or (quadrant == 3):
            xs = 1
        else:
            xs = -1
        
        # Sign of y coordinates
        if (quadrant == 0) or (quadrant == 1):
            ys = 1
        else:
            ys = -1
                                                
        a=self.roundToGrid((2*r)/(sqrt(2)+2))            # x,y length of outer corner
        c=self.roundToGrid((2*r)/(sqrt(2)+2)+w/(sqrt(2)+1))  # x,y length of inner corner

        b1=r-a  # length of outer vertical side
        b2=r-c  # length of inner vertical side

        # Start constructing points
        x=r 
        y=e
        p1=(xs*x+centerX,ys*y+centerY)

        y=b1
        p2=(xs*x+centerX,ys*y+centerY)

        x=x-a
        y=y+a
        p3=(xs*x+centerX,ys*y+centerY)

        x=e
        p4=(xs*x+centerX,ys*y+centerY)

        y=y-w
        p5=(xs*x+centerX,ys*y+centerY)
    
        x=r-c
        p6=(xs*x+centerX,ys*y+centerY)

        x=r-w
        y=r-c
        p7=(xs*x+centerX,ys*y+centerY)

        y=e
        p8=(xs*x+centerX,ys*y+centerY)

        if gndContact:
            X = (2*r-a)/2
            Y = (2*b1+a)/2
            W = self.roundToGrid(w*sqrt(2))
            
            P1=(xs*(X-W/2)+centerX,ys*(Y+W/2)+centerY)
            P2=(xs*(X+W/2)+centerX,ys*(Y-W/2)+centerY)
            P3=(xs*(X+W/2+W)+centerX,ys*(Y-W/2+W)+centerY)
            P4=(xs*(X-W/2+W)+centerX,ys*(Y+W/2+W)+centerY)
            label = ((xs*(X+w*sqrt(2))+centerX,ys*(Y+w*sqrt(2))+centerY),'GND')
            if self.closed:
                gndPolygon = (P1, P2, P3, P4, P1)
            else:
                gndPolygon = (P1, P2, P3, P4)

        if self.closed:
            polygon=(p1, p2, p3, p4, p5, p6, p7, p8, p1) # Last polygon point is equal to first
        else:
            polygon=(p1, p2, p3, p4, p5, p6, p7, p8)

        if gndContact:
            return (polygon, gndPolygon, label)
        else:
            return polygon  

    def make45Bridge(self, w, l, offX, offY, originX, originY, mirror, r90, addVias, viaEnc=0.0, viaSize=1.0, viaSpace=1.0):
        """
        Draw 45 degree bridge
        w : float
            width of metal
        l : float
            bridge length
        offX : float 
            offset of bridge
        offY : float
            offset for centering of bridge (0 for center, - towards seg1)
        originX : float
            where to draw bridge X
        originY : float
            where to draw bridge Y
        mirror : Boolean
            whether to mirror on X axis
        r90 : Boolean
            whether to rotate after mirroring operation
        addVias : Boolean
            whether to add vias
        viaEnc : float
            Via enclosure.
        viaSize : float
            Via size.
        viaSpace :float
            Via spacing.
            
        Returns a tuple: (polygon, vias), where polygon and vias are tuples.
        """
    
        sqrt = math.sqrt
        addPoints = self.addPoints
        mulPoints = self.mulPoints
        fillVias = self.fillVias
        swapXY = self.swapXY

        off=offX
        x=0.0
        y=0.0
        p1=(x,y)
        x=w
        p2=(x,y)
        y=self.roundToGrid((l/2.0-off/2.0-w/2.0/(1.0+sqrt(2.0))))+offY
        p3=(x,y)
        x=x+off
        y=y+off
        p4=(x,y)
        y=l
        p5=(x,y)
        x=x-w
        p6=(x,y)
        y=self.roundToGrid((l/2.0+off/2.0+w/2.0/(1+sqrt(2))))+offY
        p7=(x,y)
        x=x-off
        y=y-off
        p8=(x,y)

        if addVias:
            tpoint=(0,-w)
            p1=addPoints(p1,tpoint)
            p2=addPoints(p2,tpoint)
            tpoint=(0,w)
            p5=addPoints(p5,tpoint)
            p6=addPoints(p6,tpoint)

        if mirror:
           mp=(w+off, 0)
           p1=addPoints(mp,mulPoints(p1,(-1,1)))
           p2=addPoints(mp,mulPoints(p2,(-1,1)))
           p3=addPoints(mp,mulPoints(p3,(-1,1)))
           p4=addPoints(mp,mulPoints(p4,(-1,1)))
           p5=addPoints(mp,mulPoints(p5,(-1,1)))
           p6=addPoints(mp,mulPoints(p6,(-1,1)))
           p7=addPoints(mp,mulPoints(p7,(-1,1)))
           p8=addPoints(mp,mulPoints(p8,(-1,1)))

        if r90:
            p1=swapXY(p1)
            p2=swapXY(p2)
            p3=swapXY(p3)
            p4=swapXY(p4)
            p5=swapXY(p5)
            p6=swapXY(p6)
            p7=swapXY(p7)
            p8=swapXY(p8)

        tpoint=(originX,originY)
        p1=addPoints(p1,tpoint)
        p2=addPoints(p2,tpoint)
        p3=addPoints(p3,tpoint)
        p4=addPoints(p4,tpoint)
        p5=addPoints(p5,tpoint)
        p6=addPoints(p6,tpoint)
        p7=addPoints(p7,tpoint)
        p8=addPoints(p8,tpoint)
        
        if addVias:
            if r90:
                vias1 =fillVias( (p1,addPoints(p2, (w, 0))) ,viaEnc, viaSize, viaSpace)
                vias2 =fillVias( (p5,addPoints(p6, (-w, 0))) ,viaEnc, viaSize, viaSpace)
            else:
                vias1 = fillVias( (p1,addPoints(p2, (0, w))) ,viaEnc, viaSize, viaSpace)
                vias2 = fillVias( (p5,addPoints(p6, (0,-w))) ,viaEnc, viaSize, viaSpace)
            vias = list()
            for via in vias1:
                vias.append(via)
            for via in vias2:
                vias.append(via)
        else:
            vias = list()
            
        if self.closed:
            polygon=(p1, p2, p3, p4, p5, p6, p7, p8, p1) # Last polygon point is equal to first
        else:
            polygon=(p1, p2, p3, p4, p5, p6, p7, p8)

        return (polygon, vias)

    def fillViasPolygon(self, polygonPoints, viaEnc, viaSize, viaSpace):
        poly = self.breakPolygon(polygonPoints)
        res = []
        for p in poly:
            res += self.fillViasSinglePolygon(p, viaEnc, viaSize, viaSpace)
        return res

    def fillViasSinglePolygon(self, polygonPoints, viaEnc, viaSize, viaSpace):
        """
            Fills a given polygon with vias.
            If emVias is set to True, a single large via is drawn to reduce EM simulation time.
            Parameters:
                polygon : polygon as list of coordinates
                    polygon to fill with vias
                viaEnc : float
                    Via enclosure.
                viaSize : float
                    Via size.
                viaSpace :float
                    Via spacing.
            
            Returns a list of rectangles.
        """
        viaList = []
        
        roundToGrid = self.roundToGrid
        # Find bounding box
        minX = 1e9
        minY = 1e9
        maxX = -1e9
        maxY = -1e9
        polygon = gdspy.Polygon(polygonPoints)
        
        # Find width of polygon
        W = 1e9
        polypoints = polygon.polygons[0]
        for i in range(0,len(polypoints)-1):
            x1, y1 = polypoints[i]
            x2, y2 = polypoints[i+1]
            if x1==x2:
                W = min(abs(y1-y2),W)
            if y1==y2:
                W = min(abs(x1-x2),W)            
        
        for point in polypoints:
            x, y = point
            if x>maxX:
                maxX = x
            if x<minX:
                minX = x
            if y>maxY:
                maxY = y
            if y<minY:
                minY = y
        
        dX = maxX - minX
        dY = maxY - minY

        #nRows = int((dY-2*viaEnc)/(viaSize+viaSpace))   # number of via rows
        nRows = int((dY-2*viaEnc+viaSpace)/(viaSize+viaSpace))   # number of via rows
        if nRows<=0:
            return []   # no vias
        #y = roundToGrid(minY + (dY-nRows*(viaSize+viaSpace)+viaSpace)/2)
        y = roundToGrid(minY + (W - int((W - 2*viaEnc+viaSpace)/(viaSize+viaSpace))*(viaSize+viaSpace)+viaSpace)/2)
        
        #while y<maxY-viaSpace-viaSize:
        for jj in range(0, nRows):
            polySet = gdspy.slice(polygon, y, 1)
            if polySet[0]==None:
                continue
            for poly1 in polySet[0].polygons:
                if polySet[1]==None:
                    continue
                for poly2 in polySet[1].polygons:
                    commonPoints1 = []
                    for point1 in poly1:
                        for point2 in poly2:
                            x1,y1=point1
                            x2,y2=point2
                            if x1==x2 and y1==y2:
                                commonPoints1.append(point1)
                    polySet2 = gdspy.slice(polygon, y+viaSize+viaEnc, 1)
                    for poly1n in polySet2[0].polygons:
                        if polySet2[1]==None:
                            continue
                        for poly2n in polySet2[1].polygons:
                            commonPoints2 = []
                            for point1n in poly1n:
                                for point2n in poly2n:
                                    x1,y1=point1n
                                    x2,y2=point2n
                                    if x1==x2 and y1==y2:
                                        commonPoints2.append(point1n)
                            if len(commonPoints1)<2 or len(commonPoints2)<2:
                                continue
                            leftX = max(min(commonPoints1[0][0],commonPoints1[1][0]),min(commonPoints2[0][0],commonPoints2[1][0]))
                            rightX = min(max(commonPoints1[0][0],commonPoints1[1][0]),max(commonPoints2[0][0],commonPoints2[1][0]))
                            topY = max(min(commonPoints1[0][1],commonPoints1[1][1]),min(commonPoints2[0][1],commonPoints2[1][1]))
                            botY = min(max(commonPoints1[0][1],commonPoints1[1][1]),max(commonPoints2[0][1],commonPoints2[1][1]))

                            nContacts = int((rightX-leftX-2*viaEnc)/(viaSize+viaSpace)) # Number of contacts
                            X = leftX + self.roundToGrid((rightX-leftX-nContacts*(viaSize+viaSpace)+viaSpace)/2)

                            for i in range(0, nContacts):
                                cont = ( (X,botY),(X+viaSize,botY+viaSize) )
                                viaList.append(cont)
                                X += viaSize+viaSpace
            y += viaSize+viaSpace
        return viaList

    def fillViasSinglePolygonDiagonal(self, polygonPoints, viaEnc, viaSize, viaSpace):
        """
            Fills a given polygon with vias.
            If emVias is set to True, a single large via is drawn to reduce EM simulation time.
            Parameters:
                polygon : polygon as list of coordinates
                    polygon to fill with vias
                viaEnc : float
                    Via enclosure.
                viaSize : float
                    Via size.
                viaSpace :float
                    Via spacing.
            
            Returns a list of rectangles.
        """
        viaList = []
        
        roundToGrid = self.roundToGrid
        # Find bounding box
        minX = 1e9
        minY = 1e9
        maxX = -1e9
        maxY = -1e9
        polygon = gdspy.Polygon(polygonPoints)
        
        # Find width of polygon
        W = 1e9
        polypoints = polygon.polygons[0]
        for i in range(0,len(polypoints)-1):
            x1, y1 = polypoints[i]
            x2, y2 = polypoints[i+1]
            if x1==x2:
                W = min(abs(y1-y2),W)
            if y1==y2:
                W = min(abs(x1-x2),W)            
        
        for point in polypoints:
            x, y = point
            if x>maxX:
                maxX = x
            if x<minX:
                minX = x
            if y>maxY:
                maxY = y
            if y<minY:
                minY = y
        
        dX = maxX - minX
        dY = maxY - minY

        nRows = int((dY-2*viaEnc+viaSpace)/(viaSize+viaSpace))   # number of via rows
        if nRows<=0:
            return []   # no vias
        y = roundToGrid(minY + (W - int((W - 2*viaEnc+viaSpace)/(viaSize+viaSpace))*(viaSize+viaSpace)+viaSpace)/2)
        
        for jj in range(0, nRows):
            polySet = gdspy.slice(polygon, y, 1)
            if polySet[0]==None:
                continue
            for poly1 in polySet[0].polygons:
                if polySet[1]==None:
                    continue
                for poly2 in polySet[1].polygons:
                    commonPoints1 = []
                    for point1 in poly1:
                        for point2 in poly2:
                            x1,y1=point1
                            x2,y2=point2
                            if x1==x2 and y1==y2:
                                commonPoints1.append(point1)
                    polySet2 = gdspy.slice(polygon, y+viaSize+viaEnc, 1)
                    for poly1n in polySet2[0].polygons:
                        if polySet2[1]==None:
                            continue
                        for poly2n in polySet2[1].polygons:
                            commonPoints2 = []
                            for point1n in poly1n:
                                for point2n in poly2n:
                                    x1,y1=point1n
                                    x2,y2=point2n
                                    if x1==x2 and y1==y2:
                                        commonPoints2.append(point1n)
                            if len(commonPoints1)<2 or len(commonPoints2)<2:
                                continue
                            leftX = max(min(commonPoints1[0][0],commonPoints1[1][0]),min(commonPoints2[0][0],commonPoints2[1][0]))
                            rightX = min(max(commonPoints1[0][0],commonPoints1[1][0]),max(commonPoints2[0][0],commonPoints2[1][0]))
                            topY = max(min(commonPoints1[0][1],commonPoints1[1][1]),min(commonPoints2[0][1],commonPoints2[1][1]))
                            botY = min(max(commonPoints1[0][1],commonPoints1[1][1]),max(commonPoints2[0][1],commonPoints2[1][1]))

                            nContacts = int((rightX-leftX-2*viaEnc)/(viaSize+viaSpace)) # Number of contacts
                            X = leftX + self.roundToGrid((rightX-leftX-nContacts*(viaSize+viaSpace)+viaSpace)/2)

                            for i in range(0, nContacts):
                                cont = ( (X,botY),(X+viaSize,botY+viaSize) )
                                viaList.append(cont)
                                X += viaSize+viaSpace
            y += viaSize+viaSpace
        return viaList

    def breakPolygon(self, polygon):
        """
        Break polygon into quads
        """
        if len(polygon)==4:
            p = [polygon]
        elif len(polygon)==6:
            # rect
            p1 = [polygon[0], polygon[1], polygon[4], polygon[5]] 
            p2 = [polygon[1], polygon[2], polygon[3], polygon[4]]
            p = [p1, p2]
        elif len(polygon)==8:
            # oct
            p1 = [polygon[0], polygon[1], polygon[6], polygon[7]] 
            p2 = [polygon[1], polygon[2], polygon[5], polygon[6]] 
            p3 = [polygon[2], polygon[3], polygon[4], polygon[5]] 
            p = [p1, p2, p3]
        
        else:
            p = []
        return p

    def nearestPoint(self, point, polygon):
        """
        Find nearest point        
        """
        d = 1e9
        x1, y1 = point
        nearestPoint = None
        for p in polygon:
            if p != point:
                x2, y2 = p
                if d > (x1-x2)**2+(y1-y2)**2:
                    d = (x1-x2)**2+(y1-y2)**2
                    nearestPoint = p
        return p            

    def oversize(self, polygon, size):
        """
        Oversize polygon by size
        """
        if self._tech==None:
            grid = 0.0
        else:
            grid = self._tech.getGrid()
        if grid==0.0:
            grid = 0.001
        # Convert list of coordinates to polygon
        tmp = gdspy.Polygon(polygon)
        oversized = gdspy.offset(tmp, size, precision=grid)
        return oversized.polygons[0]

    def makeSubstrateContacts(self, w, r, s, centerX, centerY, geomType, contEnc=0.1, contSize=0.5, contSpace=0.2, diffEnc = 0.1):
        """
            w - width of substrate contact
            r - outer radius
            s - segment spacing
            centerX, centerY - center
            geomType - type of geometry "octagon", "rect"
            Returns (m1Polygons, diffPolygons, implantPolygons, subContacts, pinLabels )
        """

        m1Polygons = []
        diffPolygons = []
        implantPolygons = []
        subContacts = []
        pinLabels = []

        roundToGrid = self.roundToGrid
        sqrt = math.sqrt
        
        if geomType == "octagon":
            makeSegment = self.octSegment
        else:
            makeSegment = self.rectSegment
    
        makeRect = self.makeRect
            
        # Make segments
        poly, gndPoly, label = makeSegment(w,r, s, 0, centerX, centerY, True)
        m1Polygons += [poly, gndPoly]
        diffPolygons += [poly]
        pinLabels.append(label)

        poly, gndPoly, label = makeSegment(w,r, s, 1, centerX, centerY, True)
        m1Polygons += [poly, gndPoly]
        diffPolygons += [poly]
        pinLabels.append(label)

        poly, gndPoly, label = makeSegment(w,r, s, 2, centerX, centerY, True)
        m1Polygons += [poly, gndPoly]
        diffPolygons += [poly]
        pinLabels.append(label)

        poly, gndPoly, label = makeSegment(w,r, s, 3, centerX, centerY, True)
        m1Polygons += [poly, gndPoly]
        diffPolygons += [poly]
        pinLabels.append(label)
        
        for poly in diffPolygons:
            implantPolygons.append(self.oversize(poly, diffEnc))
            
        # Make substrate contacts
        for poly in diffPolygons:
            subContacts +=  self.fillViasPolygon(poly, contEnc, contSize, contSpace) 

        # Make pin labels        
        
        return (m1Polygons, diffPolygons, implantPolygons, subContacts, pinLabels )

    def makeGroundShield(self, w, l, offX, offY, originX, originY, mirror, r90, addVias, viaEnc=0.0, viaSize=1.0, viaSpace=1.0):
        pass



