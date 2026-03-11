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

from pclab.pclGeom import *
import math

###############################################################################
#
# Balun 4 + 3 windings
#
###############################################################################

class balun4x3(geomBase):
    """
        Balun 4 + 3 windings
    """

    _r = None
    _w = None
    _s = None

    _signalLayer = None     # Name of signal layer
    _underPassLayer = None  # Name of under pass layer

    _viaLayer = None    # Name of via layer
    _viaEnc = 0
    _viaSize = 0
    _viaSpace = 0

    _geomType = None
    
    _centerX = 0.0
    _centerY = 0.0
    
    def __init__(self,tech=None):
        self._tech = tech   # Set the technology

    def setupGeometry(self, r, w, s, signalLayer, underPassLayer, geomType="octagon", centerX = None, centerY = None, subRingSpace=0.0, subRingW=0.0, diffLayer=None, implantLayer=None, contSpaceMult=4.0):
        """
            Setup balun 4x3 geometry
            r : float
                outer inductor dimension
            w : float
                winding line width
            s : foat
                winding spacing
            signalLayer : string
                signal layer name
            underPassLayer : string
                underpass layer name
            geomType : string
                Type of geometry. Allowed values : "rect", "octagon"
            centerX : float
                Center of inductor x coordinate
            centerY : float
                Center of inductor y coordinate
        """
        self._r = r
        self._w = w
        self._s = s
        self._signalLayer = signalLayer
        self._underPassLayer = underPassLayer
        if (geomType != "rect") and (geomType != "octagon"):
            print("WARNING:balun4x3::setupGeometry: Unknown geometry type. Setting to octagonal.")
            self._geomType = "octagon"
        else:
            self._geomType = geomType
                
        if centerX == None:
            self._centerX = 0
        else:
            self._centerX = centerX
            
        if centerY == None:
            self._centerY = 0
        else:
            self._centerY = centerY
            
        # Find via, find via rules
        viaLay = self._tech.findViaTopMet(signalLayer)
        if viaLay == None:
            print("ERROR:balun4x3::setupGeometry: Signal layer " + signalLayer + " does not have any vias connecting to it from underside.")
            return
        
        viaName = viaLay.name
        self._viaLayer = viaName
        self._viaEnc = self._tech.getDRCRule(viaName, "viaEnc")
        self._viaSize = self._tech.getDRCRule(viaName, "viaSize")
        self._viaSpace = self._tech.getDRCRule(viaName, "viaSpace")

        #        
        # Substrate ring parameters
        #
        if diffLayer!=None:
            self._genSubstrateContact = True
            contLay = self._tech.findViaBotMet(diffLayer).name
            if contLay == None:
                print("ERROR:inductorSE::setupGeometry: Diffusion layer " + diffLayer + " does not have any vias connecting to it from top.")
                return

            self._diffLayer = diffLayer
            self._impLayer = implantLayer
            
            if implantLayer!=None:
                self._diffEnc = self._tech.getDRCRule(implantLayer, "enclosure")
            else:
                self._diffEnc = 0            

            self._contLayer = contLay
            #print contLay
            self._contEnc = self._tech.getDRCRule(contLay, "viaEnc")
            self._contSize = self._tech.getDRCRule(contLay, "viaSize")
            self._contSpace = self._tech.getDRCRule(contLay, "viaSpace") * contSpaceMult

            self._m1Layer = self._tech.findTopMetVia(contLay).name
            self._subRingSpace = subRingSpace
            self._subRingW = subRingW
            
        else:
            self._genSubstrateContact = False
                    
        
        # Dimension check: return False if diameter is too small
        return r>=self.get_min_diameter()


    def get_min_diameter(self):

        return balun_MxN_get_min_diameter(self,4,3)


    def genGeometry(self):
        """
        Generate geometry for 4x3 balun
        returns polygon collections
        
        """    

        roundToGrid = self.roundToGrid
        sqrt = math.sqrt
        
        if self._geomType == "octagon":
            makeSegment = self.octSegment
        else:
            makeSegment = self.rectSegment
    
        makeRect = self.makeRect
        make45Bridge = self.make45Bridge
            
        w = self._w
        s = self._s
        r = roundToGrid(self._r/2)

        e=roundToGrid(w+s+2*w/(1+sqrt(2)))

        corner_w=roundToGrid((w+s)/2/(1+sqrt(2)))
        corner_w2=roundToGrid((w+s)/2.0/(1+sqrt(2.0)))

        centerX=self._centerX;
        centerY=self._centerY;

        signalMet = list()
        underMet = list()
        vias = list()
        
        viaEnc = self._viaEnc
        viaSize = self._viaSize
        viaSpace = self._viaSpace

        for i in range(7):
           signalMet.append(makeSegment(w,r-i*(w+s), e, 0, centerX, centerY))
           signalMet.append(makeSegment(w,r-i*(w+s), e, 1, centerX, centerY))
           signalMet.append(makeSegment(w,r-i*(w+s), e, 2, centerX, centerY))
           signalMet.append(makeSegment(w,r-i*(w+s), e, 3, centerX, centerY))
    
        # Connect continous segments
        signalMet.append(makeRect( (-r+(w+s)+centerX, e+centerY), (-r+(w+s)+w+centerX, -e+centerY)))
        signalMet.append(makeRect( (-r+6*(w+s)+centerX, e+centerY), (-r+6*(w+s)+w+centerX, -e+centerY)))

        signalMet.append(makeRect( (e+centerX, -r+6*(w+s)+centerY), (-e+centerX, -r+6*(w+s)+w+centerY)))
        signalMet.append(makeRect( (e+centerX, -(-r+6*(w+s))+centerY), (-e+centerX, -(-r+6*(w+s)+w)+centerY)))

        
        # left
        #                  w   e  offx offy      originX         originY    mir  r90   addVias
        p1,v1 = make45Bridge(w, 2*e, w+s, 0, -r+2*(w+s)+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # Underpass
        p2,v2 = make45Bridge(w, 2*e, w+s, 0, -r+4*(w+s)+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # Underpass

        p3,v3 = make45Bridge(w, 2*e, w+s, 0, -r+2*(w+s)+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # Signal
        p4,v4 = make45Bridge(w, 2*e, w+s, 0, -r+4*(w+s)+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # Signal


        # right
        p5,v5 = make45Bridge(w, 2*e, w+s, 0, r-6*(w+s)-w+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # Underpass
        p6,v6 = make45Bridge(w, 2*e, w+s, 0, r-6*(w+s)-w+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # Signal

        p7,v7 = make45Bridge(w, 2*e, 2*(w+s), -corner_w, r-4*(w+s)-w+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # Underpass
        p8,v8 = make45Bridge(w, 2*e, 2*(w+s), corner_w, r-3*(w+s)-w+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # Underpass

        p9,v9 = make45Bridge(w, 2*e, 2*(w+s), corner_w, r-4*(w+s)-w+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # Signal
        p10,v10 = make45Bridge(w, 2*e, 2*(w+s), -corner_w, r-3*(w+s)-w+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # Signal


        #; up
        p11,v11 = make45Bridge(w, 2*e, (w+s), -corner_w2, -e+centerX, r-3*(w+s)+s+centerY, True, True, True, viaEnc, viaSize, viaSpace) # Underpass
        p12,v12 = make45Bridge(w, 2*e, (w+s), corner_w2, -e+centerX, r-2*(w+s)+s+centerY, True, True, True, viaEnc, viaSize, viaSpace) # Underpass

        p13,v13 = make45Bridge(w, 2*e, (w+s), -corner_w2, -e+centerX, r-5*(w+s)+s+centerY, False, True, True, viaEnc, viaSize, viaSpace) # Underpass
        p14,v14 = make45Bridge(w, 2*e, (w+s), corner_w2, -e+centerX, r-6*(w+s)+s+centerY, False, True, True, viaEnc, viaSize, viaSpace) # Underpass

        p15,v15 = make45Bridge(w, 2*e, 2*(w+s), 0, -e+centerX, r-3*(w+s)+s+centerY, False, True, False, viaEnc, viaSize, viaSpace) # Signal
        p16,v16 = make45Bridge(w, 2*e, 2*(w+s), 0, -e+centerX, r-6*(w+s)+s+centerY, True, True, False, viaEnc, viaSize, viaSpace) # Signal


        # down
        p17,v17 = make45Bridge(w, 2*e, (w+s), corner_w2, -e+centerX, -(r-4*(w+s))+centerY, True, True, True, viaEnc, viaSize, viaSpace) # Underpass
        p18,v18 = make45Bridge(w, 2*e, (w+s), -corner_w2, -e+centerX, -(r-3*(w+s))+centerY, True, True, True, viaEnc, viaSize, viaSpace) # Underpass

        p19,v19 = make45Bridge(w, 2*e, (w+s), corner_w2, -e+centerX, -(r-0*(w+s))+centerY, False, True, True, viaEnc, viaSize, viaSpace) # Underpass
        p20,v20 = make45Bridge(w, 2*e, (w+s), -corner_w2, -e+centerX, -(r-1*(w+s))+centerY, False, True, True, viaEnc, viaSize, viaSpace) # Underpass

        p21,v21 = make45Bridge(w, 2*e, 2*(w+s), 0, -e+centerX, -(r-3*(w+s))+centerY, False, True, False, viaEnc, viaSize, viaSpace) # Signal
        p22,v22 = make45Bridge(w, 2*e, 2*(w+s), 0, -e+centerX, -(r-0*(w+s))+centerY, True, True, False, viaEnc, viaSize, viaSpace) # Signal

        appendPoly = self.appendPoly  
        appendVias = self.appendVias  
        
        appendPoly( signalMet, [p3, p4, p6, p9, p10, p15, p16, p21, p22])
        appendPoly( underMet, [p1, p2, p5, p7, p8, p11, p12, p13, p14, p17, p18, p19, p20])
        appendVias( vias, [v1, v2, v5, v7, v8, v11, v12, v13, v14, v17, v18, v19, v20])

        # Draw connections

        p1 = makeRect( (-r+centerX, e+centerY), (-r-2.0*w+centerX, w+e+centerY) )
        p2 = makeRect( (-r+centerX, -e+centerY), (-r-2.0*w+centerX, -w-e+centerY) )
        p3 = makeRect( (-r+w+s+centerX, -w/2.0+centerY), (-r-2.0*w+centerX, w/2.0+centerY) )

        p4 = makeRect( (r+centerX, e+centerY), (r+2.0*w+centerX, w+e+centerY) )
        p5 = makeRect( (r+centerX, -e+centerY), (r+2.0*w+centerX, -w-e+centerY) )

        #
        # Make port labels
        #
        portLabels = []
        # Primary +
        X = -r-2.0*w+centerX
        Y = 0.5*w+e+centerY
        portLabels.append( ((X, Y), 'PP') )
        # Primary -
        X = -r-2.0*w+centerX
        Y = -0.5*w-e+centerY
        portLabels.append( ((X, Y), 'PN') )
        # Primary center tap
        X = -r-2.0*w+centerX
        Y = 0.0
        portLabels.append( ((X, Y), 'PT') )
        # Secondary +
        X = r+centerX+2.0*w
        Y = 0.5*w+e+centerY
        portLabels.append( ((X, Y), 'SP') )
        # Secondary -
        X = r+centerX+2.0*w
        Y = -1.0*(0.5*w+e+centerY)
        portLabels.append( ((X, Y), 'SN') )
        #
        # end of port labels
        #
        
        appendPoly( signalMet, [p1, p2, p3, p4, p5])

        Geom = (signalMet, vias, underMet, portLabels)

        if self._genSubstrateContact:
            # Generate substrate contact
            subRingSpace = self._subRingSpace
            subRingW = self._subRingW
            r = self._r/2+subRingSpace
            s = subRingW
            centerX = self._centerX
            centerY = self._centerY
            geomType = self._geomType
            contEnc = self._contEnc
            contSize = self._contSize
            contSpace = self._contSpace
            diffEnc = self._diffEnc
            subCont = self.makeSubstrateContacts(subRingW, r, s, centerX, centerY, geomType, contEnc, contSize, contSpace, diffEnc)
        else:
            subCont = [[], [], [], [], []]
        return list(Geom) + list(subCont)

    def genGDSII(self, fileName, structName='bal_4x3', precision=1e-9):
        """
            Generate balun 4x3 GDSII
        """
        balGeom = self.genGeometry()
        sigPolygons = balGeom[0]
        vias = balGeom[1]
        underPolygons = balGeom[2]
        portLabels = balGeom[3]
       
        balCell = gdspy.Cell(structName)

        sigGDSII = self._tech.getGDSIINumByName(self._signalLayer)  # get signal layer GDSII number
        polySet = gdspy.PolygonSet(sigPolygons, sigGDSII)
        result = gdspy.boolean(polySet, None, "or", layer=sigGDSII)
        balCell.add(result)

        upGDSII = self._tech.getGDSIINumByName(self._underPassLayer)  # get signal layer GDSII number
        polySet = gdspy.PolygonSet(underPolygons, upGDSII)
        balCell.add(polySet)

        viaGDSII = self._tech.getGDSIINumByName(self._viaLayer)  # get signal layer GDSII number
        # add vias
        for viaRect in vias:
            balCell.add(gdspy.Rectangle(viaRect[0], viaRect[1], viaGDSII))

        for portLabel in portLabels:
            xy, name = portLabel
            balCell.add(gdspy.Label(name, xy, layer=sigGDSII))

        #
        # Substrate contacts
        #

        # Substrate contacts
        m1Polygons = balGeom[4]
        diffPolygons = balGeom[5]
        impPolygons = balGeom[6]
        subContacts = balGeom[7]
        subPinLabels = balGeom[8]

        if self._genSubstrateContact:
            m1GDSII = self._tech.getGDSIINumByName(self._m1Layer)
            for m1Polygon in m1Polygons:
                poly = gdspy.Polygon(m1Polygon, m1GDSII)
                balCell.add(poly)

            diffGDSII = self._tech.getGDSIINumByName(self._diffLayer)
            contGDSII = self._tech.getGDSIINumByName(self._contLayer)
            for diffPolygon in diffPolygons:
                poly = gdspy.Polygon(diffPolygon, diffGDSII)
                balCell.add(poly)
                if self.emVias:
                    contPolygon = self.oversize(diffPolygon, -self._contEnc)
                    poly = gdspy.Polygon(contPolygon, contGDSII)
                    balCell.add(poly)

            if not self.emVias:
                # add vias
                for viaRect in subContacts:
                    balCell.add(gdspy.Rectangle(viaRect[0], viaRect[1], contGDSII))
            
            impLayer = self._impLayer
            if impLayer != None:
                impGDSII = self._tech.getGDSIINumByName(impLayer)
                for impPolygon in impPolygons:
                    poly = gdspy.Polygon(impPolygon, impGDSII)
                    balCell.add(poly)

            for portLabel in subPinLabels:
                xy, name = portLabel
                balCell.add(gdspy.Label(name, xy, layer=sigGDSII))

        #
        # end of substrate contacts
        #

        lib = gdspy.GdsLibrary(structName, unit = 1.0e-6, precision=precision)
        lib.add(balCell)
        lib.write_gds(fileName)

###############################################################################
#
# Balun 2 + 2 windings
#
###############################################################################

class balun2x2(geomBase):
    """
        Balun 2 + 2 windings
    """

    _r = None
    _w = None
    _s = None

    _signalLayer = None     # Name of signal layer
    _underPassLayer = None  # Name of under pass layer

    _viaLayer = None    # Name of via layer
    _viaEnc = 0
    _viaSize = 0
    _viaSpace = 0

    _geomType = None
    
    _centerX = 0.0
    _centerY = 0.0
    
    def __init__(self,tech=None):
        self._tech = tech   # Set the technology

    def setupGeometry(self, r, w, s, signalLayer, underPassLayer, geomType="octagon", centerX = None, centerY = None, subRingSpace=0.0, subRingW=0.0, diffLayer=None, implantLayer=None, contSpaceMult=4.0):
        """
            Setup balun 2x2 geometry
            r : float
                outer inductor dimension
            w : float
                winding line width
            s : foat
                winding spacing
            signalLayer : string
                signal layer name
            underPassLayer : string
                underpass layer name
            geomType : string
                Type of geometry. Allowed values : "rect", "octagon"
            centerX : float
                Center of inductor x coordinate
            centerY : float
                Center of inductor y coordinate
                
        """
        self._r = r
        self._w = w
        self._s = s
        self._signalLayer = signalLayer
        self._underPassLayer = underPassLayer
        if (geomType != "rect") and (geomType != "octagon"):
            print("WARNING:balun2x2::setupGeometry: Unknown geometry type. Setting to octagonal.")
            self._geomType = "octagon"
        else:
            self._geomType = geomType
                
        if centerX == None:
            self._centerX = 0
        else:
            self._centerX = centerX
            
        if centerY == None:
            self._centerY = 0
        else:
            self._centerY = centerY
            
        # Find via, find via rules
        viaLay = self._tech.findViaTopMet(signalLayer)
        if viaLay == None:
            print("ERROR:balun2x2::setupGeometry: Signal layer " + signalLayer + " does not have any vias connecting to it from underside.")
            return
        
        viaName = viaLay.name
        self._viaLayer = viaName
        self._viaEnc = self._tech.getDRCRule(viaName, "viaEnc")
        self._viaSize = self._tech.getDRCRule(viaName, "viaSize")
        self._viaSpace = self._tech.getDRCRule(viaName, "viaSpace")

        #        
        # Substrate ring parameters
        #
        if diffLayer!=None:
            self._genSubstrateContact = True
            contLay = self._tech.findViaBotMet(diffLayer).name
            if contLay == None:
                print("ERROR:inductorSE::setupGeometry: Diffusion layer " + diffLayer + " does not have any vias connecting to it from top.")
                return

            self._diffLayer = diffLayer
            self._impLayer = implantLayer
            
            if implantLayer!=None:
                self._diffEnc = self._tech.getDRCRule(implantLayer, "enclosure")
            else:
                self._diffEnc = 0            

            self._contLayer = contLay
            self._contEnc = self._tech.getDRCRule(contLay, "viaEnc")
            self._contSize = self._tech.getDRCRule(contLay, "viaSize")
            self._contSpace = self._tech.getDRCRule(contLay, "viaSpace") * contSpaceMult

            self._m1Layer = self._tech.findTopMetVia(contLay).name
            self._subRingSpace = subRingSpace
            self._subRingW = subRingW
            
        else:
            self._genSubstrateContact = False
                    
        # Dimension check: return False if diameter is too small
        return r>=self.get_min_diameter()


    def get_min_diameter(self):

        return balun_MxN_get_min_diameter(self,3,3)


    def genGeometry(self):
        """
        Generate geometry for 4x3 balun
        returns polygon collections
        """    

        roundToGrid = self.roundToGrid
        sqrt = math.sqrt
        
        if self._geomType == "octagon":
            makeSegment = self.octSegment
        else:
            makeSegment = self.rectSegment
    
        makeRect = self.makeRect
        make45Bridge = self.make45Bridge
            
        w = self._w
        s = self._s
        r = roundToGrid(self._r/2)

        e=roundToGrid(w+s+2*w/(1+sqrt(2)))

        corner_w=roundToGrid((w+s)/2/(1+sqrt(2)))
        corner_w2=roundToGrid((w+s)/2.0/(1+sqrt(2.0)))

        centerX=self._centerX;
        centerY=self._centerY;

        signalMet = list()
        underMet = list()
        vias = list()
        
        viaEnc = self._viaEnc
        viaSize = self._viaSize
        viaSpace = self._viaSpace

        for i in range(6):
           signalMet.append(makeSegment(w,r-i*(w+s), e, 0, centerX, centerY))
           signalMet.append(makeSegment(w,r-i*(w+s), e, 1, centerX, centerY))
           signalMet.append(makeSegment(w,r-i*(w+s), e, 2, centerX, centerY))
           signalMet.append(makeSegment(w,r-i*(w+s), e, 3, centerX, centerY))
    
        # Connect continous segments
        signalMet.append(makeRect( (-r+(w+s)+centerX, e+centerY), (-r+(w+s)+w+centerX, -e+centerY)))

        signalMet.append(makeRect( (r-5*(w+s)-w+centerX, e+centerY), (r-5*(w+s)-w+w+centerX, -e+centerY)))

        # left
        #                  w   e  offx offy      originX         originY    mir  r90   addVias
        p1,v1 = make45Bridge(w, 2*e, w+s, 0, -r+2*(w+s)+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # Underpass
        p2,v2 = make45Bridge(w, 2*e, w+s, 0, -r+4*(w+s)+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # Underpass

        p3,v3 = make45Bridge(w, 2*e, w+s, 0, -r+2*(w+s)+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # Signal
        p4,v4 = make45Bridge(w, 2*e, w+s, 0, -r+4*(w+s)+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # Signal

        # right
        p7,v7 = make45Bridge(w, 2*e, 2*(w+s), -corner_w, r-4*(w+s)-w+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # Underpass
        p8,v8 = make45Bridge(w, 2*e, 2*(w+s), corner_w, r-3*(w+s)-w+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # Underpass

        p9,v9 = make45Bridge(w, 2*e, 2*(w+s), corner_w, r-4*(w+s)-w+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # Signal
        p10,v10 = make45Bridge(w, 2*e, 2*(w+s), -corner_w, r-3*(w+s)-w+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # Signal

        # up
        p11,v11 = make45Bridge(w, 2*e, (w+s), -corner_w2, -e+centerX, r-3*(w+s)+s+centerY, True, True, True, viaEnc, viaSize, viaSpace) # Underpass
        p12,v12 = make45Bridge(w, 2*e, (w+s), corner_w2, -e+centerX, r-2*(w+s)+s+centerY, True, True, True, viaEnc, viaSize, viaSpace) # Underpass

        p13,v13 = make45Bridge(w, 2*e, (w+s), -corner_w2, -e+centerX, r-5*(w+s)+s+centerY, False, True, True, viaEnc, viaSize, viaSpace) # Underpass
        p14,v14 = make45Bridge(w, 2*e, (w+s), corner_w2, -e+centerX, r-6*(w+s)+s+centerY, False, True, True, viaEnc, viaSize, viaSpace) # Underpass

        p15,v15 = make45Bridge(w, 2*e, 2*(w+s), 0, -e+centerX, r-3*(w+s)+s+centerY, False, True, False, viaEnc, viaSize, viaSpace) # Signal
        p16,v16 = make45Bridge(w, 2*e, 2*(w+s), 0, -e+centerX, r-6*(w+s)+s+centerY, True, True, False, viaEnc, viaSize, viaSpace) # Signal

        # down
        p17,v17 = make45Bridge(w, 2*e, (w+s), corner_w2, -e+centerX, -(r-4*(w+s))+centerY, True, True, True, viaEnc, viaSize, viaSpace) # Underpass
        p18,v18 = make45Bridge(w, 2*e, (w+s), -corner_w2, -e+centerX, -(r-3*(w+s))+centerY, True, True, True, viaEnc, viaSize, viaSpace) # Underpass

        p19,v19 = make45Bridge(w, 2*e, (w+s), corner_w2, -e+centerX, -(r-0*(w+s))+centerY, False, True, True, viaEnc, viaSize, viaSpace) # Underpass
        p20,v20 = make45Bridge(w, 2*e, (w+s), -corner_w2, -e+centerX, -(r-1*(w+s))+centerY, False, True, True, viaEnc, viaSize, viaSpace) # Underpass

        p21,v21 = make45Bridge(w, 2*e, 2*(w+s), 0, -e+centerX, -(r-3*(w+s))+centerY, False, True, False, viaEnc, viaSize, viaSpace) # Signal
        p22,v22 = make45Bridge(w, 2*e, 2*(w+s), 0, -e+centerX, -(r-0*(w+s))+centerY, True, True, False, viaEnc, viaSize, viaSpace) # Signal

        appendPoly = self.appendPoly  
        appendVias = self.appendVias  
        
        appendPoly( signalMet, [p3, p4, p9, p10, p15, p16, p21, p22])
        appendPoly( underMet, [p1, p2, p7, p8, p11, p12, p13, p14, p17, p18, p19, p20])
        appendVias( vias, [v1, v2, v7, v8, v11, v12, v13, v14, v17, v18, v19, v20])

        # Draw connections

        p1 = makeRect( (-r+centerX, e+centerY), (-r-2.0*w+centerX, w+e+centerY) )
        p2 = makeRect( (-r+centerX, -e+centerY), (-r-2.0*w+centerX, -w-e+centerY) )
        p3 = makeRect( (-r+w+s+centerX, -w/2.0+centerY), (-r-2.0*w+centerX, w/2.0+centerY) )

        p4 = makeRect( (r+centerX, e+centerY), (r+2.0*w+centerX, w+e+centerY) )
        p5 = makeRect( (r+centerX, -e+centerY), (r+2.0*w+centerX, -w-e+centerY) )

        #
        # Make port labels
        #
        portLabels = []
        # Primary +
        X = -r-2.0*w+centerX
        Y = 0.5*w+e+centerY
        portLabels.append( ((X, Y), 'PP') )
        # Primary -
        X = -r-2.0*w+centerX
        Y = -0.5*w-e+centerY
        portLabels.append( ((X, Y), 'PN') )
        # Primary center tap
        X = -r-2.0*w+centerX
        Y = 0.0
        portLabels.append( ((X, Y), 'PT') )
        # Secondary +
        X = r+centerX+2.0*w
        Y = 0.5*w+e+centerY
        portLabels.append( ((X, Y), 'SP') )
        # Secondary -
        X = r+centerX+2.0*w
        Y = -1.0*(0.5*w+e+centerY)
        portLabels.append( ((X, Y), 'SN') )
        #
        # end of port labels
        #

        appendPoly( signalMet, [p1, p2, p3, p4, p5])
        Geom = (signalMet, vias, underMet, portLabels)        

        if self._genSubstrateContact:
            # Generate substrate contact
            subRingSpace = self._subRingSpace
            subRingW = self._subRingW
            r = self._r/2+subRingSpace
            s = subRingW
            centerX = self._centerX
            centerY = self._centerY
            geomType = self._geomType
            contEnc = self._contEnc
            contSize = self._contSize
            contSpace = self._contSpace
            diffEnc = self._diffEnc
            subCont = self.makeSubstrateContacts(subRingW, r, s, centerX, centerY, geomType, contEnc, contSize, contSpace, diffEnc)
        else:
            subCont = [[], [], [], [], []]
        return list(Geom) + list(subCont)

    def genGDSII(self, fileName, structName='bal_2x2', precision=1e-9):
        """
            Generate balun 2x2 GDSII
        """
        balGeom = self.genGeometry()
        sigPolygons = balGeom[0]
        vias = balGeom[1]
        underPolygons = balGeom[2]
        portLabels = balGeom[3]
       
        balCell = gdspy.Cell(structName)

        sigGDSII = self._tech.getGDSIINumByName(self._signalLayer)  # get signal layer GDSII number
        polySet = gdspy.PolygonSet(sigPolygons, sigGDSII)
        result = gdspy.boolean(polySet, None, "or", layer=sigGDSII)
        balCell.add(result)

        upGDSII = self._tech.getGDSIINumByName(self._underPassLayer)  # get signal layer GDSII number
        polySet = gdspy.PolygonSet(underPolygons, upGDSII)
        balCell.add(polySet)

        viaGDSII = self._tech.getGDSIINumByName(self._viaLayer)  # get signal layer GDSII number
        # add vias
        for viaRect in vias:
            balCell.add(gdspy.Rectangle(viaRect[0], viaRect[1], viaGDSII))

        for portLabel in portLabels:
            xy, name = portLabel
            balCell.add(gdspy.Label(name, xy, layer=sigGDSII))

        #
        # Substrate contacts
        #

        # Substrate contacts
        m1Polygons = balGeom[4]
        diffPolygons = balGeom[5]
        impPolygons = balGeom[6]
        subContacts = balGeom[7]
        subPinLabels = balGeom[8]

        if self._genSubstrateContact:
            m1GDSII = self._tech.getGDSIINumByName(self._m1Layer)
            for m1Polygon in m1Polygons:
                poly = gdspy.Polygon(m1Polygon, m1GDSII)
                balCell.add(poly)

            diffGDSII = self._tech.getGDSIINumByName(self._diffLayer)
            contGDSII = self._tech.getGDSIINumByName(self._contLayer)
            for diffPolygon in diffPolygons:
                poly = gdspy.Polygon(diffPolygon, diffGDSII)
                balCell.add(poly)
                if self.emVias:
                    contPolygon = self.oversize(diffPolygon, -self._contEnc)
                    poly = gdspy.Polygon(contPolygon, contGDSII)
                    balCell.add(poly)

            if not self.emVias:
                # add vias
                for viaRect in subContacts:
                    balCell.add(gdspy.Rectangle(viaRect[0], viaRect[1], contGDSII))

            impLayer = self._impLayer
            if impLayer != None:
                impGDSII = self._tech.getGDSIINumByName(impLayer)
                for impPolygon in impPolygons:
                    poly = gdspy.Polygon(impPolygon, impGDSII)
                    balCell.add(poly)

            for portLabel in subPinLabels:
                xy, name = portLabel
                balCell.add(gdspy.Label(name, xy, layer=sigGDSII))

        #
        # end of substrate contacts
        #

        lib = gdspy.GdsLibrary(structName, unit = 1.0e-6, precision=precision)
        lib.add(balCell)
        lib.write_gds(fileName)

###############################################################################
#
# Balun 6 + 3 windings
#
###############################################################################

class balun6x3(geomBase):
    """
        Balun 6 + 3 windings
    """

    _r = None
    _w = None
    _s = None

    _signalLayer = None     # Name of signal layer
    _underPassLayer = None  # Name of under pass layer

    _viaLayer = None    # Name of via layer
    _viaEnc = 0
    _viaSize = 0
    _viaSpace = 0

    _geomType = None
    
    _centerX = 0.0
    _centerY = 0.0
    
    def __init__(self,tech=None):
        self._tech = tech   # Set the technology

    def setupGeometry(self, r, w, s, signalLayer, underPassLayer, geomType="octagon", centerX = None, centerY = None, subRingSpace=0.0, subRingW=0.0, diffLayer=None, implantLayer=None, contSpaceMult=4.0):
        """
            Setup balun 6x3 geometry
            r : float
                outer inductor dimension
            w : float
                winding line width
            s : foat
                winding spacing
            signalLayer : string
                signal layer name
            underPassLayer : string
                underpass layer name
            geomType : string
                Type of geometry. Allowed values : "rect", "octagon"
            centerX : float
                Center of inductor x coordinate
            centerY : float
                Center of inductor y coordinate
                
        """
        self._r = r
        self._w = w
        self._s = s
        self._signalLayer = signalLayer
        self._underPassLayer = underPassLayer
        if (geomType != "rect") and (geomType != "octagon"):
            print("WARNING:balun6x3::setupGeometry: Unknown geometry type. Setting to octagonal.")
            self._geomType = "octagon"
        else:
            self._geomType = geomType
                
        if centerX == None:
            self._centerX = 0
        else:
            self._centerX = centerX
            
        if centerY == None:
            self._centerY = 0
        else:
            self._centerY = centerY
            
        # Find via, find via rules
        viaLay = self._tech.findViaTopMet(signalLayer)
        if viaLay == None:
            print("ERROR:balun6x3::setupGeometry: Signal layer " + signalLayer + " does not have any vias connecting to it from underside.")
            return
        
        viaName = viaLay.name
        self._viaLayer = viaName
        self._viaEnc = self._tech.getDRCRule(viaName, "viaEnc")
        self._viaSize = self._tech.getDRCRule(viaName, "viaSize")
        self._viaSpace = self._tech.getDRCRule(viaName, "viaSpace")

        #        
        # Substrate ring parameters
        #
        if diffLayer!=None:
            self._genSubstrateContact = True
            contLay = self._tech.findViaBotMet(diffLayer).name
            if contLay == None:
                print("ERROR:inductorSE::setupGeometry: Diffusion layer " + diffLayer + " does not have any vias connecting to it from top.")
                return

            self._diffLayer = diffLayer
            self._impLayer = implantLayer
            
            if implantLayer!=None:
                self._diffEnc = self._tech.getDRCRule(implantLayer, "enclosure")
            else:
                self._diffEnc = 0            

            self._contLayer = contLay
            self._contEnc = self._tech.getDRCRule(contLay, "viaEnc")
            self._contSize = self._tech.getDRCRule(contLay, "viaSize")
            self._contSpace = self._tech.getDRCRule(contLay, "viaSpace") * contSpaceMult

            self._m1Layer = self._tech.findTopMetVia(contLay).name
            self._subRingSpace = subRingSpace
            self._subRingW = subRingW
            
        else:
            self._genSubstrateContact = False

        # Dimension check: return False if diameter is too small
        return r>=self.get_min_diameter()

    def get_min_diameter(self):

        return balun_MxN_get_min_diameter(self,6,3)
    
    def genGeometry(self):
        """
        Generate geometry for 4x3 balun
        returns polygon collections
        
        """    

        roundToGrid = self.roundToGrid
        sqrt = math.sqrt
        
        if self._geomType == "octagon":
            makeSegment = self.octSegment
        else:
            makeSegment = self.rectSegment
    
        makeRect = self.makeRect
        make45Bridge = self.make45Bridge
            
        w = self._w
        s = self._s
        r = roundToGrid(self._r/2)

        e=roundToGrid(w+s+2*w/(1+sqrt(2)))

        corner_w=roundToGrid((w+s)/2/(1+sqrt(2)))
        corner_w2=roundToGrid((w+s)/2.0/(1+sqrt(2.0)))

        centerX=self._centerX;
        centerY=self._centerY;

        signalMet = list()
        underMet = list()
        vias = list()
        
        viaEnc = self._viaEnc
        viaSize = self._viaSize
        viaSpace = self._viaSpace

        for i in range(9):
           signalMet.append(makeSegment(w,r-i*(w+s), e, 0, centerX, centerY))
           signalMet.append(makeSegment(w,r-i*(w+s), e, 1, centerX, centerY))
           signalMet.append(makeSegment(w,r-i*(w+s), e, 2, centerX, centerY))
           signalMet.append(makeSegment(w,r-i*(w+s), e, 3, centerX, centerY))
    
        # Connect continous segments
        signalMet.append(makeRect( (-r+(w+s)+centerX, e+centerY), (-r+(w+s)+w+centerX, -e+centerY)))
        signalMet.append(makeRect( (-r+8*(w+s)+centerX, e+centerY), (-r+8*(w+s)+w+centerX, -e+centerY)))

        # left
        #                  w   e  offx offy      originX         originY    mir  r90   addVias
        p1, v1 = make45Bridge(w, 2*e, w+s, 0, -r+2*(w+s)+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # underpass
        p2, v2 = make45Bridge(w, 2*e, w+s, 0, -r+2*(w+s)+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # signal

        p3, v3 = make45Bridge(w, 2*e, 2*(w+s), -corner_w, -r+4*(w+s)+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # underpass
        p4, v4 = make45Bridge(w, 2*e, 2*(w+s), corner_w, -r+5*(w+s)+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # underpass

        p5, v5 = make45Bridge(w, 2*e, 2*(w+s), corner_w, -r+4*(w+s)+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # signal
        p6, v6 = make45Bridge(w, 2*e, 2*(w+s), -corner_w, -r+5*(w+s)+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # signal

        # right
        p7, v7 = make45Bridge(w, 2*e, w+s, 0, r-6*(w+s)-w+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # underpass
        p8, v8 = make45Bridge(w, 2*e, w+s, 0, r-6*(w+s)-w+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # signal

        p9, v9 = make45Bridge(w, 2*e, w+s, 0, r-8*(w+s)-w+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # underpass
        p10, v10 = make45Bridge(w, 2*e, w+s, 0, r-8*(w+s)-w+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # signal

        p11, v11 = make45Bridge(w, 2*e, 2*(w+s), -corner_w, r-4*(w+s)-w+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # underpass
        p12, v12 = make45Bridge(w, 2*e, 2*(w+s), corner_w, r-3*(w+s)-w+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # underpass

        p13, v13 = make45Bridge(w, 2*e, 2*(w+s), corner_w, r-4*(w+s)-w+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # signal
        p14, v14 = make45Bridge(w, 2*e, 2*(w+s), -corner_w, r-3*(w+s)-w+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # signal

        # up
        p15, v15 = make45Bridge(w, 2*e, (w+s), -corner_w2, -e+centerX, r-3*(w+s)+s+centerY, True, True, True, viaEnc, viaSize, viaSpace) # underpass
        p16, v16 = make45Bridge(w, 2*e, (w+s), corner_w2, -e+centerX, r-2*(w+s)+s+centerY, True, True, True, viaEnc, viaSize, viaSpace) # underpass

        p17, v17 = make45Bridge(w, 2*e, (w+s), -corner_w2, -e+centerX, r-5*(w+s)+s+centerY, False, True, True, viaEnc, viaSize, viaSpace) # underpass
        p18, v18 = make45Bridge(w, 2*e, (w+s), corner_w2, -e+centerX, r-6*(w+s)+s+centerY, False, True, True, viaEnc, viaSize, viaSpace) # underpass

        p19, v19 = make45Bridge(w, 2*e, 2*(w+s), 0, -e+centerX, r-3*(w+s)+s+centerY, False, True, False, viaEnc, viaSize, viaSpace) # signal
        p20, v20 = make45Bridge(w, 2*e, 2*(w+s), 0, -e+centerX, r-6*(w+s)+s+centerY, True, True, False, viaEnc, viaSize, viaSpace) # signal

        p21, v21 = make45Bridge(w, 2*e, (w+s), -corner_w2, -e+centerX, r-9*(w+s)+s+centerY, True, True, True, viaEnc, viaSize, viaSpace) # underpass
        p22, v22 = make45Bridge(w, 2*e, (w+s), corner_w2, -e+centerX, r-8*(w+s)+s+centerY, True, True, True, viaEnc, viaSize, viaSpace) # underpass
        p23, v23 = make45Bridge(w, 2*e, 2*(w+s), 0, -e+centerX, r-9*(w+s)+s+centerY, False, True, False, viaEnc, viaSize, viaSpace) # signal

        # down
        p24, v24 = make45Bridge(w, 2*e, (w+s), corner_w2, -e+centerX, -(r-4*(w+s))+centerY, True, True, True, viaEnc, viaSize, viaSpace) # underpass
        p25, v25 = make45Bridge(w, 2*e, (w+s), -corner_w2, -e+centerX, -(r-3*(w+s))+centerY, True, True, True, viaEnc, viaSize, viaSpace) # underpass

        p26, v26 = make45Bridge(w, 2*e, (w+s), corner_w2, -e+centerX, -(r-0*(w+s))+centerY, False, True, True, viaEnc, viaSize, viaSpace) # underpass
        p27, v27 = make45Bridge(w, 2*e, (w+s), -corner_w2, -e+centerX, -(r-1*(w+s))+centerY, False, True, True, viaEnc, viaSize, viaSpace) # underpass

        p28, v28 = make45Bridge(w, 2*e, 2*(w+s), 0, -e+centerX, -(r-3*(w+s))+centerY, False, True, False, viaEnc, viaSize, viaSpace) # signal
        p29, v29 = make45Bridge(w, 2*e, 2*(w+s), 0, -e+centerX, -(r-0*(w+s))+centerY, True, True, False, viaEnc, viaSize, viaSpace) # signal


        p30, v30 = make45Bridge(w, 2*e, 2*(w+s), 0, -e+centerX, -(r-6*(w+s))+centerY, True, True, False, viaEnc, viaSize, viaSpace) # signal
        p31, v31 = make45Bridge(w, 2*e, (w+s), corner_w2, -e+centerX, -(r-6*(w+s))+centerY, False, True, True, viaEnc, viaSize, viaSpace) # underpass
        p32, v32 = make45Bridge(w, 2*e, (w+s), -corner_w2, -e+centerX, -(r-7*(w+s))+centerY, False, True, True, viaEnc, viaSize, viaSpace) # underpass

    
        appendPoly = self.appendPoly  
        appendVias = self.appendVias  
        
        appendPoly( signalMet, [p2, p5, p6, p8, p10, p13, p14, p19, p20, p23,p28, p29, p30])
        appendPoly( underMet, [p1, p3, p4, p7, p9, p11, p12, p15, p16, p17, p18, p21, p22, p24, p25, p26, p27,p31, p32])
        appendVias( vias, [v1,v3,v4,v7,v9,v11,v12,v15,v16,v17,v18,v21,v22,v24,v25,v26,v27,v31,v32])

        # Draw connections

        p1 = makeRect( (-r+centerX, e+centerY), (-r-2.0*w+centerX, w+e+centerY) )
        p2 = makeRect( (-r+centerX, -e+centerY), (-r-2.0*w+centerX, -w-e+centerY) )
        p3 = makeRect( (-r+w+s+centerX, -w/2.0+centerY), (-r-2.0*w+centerX, w/2.0+centerY) )

        p4 = makeRect( (r+centerX, e+centerY), (r+2.0*w+centerX, w+e+centerY) )
        p5 = makeRect( (r+centerX, -e+centerY), (r+2.0*w+centerX, -w-e+centerY) )

        #
        # Make port labels
        #
        portLabels = []
        # Primary +
        X = -r-2.0*w+centerX
        Y = 0.5*w+e+centerY
        portLabels.append( ((X, Y), 'PP') )
        # Primary -
        X = -r-2.0*w+centerX
        Y = -0.5*w-e+centerY
        portLabels.append( ((X, Y), 'PN') )
        # Primary center tap
        X = -r-2.0*w+centerX
        Y = 0.0
        portLabels.append( ((X, Y), 'PT') )
        # Secondary +
        X = r+centerX+2.0*w
        Y = 0.5*w+e+centerY
        portLabels.append( ((X, Y), 'SP') )
        # Secondary -
        X = r+centerX+2.0*w
        Y = -1.0*(0.5*w+e+centerY)
        portLabels.append( ((X, Y), 'SN') )
        #
        # end of port labels
        #

        appendPoly( signalMet, [p1, p2, p3, p4, p5])        
        Geom = (signalMet, vias, underMet, portLabels)
        
        if self._genSubstrateContact:
            # Generate substrate contact
            subRingSpace = self._subRingSpace
            subRingW = self._subRingW
            r = self._r/2+subRingSpace
            s = subRingW
            centerX = self._centerX
            centerY = self._centerY
            geomType = self._geomType
            contEnc = self._contEnc
            contSize = self._contSize
            contSpace = self._contSpace
            diffEnc = self._diffEnc
            subCont = self.makeSubstrateContacts(subRingW, r, s, centerX, centerY, geomType, contEnc, contSize, contSpace, diffEnc)
        else:
            subCont = [[], [], [], [], []]
        return list(Geom) + list(subCont)        

    def genGDSII(self, fileName, structName='bal_6x3', precision=1e-9):
        """
            Generate balun 6x3 GDSII
        """
        balGeom = self.genGeometry()
        sigPolygons = balGeom[0]
        vias = balGeom[1]
        underPolygons = balGeom[2]
        portLabels = balGeom[3]
      
        balCell = gdspy.Cell(structName)

        sigGDSII = self._tech.getGDSIINumByName(self._signalLayer)  # get signal layer GDSII number
        polySet = gdspy.PolygonSet(sigPolygons, sigGDSII)
        result = gdspy.boolean(polySet, None, "or", layer=sigGDSII)
        balCell.add(result)

        upGDSII = self._tech.getGDSIINumByName(self._underPassLayer)  # get signal layer GDSII number
        polySet = gdspy.PolygonSet(underPolygons, upGDSII)
        balCell.add(polySet)

        viaGDSII = self._tech.getGDSIINumByName(self._viaLayer)  # get signal layer GDSII number
        # add vias
        for viaRect in vias:
            balCell.add(gdspy.Rectangle(viaRect[0], viaRect[1], viaGDSII))

        for portLabel in portLabels:
            xy, name = portLabel
            balCell.add(gdspy.Label(name, xy, layer=sigGDSII))

        #
        # Substrate contacts
        #

        # Substrate contacts
        m1Polygons = balGeom[4]
        diffPolygons = balGeom[5]
        impPolygons = balGeom[6]
        subContacts = balGeom[7]
        subPinLabels = balGeom[8]

        if self._genSubstrateContact:
            m1GDSII = self._tech.getGDSIINumByName(self._m1Layer)
            for m1Polygon in m1Polygons:
                poly = gdspy.Polygon(m1Polygon, m1GDSII)
                balCell.add(poly)

            diffGDSII = self._tech.getGDSIINumByName(self._diffLayer)
            contGDSII = self._tech.getGDSIINumByName(self._contLayer)
            for diffPolygon in diffPolygons:
                poly = gdspy.Polygon(diffPolygon, diffGDSII)
                balCell.add(poly)
                if self.emVias:
                    contPolygon = self.oversize(diffPolygon, -self._contEnc)
                    poly = gdspy.Polygon(contPolygon, contGDSII)
                    balCell.add(poly)

            if not self.emVias:
                # add vias
                for viaRect in subContacts:
                    balCell.add(gdspy.Rectangle(viaRect[0], viaRect[1], contGDSII))
            
            impLayer = self._impLayer
            if impLayer != None:
                impGDSII = self._tech.getGDSIINumByName(impLayer)
                for impPolygon in impPolygons:
                    poly = gdspy.Polygon(impPolygon, impGDSII)
                    balCell.add(poly)

            for portLabel in subPinLabels:
                xy, name = portLabel
                balCell.add(gdspy.Label(name, xy, layer=sigGDSII))

        #
        # end of substrate contacts
        #

        lib = gdspy.GdsLibrary(structName, unit = 1.0e-6, precision=precision)
        lib.add(balCell)
        lib.write_gds(fileName)
        

###############################################################################
#
# Balun 2 + 1 windings edge coupled
#
###############################################################################

class balun2x1_edgecoupled(geomBase):
    """
        Balun 2 + 1 windings
    """

    _r = None
    _w = None
    _s = None

    _signalLayer = None     # Name of signal layer
    _bridgeLayer = None  # Name of bridge layer

    _viaLayer = None    # Name of via layer
    _viaEnc = 0
    _viaSize = 0
    _viaSpace = 0
    
    _pct = None     # primary center tap
    _sct = None     # secondary center tap

    _geomType = None
    
    _centerX = 0.0
    _centerY = 0.0
    
    def __init__(self,tech=None):
        self._tech = tech   # Set the technology

    def setupGeometry(self, r, w, s, signalLayer, bridgeLayer, geomType="octagon", pct = None, sct = None, centerX = None, centerY = None, subRingSpace=0.0, subRingW=0.0, diffLayer=None, implantLayer=None, contSpaceMult=4.0):
        """
            Setup balun 2x1 geometry
            r : float
                outer inductor dimension
            w : float
                winding line width
            s : foat
                winding spacing
            signalLayer : string
                signal layer name
            brodgeLayer : string
                bridge layer name
            geomType : string
                Type of geometry. Allowed values : "rect", "octagon"
            pct : float
                if set, generates primary center tap
            sct : float
                if set, generates secondary center tap
            centerX : float
                Center of inductor x coordinate
            centerY : float
                Center of inductor y coordinate
        """
        self._r = r
        self._w = w
        self._s = s
        self._signalLayer = signalLayer
        self._bridgeLayer = bridgeLayer
        if (geomType != "rect") and (geomType != "octagon"):
            print("WARNING:balun2x1::setupGeometry: Unknown geometry type. Setting to octagonal.")
            self._geomType = "octagon"
        else:
            self._geomType = geomType
            
        if pct == None:
            self._pct = 0
        else:
            self._pct = pct
            
        if sct == None:
            self._pct = 0
        else:
            self._sct = sct

        if centerX == None:
            self._centerX = 0
        else:
            self._centerX = centerX
            
        if centerY == None:
            self._centerY = 0
        else:
            self._centerY = centerY

        # Find via, find via rules
        if self._tech.findViaTopMet(signalLayer) == self._tech.findViaBotMet(bridgeLayer): # try overpass
            viaLay = self._tech.findViaTopMet(signalLayer)
        elif self._tech.findViaBotMet(signalLayer) == self._tech.findViaTopMet(bridgeLayer): # try underpass
            viaLay = self._tech.findViaBotMet(signalLayer)              
        else:
            print("ERROR:balun2x1::setupGeometry: Signal layer and bridge layer must be adjacent. ")
            exit(1)
        
        viaName = viaLay.name
        self._viaLayer = viaName
        self._viaEnc = self._tech.getDRCRule(viaName, "viaEnc")
        self._viaSize = self._tech.getDRCRule(viaName, "viaSize")
        self._viaSpace = self._tech.getDRCRule(viaName, "viaSpace")

        #        
        # Substrate ring parameters
        #
        if diffLayer!=None:
            self._genSubstrateContact = True
            contLay = self._tech.findViaBotMet(diffLayer).name
            if contLay == None:
                print("ERROR:balun2x1::setupGeometry: Diffusion layer " + diffLayer + " does not have any vias connecting to it from top.")
                return

            self._diffLayer = diffLayer
            self._impLayer = implantLayer
            
            if implantLayer!=None:
                self._diffEnc = self._tech.getDRCRule(implantLayer, "enclosure")
            else:
                self._diffEnc = 0            

            self._contLayer = contLay

            self._contEnc = self._tech.getDRCRule(contLay, "viaEnc")
            self._contSize = self._tech.getDRCRule(contLay, "viaSize")
            self._contSpace = self._tech.getDRCRule(contLay, "viaSpace") * contSpaceMult

            self._m1Layer = self._tech.findTopMetVia(contLay).name
            self._subRingSpace = subRingSpace
            self._subRingW = subRingW
            
        else:
            self._genSubstrateContact = False
                    
        # Dimension check: return False if diameter is too small
        return r>=self.get_min_diameter()

    
    def get_min_diameter(self):
        w = self._w
        s = self._s

        e=w+2*w/(1+math.sqrt(2))
        crossover_size = 2*(w+e)
        if self._geomType == "octagon":
            Di_min = crossover_size * (1 + math.sqrt(2))
        else:
            Di_min = crossover_size    

        Do_min = (Di_min + 2*3*w + 2*2*s)
        # round to 2 decimal digits
        Do_min = math.ceil(100*Do_min)/100
        return Do_min
   


    def genGeometry(self):
        """
        Generate geometry for 2x1 balun
        returns polygon collections
        
        """    

        roundToGrid = self.roundToGrid
        sqrt = math.sqrt
        
        if self._geomType == "octagon":
            makeSegment = self.octSegment
        else:
            makeSegment = self.rectSegment
    
        makeRect = self.makeRect
        make45Bridge = self.make45Bridge
        fillVias = self.fillVias
            
        w = self._w
        s = self._s
        r = roundToGrid(self._r/2)
        
        e=roundToGrid(w+2*w/(1+sqrt(2)))

        centerX=self._centerX;
        centerY=self._centerY;

        signalMet = list()
        bridgeMet = list()
        vias = list()
        
        viaEnc = self._viaEnc
        viaSize = self._viaSize
        viaSpace = self._viaSpace

        for i in range(3):
           signalMet.append(makeSegment(w,r-i*(w+s), e, 0, centerX, centerY))
           signalMet.append(makeSegment(w,r-i*(w+s), e, 1, centerX, centerY))
           signalMet.append(makeSegment(w,r-i*(w+s), e, 2, centerX, centerY))
           signalMet.append(makeSegment(w,r-i*(w+s), e, 3, centerX, centerY))
    
        # Connect continous segments
        signalMet.append(makeRect( (-r+(w+s)+centerX, e+centerY), (-r+(w+s)+w+centerX, -e+centerY)))
        signalMet.append(makeRect( (-r+2*(w+s)+centerX, e+centerY), (-r+2*(w+s)+w+centerX, -e+centerY)))

        signalMet.append(makeRect( (e+centerX, -r+2*(w+s)+centerY), (-e+centerX, -r+2*(w+s)+w+centerY)))
        signalMet.append(makeRect( (e+centerX, -(-r+2*(w+s))+centerY), (-e+centerX, -(-r+2*(w+s)+w)+centerY)))

        # right
        p1,v1 = make45Bridge(w, 2*e, w+s, 0, r-2*(w+s)-w+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # Bridge
        p2,v2 = make45Bridge(w, 2*e, w+s, 0, r-2*(w+s)-w+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # Signal

        #; up
        p3,v3 = make45Bridge(w, 2*e, (w+s), 0, -e+centerX, r-2*(w+s)+s+centerY, True, True, False, viaEnc, viaSize, viaSpace) # Signal
        p4,v4 = make45Bridge(w, 2*e, (w+s), 0, -e+centerX, r-2*(w+s)+s+centerY, False, True, True, viaEnc, viaSize, viaSpace) # Bridge

        # down
        p5,v5 = make45Bridge(w, 2*e, (w+s), 0, -e+centerX, -(r-0*(w+s))+centerY, False, True, False, viaEnc, viaSize, viaSpace) # Signal
        p6,v6 = make45Bridge(w, 2*e, (w+s), 0, -e+centerX, -(r-0*(w+s))+centerY, True, True, True, viaEnc, viaSize, viaSpace) # Bridge

        appendPoly = self.appendPoly  
        appendVias = self.appendVias  
        
        appendPoly( signalMet, [p2, p3, p5])
        appendPoly( bridgeMet, [p1, p4, p6])
        appendVias( vias, [v1, v4, v6])

        # Draw connections

        c1 = makeRect( (-r+centerX, e+centerY), (-r-2.0*w+centerX, w+e+centerY) )
        c2 = makeRect( (-r+centerX, -e+centerY), (-r-2.0*w+centerX, -w-e+centerY) )
        if self._pct:
            c3 = makeRect( (-r+w+2*(w+s)+centerX, -w/2.0+centerY), (-r-2.0*w+centerX, w/2.0+centerY) )
            pctVias = fillVias(((-r+2*(w+s)+centerX, -w/2.0+centerY), (-r+w+2*(w+s)+centerX, w/2.0+centerY)), viaEnc, viaSize, viaSpace)
            appendVias(vias,[pctVias])
        c4 = makeRect( (r+centerX, e+centerY), (r+2.0*w+centerX, w+e+centerY) )
        c5 = makeRect( (r+centerX, -e+centerY), (r+2.0*w+centerX, -w-e+centerY) )
        if self._sct:
            c6 = makeRect( (-r+w+1*(w+s)+centerX, -w/2.0+centerY), (-r-2.0*w+centerX, w/2.0+centerY) )

        #
        # Make port labels
        #
        portLabels = []
        # Primary +
        X = -r-2.0*w+centerX
        Y = 0.5*w+e+centerY
        portLabels.append( ((X, Y), 'PP') )
        # Primary -
        X = -r-2.0*w+centerX
        Y = -0.5*w-e+centerY
        portLabels.append( ((X, Y), 'PN') )
        # Primary center tap
        if self._pct:
            X = -r-2.0*w+centerX
            Y = 0.0
            portLabels.append( ((X, Y), 'PT') )
        # Secondary +
        X = r+centerX+2.0*w
        Y = 0.5*w+e+centerY
        portLabels.append( ((X, Y), 'SN') )
        # Secondary -
        X = r+centerX+2.0*w
        Y = -1.0*(0.5*w+e+centerY)
        portLabels.append( ((X, Y), 'SP') )
        if self._sct:
            X = -r-2.0*w+centerX
            Y = 0.0
            portLabels.append( ((X, Y), 'ST') )
        #
        # end of port labels
        #
        
        appendPoly( signalMet, [c1, c2, c4, c5])
        if self._pct:
            appendPoly(bridgeMet, [c3])
        if self._sct:
            appendPoly(signalMet, [c6])

        Geom = (signalMet, vias, bridgeMet, portLabels)

        if self._genSubstrateContact:
            # Generate substrate contact
            subRingSpace = self._subRingSpace
            subRingW = self._subRingW
            r = self._r/2+subRingSpace
            s = subRingW
            centerX = self._centerX
            centerY = self._centerY
            geomType = self._geomType
            contEnc = self._contEnc
            contSize = self._contSize
            contSpace = self._contSpace
            diffEnc = self._diffEnc
            subCont = self.makeSubstrateContacts(subRingW, r, s, centerX, centerY, geomType, contEnc, contSize, contSpace, diffEnc)
        else:
            subCont = [[], [], [], [], []]
        return list(Geom) + list(subCont)

    def genGDSII(self, fileName, structName='bal_2x1_ec', precision=1e-9):
        """
            Generate balun 2x1 GDSII
        """
        balGeom = self.genGeometry()
        sigPolygons = balGeom[0]
        vias = balGeom[1]
        bridgePolygons = balGeom[2]
        portLabels = balGeom[3]
       
        balCell = gdspy.Cell(structName)

        sigGDSIINum = self._tech.getGDSIINumByName(self._signalLayer)  # get signal layer GDSII number
        sigGDSIIDType = self._tech.getGDSIITypeByName(self._signalLayer) # get signal layer GDSII data type
        polySet = gdspy.PolygonSet(sigPolygons, sigGDSIINum, sigGDSIIDType)
        result = gdspy.boolean(polySet, None, "or", layer=sigGDSIINum, datatype=sigGDSIIDType)
        balCell.add(result)

        bridgeGDSIINum = self._tech.getGDSIINumByName(self._bridgeLayer)  # get bridge layer GDSII number
        bridgeGDSIIDType = self._tech.getGDSIITypeByName(self._bridgeLayer) # get primary layer GDSII data type
        polySet = gdspy.PolygonSet(bridgePolygons, bridgeGDSIINum, bridgeGDSIIDType)
        balCell.add(polySet)

        viaGDSIINum = self._tech.getGDSIINumByName(self._viaLayer)  # get signal layer GDSII number
        viaGDSIIDType = self._tech.getGDSIITypeByName(self._viaLayer) 
        # add vias
        for viaRect in vias:
            balCell.add(gdspy.Rectangle(viaRect[0], viaRect[1], viaGDSIINum,viaGDSIIDType))

        for portLabel in portLabels:
            xy, name = portLabel
            if name == 'PT':
                balCell.add(gdspy.Label(name, xy, layer=bridgeGDSIINum, texttype=bridgeGDSIIDType))
            else:
                balCell.add(gdspy.Label(name, xy, layer=sigGDSIINum, texttype=sigGDSIIDType))

        #
        # Substrate contacts
        #

        # Substrate contacts
        m1Polygons = balGeom[4]
        diffPolygons = balGeom[5]
        impPolygons = balGeom[6]
        subContacts = balGeom[7]
        subPinLabels = balGeom[8]

        if self._genSubstrateContact:
            m1GDSII = self._tech.getGDSIINumByName(self._m1Layer)
            for m1Polygon in m1Polygons:
                poly = gdspy.Polygon(m1Polygon, m1GDSII)
                balCell.add(poly)

            diffGDSII = self._tech.getGDSIINumByName(self._diffLayer)
            contGDSII = self._tech.getGDSIINumByName(self._contLayer)
            for diffPolygon in diffPolygons:
                poly = gdspy.Polygon(diffPolygon, diffGDSII)
                balCell.add(poly)
                if self.emVias:
                    contPolygon = self.oversize(diffPolygon, -self._contEnc)
                    poly = gdspy.Polygon(contPolygon, contGDSII)
                    balCell.add(poly)

            if not self.emVias:
                # add vias
                for viaRect in subContacts:
                    balCell.add(gdspy.Rectangle(viaRect[0], viaRect[1], contGDSII))
            
            impLayer = self._impLayer
            if impLayer != None:
                impGDSII = self._tech.getGDSIINumByName(impLayer)
                for impPolygon in impPolygons:
                    poly = gdspy.Polygon(impPolygon, impGDSII)
                    balCell.add(poly)

            for portLabel in subPinLabels:
                xy, name = portLabel
                balCell.add(gdspy.Label(name, xy, layer=sigGDSII))

        #
        # end of substrate contacts
        #

        lib = gdspy.GdsLibrary(structName, unit = 1.0e-6, precision=precision)
        lib.add(balCell)
        lib.write_gds(fileName)

###############################################################################
#
# Balun 1 + 1 windings broadside coupled
#
###############################################################################

class balun1x1_broadsidecoupled(geomBase):
    """
        Balun 1 + 1 windings
    """

    _r = None
    _wp = None
    _ws = None
    __offset = None

    _primaryLayer = None     # Name of primary metal layer
    _secondaryLayer = None  # Name of secondary metal layer

    _viaLayer = None    # Name of via layer
    _viaEnc = 0
    _viaSize = 0
    _viaSpace = 0
    
    _pct = None     # primary center tap
    _sct = None     # secondary center tap

    _geomType = None
    
    _centerX = 0.0
    _centerY = 0.0
    
    def __init__(self,tech=None):
        self._tech = tech   # Set the technology

    def setupGeometry(self, r, wp, ws, r_offset, primaryLayer, secondaryLayer, geomType="octagon", pct = None, sct = None, centerX = None, centerY = None, subRingSpace=0.0, subRingW=0.0, diffLayer=None, implantLayer=None, contSpaceMult=4.0):
        """
            Setup balun 1x1 geometry
            r : float
                outer dimension of the
            wp : float
               primary winding line width
            ws : float
                secondary winding line width
            r_offset : foat
                radius offset of the secondary
            primaryLayer : string
                primary layer name
            secondaryLayer : string
                secondary layer name
            geomType : string
                Type of geometry. Allowed values : "rect", "octagon"
            pct : float
                if set, generates primary center tap
            sct : float
                if set, generates secondary center tap
            centerX : float
                Center of inductor x coordinate
            centerY : float
                Center of inductor y coordinate
        """
        self._r = r
        self._wp = wp
        self._ws = ws
        self._offset = r_offset 
        self._primaryLayer = primaryLayer
        self._secondaryLayer = secondaryLayer
        if (geomType != "rect") and (geomType != "octagon"):
            print("WARNING:balun1x1::setupGeometry: Unknown geometry type. Setting to octagonal.")
            self._geomType = "octagon"
        else:
            self._geomType = geomType

        if primaryLayer == secondaryLayer:
            print("ERROR:balun1x1::setupGeometry: Primary and secondary cannot be on the same metal layer.")
            return
            
        if pct == None:
            self._pct = 0
        else:
            self._pct = pct
            
        if sct == None:
            self._pct = 0
        else:
            self._sct = sct
            
                       
        if centerX == None:
            self._centerX = 0
        else:
            self._centerX = centerX
            
        if centerY == None:
            self._centerY = 0
        else:
            self._centerY = centerY

        #        
        # Substrate ring parameters
        #
        if diffLayer!=None:
            self._genSubstrateContact = True
            contLay = self._tech.findViaBotMet(diffLayer).name
            if contLay == None:
                print("ERROR:balun1x1::setupGeometry: Diffusion layer " + diffLayer + " does not have any vias connecting to it from top.")
                return

            self._diffLayer = diffLayer
            self._impLayer = implantLayer
            
            if implantLayer!=None:
                self._diffEnc = self._tech.getDRCRule(implantLayer, "enclosure")
            else:
                self._diffEnc = 0            

            self._contLayer = contLay
            #print contLay
            self._contEnc = self._tech.getDRCRule(contLay, "viaEnc")
            self._contSize = self._tech.getDRCRule(contLay, "viaSize")
            self._contSpace = self._tech.getDRCRule(contLay, "viaSpace") * contSpaceMult

            self._m1Layer = self._tech.findTopMetVia(contLay).name
            self._subRingSpace = subRingSpace
            self._subRingW = subRingW
            
        else:
            self._genSubstrateContact = False
                   
        # Dimension check: return False if diameter is too small
        return r>=self.get_min_diameter()

    
    def get_min_diameter(self):
        wp = self._wp
        ws = self._ws

        we = (wp+ws)/2
        e= we+2*we/(1+math.sqrt(2))
        
        crossover_size = 2*(ws+e)
        if self._geomType == "octagon":
            Di_min = crossover_size * (1 + math.sqrt(2))
        else:
            Di_min = crossover_size    

        Do_min = Di_min + max(wp,ws)
        # round to 2 decimal digits
        Do_min = math.ceil(100*Do_min)/100
        return Do_min


    def genGeometry(self):
        """
        Generate geometry for 1x1 balun
        returns polygon collections
        
        """    

        roundToGrid = self.roundToGrid
        sqrt = math.sqrt
        
        if self._geomType == "octagon":
            makeSegment = self.octSegment
        else:
            makeSegment = self.rectSegment
    
        makeRect = self.makeRect
        make45Bridge = self.make45Bridge
        fillVias = self.fillVias
            
        wp = self._wp
        ws = self._ws
        offset = self._offset
        r = roundToGrid(self._r/2)
        
        we = (wp+ws)/2
        e=roundToGrid(we+2*we/(1+sqrt(2)))

        centerX=self._centerX
        centerY=self._centerY

        primaryMet = list()
        secondaryMet = list()
        vias = list()
        
        primaryMet.append(makeSegment(wp,r, e, 0, centerX, centerY))
        primaryMet.append(makeSegment(wp,r, e, 1, centerX, centerY))
        primaryMet.append(makeSegment(wp,r, e, 2, centerX, centerY))
        primaryMet.append(makeSegment(wp,r, e, 3, centerX, centerY))
        
        secondaryMet.append(makeSegment(ws,r-offset, e, 0, centerX, centerY))
        secondaryMet.append(makeSegment(ws,r-offset, e, 1, centerX, centerY))
        secondaryMet.append(makeSegment(ws,r-offset, e, 2, centerX, centerY))
        secondaryMet.append(makeSegment(ws,r-offset, e, 3, centerX, centerY))
    
        #Connect continous segments

        primaryMet.append(makeRect( (e+centerX, -r+centerY), (-e+centerX, -r+wp+centerY))) #bot
        primaryMet.append(makeRect( (e+centerX, r+centerY), (-e+centerX, r-wp+centerY))) #top
        primaryMet.append(makeRect( (r-wp+centerX, e+centerY), (r+centerX, -e+centerY))) #right
        
        secondaryMet.append(makeRect( (e+centerX, -r+offset+centerY), (-e+centerX, -r+offset+ws+centerY))) #bot
        secondaryMet.append(makeRect( (e+centerX, r-offset+centerY), (-e+centerX, r-offset-ws+centerY))) #top
        secondaryMet.append(makeRect( (-r+offset+centerX, e+centerY), (-r+offset+ws+centerX, -e+centerY))) #left        
    
        appendPoly = self.appendPoly  

        # Draw connections
        
        wl = max(wp,ws)
        if offset >= 0:
            c1 = makeRect( (-r+centerX, e+centerY), (-r-2.0*wl+centerX, wp+e+centerY) )
            c2 = makeRect( (-r+centerX, -e+centerY), (-r-2.0*wl+centerX, -wp-e+centerY) )
            if self._pct:
                c3 = makeRect( (r+centerX, -wp/2.0+centerY), (r+2.0*wl+centerX, wp/2.0+centerY) )
            c4 = makeRect( (r-offset+centerX, e+centerY), (r+2.0*wl+centerX, ws+e+centerY) )
            c5 = makeRect( (r-offset+centerX, -e+centerY), (r+2.0*wl+centerX, -ws-e+centerY) )
            if self._sct:
                c6 = makeRect( (-r-2*wl+centerX, -ws/2.0+centerY), (-r+offset+centerX, ws/2.0+centerY) )
        else:
            c1 = makeRect( (-r+centerX, e+centerY), (-r-2.0*wl+offset+centerX, wp+e+centerY) )
            c2 = makeRect( (-r+centerX, -e+centerY), (-r-2.0*wl+offset+centerX, -wp-e+centerY) )
            if self._pct:
                c3 = makeRect( (r+centerX, -wp/2.0+centerY), (r-offset+2.0*wl+centerX, wp/2.0+centerY) )
            c4 = makeRect( (r-offset+centerX, e+centerY), (r-offset+2.0*wl+centerX, ws+e+centerY) )
            c5 = makeRect( (r-offset+centerX, -e+centerY), (r-offset+2.0*wl+centerX, -ws-e+centerY) )
            if self._sct:
                c6 = makeRect( (-r+offset-2*wl+centerX, -ws/2.0+centerY), (-r+offset+centerX, ws/2.0+centerY) )

        #
        # Make port labels
        #
        primPortLabels = []
        secPortLabels = []
        # Primary +
        Xpp = -r-2*wl+centerX if offset>=0 else -r+offset-2*wl+centerX
        Ypp = 0.5*wp+e+centerY
        primPortLabels.append( ((Xpp, Ypp), 'PP') )
        # Primary -
        Xpn = -r-2*wl+centerX if offset>=0 else -r+offset-2*wl+centerX
        Ypn = -0.5*wp-e+centerY
        primPortLabels.append( ((Xpn, Ypn), 'PN') )
        # Primary center tap
        if self._pct:
            Xpc = r+2*wl+centerX if offset>=0 else r-offset+2*wl
            Ypc = 0.0
            primPortLabels.append( ((Xpc, Ypc), 'PT') )
        # Secondary +
        Xsp = r+2*wl+centerX if offset>=0 else r-offset+2*wl+centerX
        Ysp = 0.5*ws+e+centerY
        secPortLabels.append( ((Xsp, Ysp), 'SN') )
        # Secondary -
        Xsn = r+2*wl+centerX if offset>=0 else r-offset+2*wl+centerX
        Ysn = -1.0*(0.5*ws+e+centerY)
        secPortLabels.append( ((Xsn, Ysn), 'SP') )
        if self._sct:
            Xsc = -r-2*wl+centerX if offset>=0 else -r+offset-2*wl+centerX
            Ysc = 0.0
            secPortLabels.append( ((Xsc, Ysc), 'ST') )
        #
        # end of port labels
        #
        
        appendPoly( primaryMet, [c1, c2])
        appendPoly( secondaryMet, [c4, c5])
        if self._pct:
            appendPoly(primaryMet, [c3])
        if self._sct:
            appendPoly(secondaryMet, [c6])

        Geom = (primaryMet, vias, secondaryMet, primPortLabels, secPortLabels)

        if self._genSubstrateContact:
            # Generate substrate contact
            subRingSpace = self._subRingSpace
            subRingW = self._subRingW
            r = self._r/2+subRingSpace
            s = subRingW
            centerX = self._centerX
            centerY = self._centerY
            geomType = self._geomType
            contEnc = self._contEnc
            contSize = self._contSize
            contSpace = self._contSpace
            diffEnc = self._diffEnc
            subCont = self.makeSubstrateContacts(subRingW, r, s, centerX, centerY, geomType, contEnc, contSize, contSpace, diffEnc)
        else:
            subCont = [[], [], [], [], []]
        return list(Geom) + list(subCont)

    def genGDSII(self, fileName, structName='bal_1x1', precision=1e-9):
        """
            Generate balun 1x1 GDSII
        """
        balGeom = self.genGeometry()
        primPolygons = balGeom[0]
        vias = balGeom[1]
        secPolygons = balGeom[2]
        primPortLabels = balGeom[3]
        secPortLabels = balGeom[4]
       
        balCell = gdspy.Cell(structName)

        primLayerGDSIINum = self._tech.getGDSIINumByName(self._primaryLayer)  # get primary layer GDSII number
        primLayerGDSIIDType = self._tech.getGDSIITypeByName(self._primaryLayer) # get primary layer GDSII data type
        polySet = gdspy.PolygonSet(primPolygons, primLayerGDSIINum, primLayerGDSIIDType)
        balCell.add(polySet)

        secLayerGDSIINum = self._tech.getGDSIINumByName(self._secondaryLayer)  # get secondary layer GDSII number
        secLayerGDSIIDType = self._tech.getGDSIITypeByName(self._secondaryLayer)
        polySet = gdspy.PolygonSet(secPolygons, secLayerGDSIINum, secLayerGDSIIDType)
        balCell.add(polySet)

        for portLabel in primPortLabels:
            xy, name = portLabel
            balCell.add(gdspy.Label(name, xy, layer=primLayerGDSIINum, texttype=primLayerGDSIIDType))
        for portLabel in secPortLabels:
            xy, name = portLabel
            balCell.add(gdspy.Label(name, xy, layer=secLayerGDSIINum, texttype=secLayerGDSIIDType))
        #
        # Substrate contacts
        #

        # Substrate contacts
        m1Polygons = balGeom[5]
        diffPolygons = balGeom[6]
        impPolygons = balGeom[7]
        subContacts = balGeom[8]
        subPinLabels = balGeom[9]

        if self._genSubstrateContact:
            m1GDSII = self._tech.getGDSIINumByName(self._m1Layer)
            for m1Polygon in m1Polygons:
                poly = gdspy.Polygon(m1Polygon, m1GDSII)
                balCell.add(poly)

            diffGDSII = self._tech.getGDSIINumByName(self._diffLayer)
            contGDSII = self._tech.getGDSIINumByName(self._contLayer)
            for diffPolygon in diffPolygons:
                poly = gdspy.Polygon(diffPolygon, diffGDSII)
                balCell.add(poly)
                if self.emVias:
                    contPolygon = self.oversize(diffPolygon, -self._contEnc)
                    poly = gdspy.Polygon(contPolygon, contGDSII)
                    balCell.add(poly)

            if not self.emVias:
                # add vias
                for viaRect in subContacts:
                    balCell.add(gdspy.Rectangle(viaRect[0], viaRect[1], contGDSII))
            
            impLayer = self._impLayer
            if impLayer != None:
                impGDSII = self._tech.getGDSIINumByName(impLayer)
                for impPolygon in impPolygons:
                    poly = gdspy.Polygon(impPolygon, impGDSII)
                    balCell.add(poly)

            for portLabel in subPinLabels:
                xy, name = portLabel
                balCell.add(gdspy.Label(name, xy, layer=sigGDSII))

        #
        # end of substrate contacts
        #

        lib = gdspy.GdsLibrary(structName, unit = 1.0e-6, precision=precision)
        lib.add(balCell)
        lib.write_gds(fileName)

###############################################################################
#
# Balun 2 + 1 windings broadside coupled
#
###############################################################################

class balun2x1_broadsidecoupled(geomBase):
    """
        Balun 2 + 1 windings
    """

    _r = None
    _wp = None
    _ws = None
    _offset = None
    _sp = None

    _primaryLayer = None     # Name of primary layer
    _primaryBrigdeLayer = None # name of primary spiral bridge layer
    _secondaryLayer = None  # Name of secondary layer

    _viaLayer = None    # Name of via layer
    _viaEnc = 0
    _viaSize = 0
    _viaSpace = 0
    
    _pct = None     # primary center tap
    _sct = None     # secondary center tap

    _geomType = None
    
    _centerX = 0.0
    _centerY = 0.0
    
    def __init__(self,tech=None):
        self._tech = tech   # Set the technology

    def setupGeometry(self, r, wp, ws, r_offset, primaryLayer, primaryBridgeLayer, secondaryLayer, sp, geomType="octagon", pct = None, sct = None, centerX = None, centerY = None, subRingSpace=0.0, subRingW=0.0, diffLayer=None, implantLayer=None, contSpaceMult=4.0):
        """
            Setup balun 2x1 geometry
            r : float
                outer inductor dimension
            wp : float
               primary winding line width
            ws : float
                secondary winding line width
            r_offset : foat
                radius offset of the secondary
            primaryLayer : string
                primary layer name
            primaryBridgeLayer: string
                primary bridge metal layer name
            secondaryLayer : string
                secondary layer name
            sp : float
                separation of the primary windings
            geomType : string
                Type of geometry. Allowed values : "rect", "octagon"
            pct : float
                if set, generates primary center tap
            sct : float
                if set, generates secondary center tap
            centerX : float
                Center of inductor x coordinate
            centerY : float
                Center of inductor y coordinate
        """
        self._r = r
        self._wp = wp
        self._ws = ws
        self._sp = sp
        self._offset = r_offset  # conversion from centerline to outer radius offset
        self._primaryLayer = primaryLayer
        self._primaryBridgeLayer = primaryBridgeLayer
        self._secondaryLayer = secondaryLayer
        if (geomType != "rect") and (geomType != "octagon"):
            print("WARNING:balun2x1_broadsidecoupled::setupGeometry: Unknown geometry type. Setting to octagonal.")
            self._geomType = "octagon"
        else:
            self._geomType = geomType
        
        if self._primaryLayer == self._secondaryLayer or self._primaryBrigdeLayer == self._secondaryLayer:
            print("ERROR:balun2x1_broadsidecoupled::setupGeometry: Primary or primary brigde layer cannot be on the same layer as the secondary.")
            exit(1)
        if self._primaryLayer == self._primaryBrigdeLayer:
            print("ERROR:balun2x1_broadsidecoupled::setupGeometry: Primary bridge layer cannot be the same as the main primary layer.")
            exit(1)
            
        if pct == None:
            self._pct = 0
        else:
            self._pct = pct
            
        if sct == None:
            self._pct = 0
        else:
            self._sct = sct
            
                       
        if centerX == None:
            self._centerX = 0
        else:
            self._centerX = centerX
            
        if centerY == None:
            self._centerY = 0
        else:
            self._centerY = centerY

        # Find via, find via rules
        if self._tech.findViaTopMet(primaryLayer) == self._tech.findViaBotMet(primaryBridgeLayer): # try overpass
            viaLay = self._tech.findViaTopMet(primaryLayer)
        elif self._tech.findViaBotMet(primaryLayer) == self._tech.findViaTopMet(primaryBridgeLayer): # try underpass
            viaLay = self._tech.findViaBotMet(primaryLayer)              
        else:
            print("ERROR:balun2x1::setupGeometry: Primary layer and primary bridge layer must be adjacent. ")
            exit(1)
        
        viaName = viaLay.name
        self._viaLayer = viaName
        self._viaEnc = self._tech.getDRCRule(viaName, "viaEnc")
        self._viaSize = self._tech.getDRCRule(viaName, "viaSize")
        self._viaSpace = self._tech.getDRCRule(viaName, "viaSpace")

        #        
        # Substrate ring parameters
        #
        if diffLayer!=None:
            self._genSubstrateContact = True
            contLay = self._tech.findViaBotMet(diffLayer).name
            if contLay == None:
                print("ERROR:balun2x1::setupGeometry: Diffusion layer " + diffLayer + " does not have any vias connecting to it from top.")
                return

            self._diffLayer = diffLayer
            self._impLayer = implantLayer
            
            if implantLayer!=None:
                self._diffEnc = self._tech.getDRCRule(implantLayer, "enclosure")
            else:
                self._diffEnc = 0            

            self._contLayer = contLay
            #print contLay
            self._contEnc = self._tech.getDRCRule(contLay, "viaEnc")
            self._contSize = self._tech.getDRCRule(contLay, "viaSize")
            self._contSpace = self._tech.getDRCRule(contLay, "viaSpace") * contSpaceMult

            self._m1Layer = self._tech.findTopMetVia(contLay).name
            self._subRingSpace = subRingSpace
            self._subRingW = subRingW
            
        else:
            self._genSubstrateContact = False
 
        # Dimension check: return False if diameter is too small
        return r >= self.get_min_diameter()


    def get_min_diameter(self):
    # Calculate the minimum possible diameter for octagon balun with m+n turns
        wp = self._wp
        sp = self._sp
        ws = self._ws
     
        e = wp + 2*wp/(1+math.sqrt(2))
        crossover_size = 3*wp + 2*e

        if self._geomType == "octagon":
            Di_min = crossover_size * (1 + math.sqrt(2))
        else:
            Di_min = crossover_size#  + 2*sp    

        Do_min = Di_min + max(ws, 2*wp+sp)
        # round to 2 decimal digits
        Do_min = math.ceil(100*Do_min)/100
        return Do_min


    def genGeometry(self):
        """
        Generate geometry for 2x1 balun
        returns polygon collections
        
        """    

        roundToGrid = self.roundToGrid
        sqrt = math.sqrt
        
        if self._geomType == "octagon":
            makeSegment = self.octSegment
        else:
            makeSegment = self.rectSegment
    
        makeRect = self.makeRect
        make45Bridge = self.make45Bridge
        fillVias = self.fillVias
            
        wp = roundToGrid(self._wp)
        ws = roundToGrid(self._ws)
        sp = roundToGrid(self._sp)
        offset = roundToGrid(self._offset)
        r = roundToGrid(self._r/2)
        
        e=roundToGrid(wp+2*wp/(1+sqrt(2)))

        centerX=self._centerX
        centerY=self._centerY

        primaryMet = list()
        secondaryMet = list()
        bridgeMet = list()
        vias = list()

        viaEnc = self._viaEnc
        viaSize = self._viaSize
        viaSpace = self._viaSpace

        
        primaryMet.append(makeSegment(wp,r, e, 0, centerX, centerY))
        primaryMet.append(makeSegment(wp,r, e, 1, centerX, centerY))
        primaryMet.append(makeSegment(wp,r, e, 2, centerX, centerY))
        primaryMet.append(makeSegment(wp,r, e, 3, centerX, centerY))

        primaryMet.append(makeSegment(wp,r-(wp+sp), e, 0, centerX, centerY))
        primaryMet.append(makeSegment(wp,r-(wp+sp), e, 1, centerX, centerY))
        primaryMet.append(makeSegment(wp,r-(wp+sp), e, 2, centerX, centerY))
        primaryMet.append(makeSegment(wp,r-(wp+sp), e, 3, centerX, centerY))
        
        secondaryMet.append(makeSegment(ws,r-offset, e, 0, centerX, centerY))
        secondaryMet.append(makeSegment(ws,r-offset, e, 1, centerX, centerY))
        secondaryMet.append(makeSegment(ws,r-offset, e, 2, centerX, centerY))
        secondaryMet.append(makeSegment(ws,r-offset, e, 3, centerX, centerY))
    
        #Connect continous segments

        primaryMet.append(makeRect( (e+centerX, -r+centerY), (-e+centerX, -r+wp+centerY))) #bot t1
        primaryMet.append(makeRect( (e+centerX, r+centerY), (-e+centerX, r-wp+centerY))) #top t1
        primaryMet.append(makeRect( (e+centerX, -r+sp+wp+centerY), (-e+centerX, -r+2*wp+sp+centerY))) #bot t2
        primaryMet.append(makeRect( (e+centerX, r-sp-wp+centerY), (-e+centerX, r-2*wp-sp+centerY))) #top t2
        primaryMet.append(makeRect( (-r+wp+sp+centerX, e+centerY), (-r+2*wp+sp+centerX, -e+centerY))) # t2 left 
        
        p1,v1 = make45Bridge(wp, 2*e, wp+sp, 0, r-1*(wp+sp)-wp+centerX, -e+centerY, False, False, False, viaEnc, viaSize, viaSpace) # signal
        p2,v2 = make45Bridge(wp, 2*e, wp+sp, 0, r-1*(wp+sp)-wp+centerX, -e+centerY, True, False, True, viaEnc, viaSize, viaSpace) # bridge        

        secondaryMet.append(makeRect( (e+centerX, -r+offset+centerY), (-e+centerX, -r+offset+ws+centerY))) #bot
        secondaryMet.append(makeRect( (e+centerX, r-offset+centerY), (-e+centerX, r-offset-ws+centerY))) #top
        secondaryMet.append(makeRect( (-r+offset+centerX, e+centerY), (-r+offset+ws+centerX, -e+centerY))) #left        
    
        appendPoly = self.appendPoly  
        appendVias = self.appendVias  
        
        appendPoly( primaryMet, [p1])
        appendPoly( bridgeMet, [p2])
        appendVias( vias, [v2])  

        # Draw connections
        
        wl = max(wp,ws)
        if offset >= 0:
            c1 = makeRect( (-r+centerX, e+centerY), (-r-2.0*wl+centerX, wp+e+centerY) )
            c2 = makeRect( (-r+centerX, -e+centerY), (-r-2.0*wl+centerX, -wp-e+centerY) )
            if self._pct:
                c3 = makeRect( (-r+wp+sp+centerX, -wp/2.0+centerY), (-r-2.0*wl+centerX, wp/2.0+centerY) )
            c4 = makeRect( (r-offset+centerX, e+centerY), (r+2.0*wl+centerX, ws+e+centerY) )
            c5 = makeRect( (r-offset+centerX, -e+centerY), (r+2.0*wl+centerX, -ws-e+centerY) )
            if self._sct:
                c6 = makeRect( (-r-2*wl+centerX, -ws/2.0+centerY), (-r+offset+centerX, ws/2.0+centerY) )
        else:
            c1 = makeRect( (-r+centerX, e+centerY), (-r-2.0*wl+offset+centerX, wp+e+centerY) )
            c2 = makeRect( (-r+centerX, -e+centerY), (-r-2.0*wl+offset+centerX, -wp-e+centerY) )
            if self._pct:
                c3 = makeRect( (-r+wp+sp-centerX, -wp/2.0+centerY), (-r+offset-2.0*wl+centerX, wp/2.0+centerY) )
            c4 = makeRect( (r-offset+centerX, e+centerY), (r-offset+2.0*wl+centerX, ws+e+centerY) )
            c5 = makeRect( (r-offset+centerX, -e+centerY), (r-offset+2.0*wl+centerX, -ws-e+centerY) )
            if self._sct:
                c6 = makeRect( (-r+offset-2*wl+centerX, -ws/2.0+centerY), (-r+offset+centerX, ws/2.0+centerY) )

        #
        # Make port labels
        #
        primPortLabels = []
        secPortLabels = []
        # Primary +
        Xpp = -r-2*wl+centerX if offset>=0 else -r+offset-2*wl+centerX
        Ypp = 0.5*wp+e+centerY
        primPortLabels.append( ((Xpp, Ypp), 'PP') )
        # Primary -
        Xpn = -r-2*wl+centerX if offset>=0 else -r+offset-2*wl+centerX
        Ypn = -0.5*wp-e+centerY
        primPortLabels.append( ((Xpn, Ypn), 'PN') )
        # Primary center tap
        if self._pct:
            Xpc = -r-2*wl+centerX if offset>=0 else -r+offset-2*wl
            Ypc = 0.0
            primPortLabels.append( ((Xpc, Ypc), 'PT') )
        # Secondary +
        Xsp = r+2*wl+centerX if offset>=0 else r-offset+2*wl+centerX
        Ysp = 0.5*ws+e+centerY
        secPortLabels.append( ((Xsp, Ysp), 'SN') )
        # Secondary -
        Xsn = r+2*wl+centerX if offset>=0 else r-offset+2*wl+centerX
        Ysn = -1.0*(0.5*ws+e+centerY)
        secPortLabels.append( ((Xsn, Ysn), 'SP') )
        if self._sct:
            Xsc = -r-2*wl+centerX if offset>=0 else -r+offset-2*wl+centerX
            Ysc = 0.0
            secPortLabels.append( ((Xsc, Ysc), 'ST') )
        #
        # end of port labels
        #
        
        appendPoly( primaryMet, [c1, c2])
        appendPoly( secondaryMet, [c4, c5])
        if self._pct:
            appendPoly(primaryMet, [c3])
        if self._sct:
            appendPoly(secondaryMet, [c6])


        Geom = (primaryMet, bridgeMet, secondaryMet, vias, primPortLabels, secPortLabels)

        if self._genSubstrateContact:
            # Generate substrate contact
            subRingSpace = self._subRingSpace
            subRingW = self._subRingW
            r = self._r/2+subRingSpace
            s = subRingW
            centerX = self._centerX
            centerY = self._centerY
            geomType = self._geomType
            contEnc = self._contEnc
            contSize = self._contSize
            contSpace = self._contSpace
            diffEnc = self._diffEnc
            subCont = self.makeSubstrateContacts(subRingW, r, s, centerX, centerY, geomType, contEnc, contSize, contSpace, diffEnc)
        else:
            subCont = [[], [], [], [], []]
        return list(Geom) + list(subCont)

    def genGDSII(self, fileName, structName='bal_1x1', precision=1e-9):
        """
            Generate balun 1x1 GDSII
        """
        balGeom = self.genGeometry()
        primPolygons = balGeom[0]
        bridgePolygons = balGeom[1]
        vias = balGeom[3]
        secPolygons = balGeom[2]
        primPortLabels = balGeom[4]
        secPortLabels = balGeom[5]
       
        balCell = gdspy.Cell(structName)

        primLayerGDSIINum = self._tech.getGDSIINumByName(self._primaryLayer)  # get primary layer GDSII number
        primLayerGDSIIDType = self._tech.getGDSIITypeByName(self._primaryLayer) # get primary layer GDSII data type
        polySet = gdspy.PolygonSet(primPolygons, primLayerGDSIINum, primLayerGDSIIDType)
        result = gdspy.boolean(polySet, None, "or", layer=primLayerGDSIINum, datatype=primLayerGDSIIDType)
        balCell.add(result)

        bridgeLayerGDSIINum = self._tech.getGDSIINumByName(self._primaryBridgeLayer)  # get secondary layer GDSII number
        bridgeLayerGDSIIDType = self._tech.getGDSIITypeByName(self._primaryBridgeLayer)
        polySet = gdspy.PolygonSet(bridgePolygons, bridgeLayerGDSIINum, bridgeLayerGDSIIDType)
        balCell.add(polySet)

        secLayerGDSIINum = self._tech.getGDSIINumByName(self._secondaryLayer)  # get secondary layer GDSII number
        secLayerGDSIIDType = self._tech.getGDSIITypeByName(self._secondaryLayer)
        polySet = gdspy.PolygonSet(secPolygons, secLayerGDSIINum, secLayerGDSIIDType)
        result = gdspy.boolean(polySet, None, "or", layer=secLayerGDSIINum, datatype=secLayerGDSIIDType)
        balCell.add(result)

        viaGDSIINum = self._tech.getGDSIINumByName(self._viaLayer)  # get signal layer GDSII number
        viaGDSIIDType = self._tech.getGDSIITypeByName(self._viaLayer)
        # add vias
        for viaRect in vias:
            balCell.add(gdspy.Rectangle(viaRect[0], viaRect[1], viaGDSIINum, viaGDSIIDType))

        for portLabel in primPortLabels:
            xy, name = portLabel
            balCell.add(gdspy.Label(name, xy, layer=primLayerGDSIINum, texttype=primLayerGDSIIDType))
        for portLabel in secPortLabels:
            xy, name = portLabel
            balCell.add(gdspy.Label(name, xy, layer=secLayerGDSIINum, texttype=secLayerGDSIIDType))
        #
        # Substrate contacts
        #

        # Substrate contacts
        m1Polygons = balGeom[6]
        diffPolygons = balGeom[7]
        impPolygons = balGeom[8]
        subContacts = balGeom[9]
        subPinLabels = balGeom[10]

        if self._genSubstrateContact:
            m1GDSII = self._tech.getGDSIINumByName(self._m1Layer)
            for m1Polygon in m1Polygons:
                poly = gdspy.Polygon(m1Polygon, m1GDSII)
                balCell.add(poly)

            diffGDSII = self._tech.getGDSIINumByName(self._diffLayer)
            contGDSII = self._tech.getGDSIINumByName(self._contLayer)
            for diffPolygon in diffPolygons:
                poly = gdspy.Polygon(diffPolygon, diffGDSII)
                balCell.add(poly)
                if self.emVias:
                    contPolygon = self.oversize(diffPolygon, -self._contEnc)
                    poly = gdspy.Polygon(contPolygon, contGDSII)
                    balCell.add(poly)

            if not self.emVias:
                # add vias
                for viaRect in subContacts:
                    balCell.add(gdspy.Rectangle(viaRect[0], viaRect[1], contGDSII))
            
            impLayer = self._impLayer
            if impLayer != None:
                impGDSII = self._tech.getGDSIINumByName(impLayer)
                for impPolygon in impPolygons:
                    poly = gdspy.Polygon(impPolygon, impGDSII)
                    balCell.add(poly)

            for portLabel in subPinLabels:
                xy, name = portLabel
                balCell.add(gdspy.Label(name, xy, layer=sigGDSII))

        #
        # end of substrate contacts
        #

        lib = gdspy.GdsLibrary(structName, unit = 1.0e-6, precision=precision)
        lib.add(balCell)
        lib.write_gds(fileName)
    


def balun_MxN_get_min_diameter(self, m, n):
# Calculate the minimum possible diameter for octagon balun with m+n turns
    w = self._w
    s = self._s

    e = w+s+2*w/(1+math.sqrt(2))
    crossover_size = 2*(w+e)
    if self._geomType == "octagon":
        Di_min = crossover_size * (1 + math.sqrt(2))
    else:
        Di_min = crossover_size + 2*s    

    Do_min = (Di_min + 2*(m+n)*w + 2*(m+n-1)*s)
    # round to 2 decimal digits
    Do_min = math.ceil(100*Do_min)/100
    return Do_min
