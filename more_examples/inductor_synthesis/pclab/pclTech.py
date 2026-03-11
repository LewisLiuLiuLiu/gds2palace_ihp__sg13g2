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

"""
Technology classes

Tech file format:
Technology is described with parameters and layers.
Layer properties are described in Layer class.
Default unit for length is micrometer.

Manufacturing grid:
grid = <value_in_um>

Layer definition:
layer <layer_name> <layer_type>
    <property> = <value>
endlayer

Comments:
# This is a comment
<statements>  # This is also a comment



"""

# Add display class
# Line styles, stipples



class Layer:
    """
    # - not fully implemented
    Layer in a technology.
    Available layer properties:
    
    General:
    string name         - Layer name
    string ltype        - Type of layer. Available choices: metal, via, dielectric

    Import/export:
    int GDSIINum        - GDSII layer number (0-255). -1 means not set
    int GDSIIType       - GDSII layer type (purpose) 0-255. -1 means not set
    
    Physical properties:
    float h             - Height of layer in micrometers
    float t             - Thickness of layer in micrometers
    float cond          - Conductivity of layer in S/m
    float er            - Relative permitivity of material
    
    Via properties:
    string botmet       - Bottom metal
    string topmet       - Top metal 
    
    float viaEnc       - Via enclosure
    float viaSize      - Via size
    float viaSpace     - Via space

    DRC properties:
    float minw          - Minimum width in micrometers. Ignored if set to 0.
    float maxw          - Maximum width in micrometers. Ignored if set to 0.
    float mins          - Minimum spacing in micrometers. Ignored if set to 0.
    float maxs          - Maximum spacing in micrometers. Ignored if set to 0.
    float minarea       - Minimum area. Ignored if set to 0.
        
    Display:    
    int list color      - RGB color of layer, default (0,0,0)
    int alpha           - Transparency, default 
    string stipple      - Name of stipple
    """
    
    def __init__(self, name, ltype, GDSIINum=-1, GDSIIType=-1, h=0, t=0, cond=0, er=1, minw=0, maxw=0, mins=0, maxs=0, minarea=0, color=0, alpha=255, viaEnc=0, viaSize=0, viaSpace=0, stipple=None):
        self.name = name
        self.ltype = ltype
        self.GDSIINum = GDSIINum
        self.GDSIIType = GDSIIType
        self.h = h
        self.t = t
        self.cond = cond
        self.er = er
        self.minw = minw
        self.maxw = maxw
        self.mins = mins
        self.maxs = maxs
        self.enclosure = 0
        self.minArea = minarea
        self.color = color
        self.alpha = alpha
        self.topmet = None
        self.botmet = None
        self.viaEnc = viaEnc
        self.viaSize = viaSize
        self.viaSpace = viaSpace
        self.strStipple = stipple
        self.stipple = None
        
    def __str__(self):
        s=""
        s=s+"Layer::Info : layer "+self.name+" type = "+self.ltype+"\n"
        s=s+"Layer::GDSII: GDSII number = "+str(self.GDSIINum)+", type = "+str(self.GDSIIType)+"\n"
        s=s+"Layer::Phys : height = "+str(self.h)+" um, thickness = "+str(self.t)+", conductivity = "+str(self.cond)+", er = "+str(self.er)+"\n"
        if self.ltype=="via":
            s=s+"Layer::Conn : botmet = "+self.botmet+", topmet = "+self.topmet+"\n"
            s=s+"Layer::DRC  : viaEnc = "+str(self.viaEnc)+", viaSize = "+str(self.viaSize)+", viaSpace = "+str(self.viaSpace)+"\n"
        else:
            s=s+"Layer::DRC  : minw = "+str(self.minw)+", maxw = "+str(self.maxw)+", mins = "+str(self.mins)+", maxs = "+str(self.maxs)+", minarea = "+str(self.minArea)+"\n"
        s=s+"Layer::Misc : color = "+str(self.color)+", alpha = "+str(self.alpha)+", stipple = "+str(self.stipple)
        return s

class Technology:
    """
    
    """
    _techName=""
    _techLayers=[]   # Defined layers in technology
    _techGrid=0      # Technology grid

    def __init__(self,techFile=None):
        """
        Constructor that loads technology from a specified file.
        """
        if techFile==None:
            return
        
        self.loadTech(techFile)

    def __str__(self):
        numlay=len(self._techLayers)    # Get the number of layers in technology
        laynames=""
        for lay in self._techLayers:    # Concatenate all layer names
            laynames = laynames+" "+lay.name
        laynames=laynames.strip()
        s=""
        s=s+"Technology::Info : Name = "+self._techName +", grid = "+str(self._techGrid)+"\n"
        s=s+"Technology::Layer: "+str(numlay)+" defined\n"
        s=s+"Technology::Layer: "+laynames
        return s
        

    def _stripComments(self,line):
        tmp = line.split("#")[0] # Strip comments
        tmp = tmp.strip() # Strip white space at begining and end
        return tmp
    
    def findLayerByName(self, layerName):
        """
        Find a layer in technology by name.
        Returns None if not found
        """
        for lay in self._techLayers:
            if lay.name == layerName:
                return lay
        return None    

    def getGDSIINumByName(self, layerName):
        """
        Find a layer number in technology by name.
        Returns None if not found
        """
        for lay in self._techLayers:
            if lay.name == layerName:
                return lay.GDSIINum
        return None

    def getGDSIITypeByName(self, layerName):
        """
        Find a layer data type in technology by name.
        Returns None if not found
        """
        for lay in self._techLayers:
            if lay.name == layerName:
                return lay.GDSIIType
        return None     


    def findViaTopMet(self, topmetName):
        """
        Find a via which has a given top metal
        """
        for lay in self._techLayers:
            if lay.ltype == "via":
                if lay.topmet == topmetName:
                    return lay
        return None
    
    def findViaBotMet(self, botmetName):
        """
        Find a via which has a given bottom metal
        """
        for lay in self._techLayers:
            if lay.ltype == "via":
                if lay.botmet == botmetName:
                    return lay
        return None

    def findTopMetVia(self, viaName):
        """
        Find a metal which is a top metal for given via
        """
        via = self.findLayerByName(viaName)
        topMet = via.topmet
        return self.findLayerByName(topMet)

    def findBotMetVia(self, viaName):
        """
        Find a metal which is a bottom metal for given via
        """
        via = self.findLayerByName(viaName)
        botMet = via.topmet
        return self.findLayerByName(botMet)


    def getDRCRule(self, layName, ruleName):
        """
        Get a DRC rule given by ruleName for layer layName
        """
        layer = self.findLayerByName(layName)
        if layer == None:
            return None
        if ruleName == "minw":
            return layer.minw
        elif ruleName == "maxw":
            return layer.maxw
        elif ruleName == "mins":
            return layer.mins
        elif ruleName == "maxs":
            return layer.maxs
        elif ruleName == "minArea":        
            return layer.minArea
        elif ruleName == "viaEnc":
            return layer.viaEnc
        elif ruleName == "viaSize":
            return layer.viaSize
        elif ruleName == "viaSpace":
            return layer.viaSpace
        elif ruleName == "enclosure":
            return layer.enclosure
        else:
            return None                                                      
        
    def loadTech(self,techFile):
        """
        Load technology from a specified file.
        
        """
        
        inFile=open(techFile,'r')
        
        self._techName=techFile.split('.')[0]
        
        lineNo=1
        err = 0
        line=inFile.readline()
        while line:
            # Scan through the technology file
            line = self._stripComments(line)
            if len(line)==0:
                lineNo = lineNo+1
                line=inFile.readline() # Empty or comment line, no need to process it. Read next line
                continue
            tok = line.split()  # Split the line into tokens
            if 'grid' in tok[0]:
                # Technology grid
                tok = line.split('=')
                self.setGrid(float(tok[1]))
            elif tok[0] == 'layer':
                # Layer definition
                if len(tok) != 3:
                    print ("ERROR::Technology::loadTech: Invalid number of arguments in layer definition at line "+str(lineNo)+". Expected 2, got "+str(len(tok)-1)+".")
                    err=1
                    break
                lname = tok[1].strip() # Layer name
                ltype = tok[2].strip() # Layer type
                # Create layer
                tlay = Layer(lname, ltype)
                while True:
                    # Read layer properties
                    line = self._stripComments(inFile.readline()) # Read next line
                    if len(line)==0:
                        continue
                    lineNo = lineNo + 1
                    tok = line.split('=')
                    tokw=tok[0].strip()
                    if 'endlayer' in line:
                        # Finished reading layer, add the layer to technology
                        self._techLayers.append(tlay)
                        break
                    elif tokw == 'GDSIINum':
                        tlay.GDSIINum = int(tok[1])
                    elif tokw == 'GDSIIType':
                        tlay.GDSIIType = int(tok[1])
                    elif tokw == 'h':
                        tlay.h = float(tok[1])
                    elif tokw == 't':
                        tlay.t = float(tok[1])
                    elif tokw == 'cond':
                        tlay.cond = float(tok[1])
                    elif tokw == 'er':
                        tlay.er = float(tok[1])
                    elif tokw == 'botmet':
                        if (tlay.ltype) != 'via':
                            print ("ERROR::Technology::loadTech: Bottom metal specification is valid only for vias")
                            err=1
                            break
                        tlay.botmet = tok[1].strip()
                    elif tokw == 'topmet':
                        if (tlay.ltype) != 'via':
                            print ("ERROR::Technology::loadTech: Top metal specification is valid only for vias")
                            err=1
                            break
                        tlay.topmet = tok[1].strip()
                    elif tokw == 'minw':
                        if (float(tok[1])) <0:
                            print ("ERROR::Technology::loadTech: Minimum width must be positive.")
                            err=1
                            break
                        tlay.minw = float(tok[1])
                    elif tokw == 'maxw':
                        if (float(tok[1])) <0:
                            print ("ERROR::Technology::loadTech: Maximum width must be positive.")
                            err=1
                            break
                        tlay.maxw = float(tok[1])
                    elif tokw == 'mins':
                        if (float(tok[1])) <0:
                            print ("ERROR::Technology::loadTech: Minimum spacing must be positive.")
                            err=1
                            break
                        tlay.mins = float(tok[1])
                    elif tokw == 'maxs':
                        if (float(tok[1])) <0:
                            print ("ERROR::Technology::loadTech: Maximum spacing must be positive.")
                            err=1
                            break
                        tlay.maxs = float(tok[1])
                    elif tokw == 'minArea':
                        if (float(tok[1])) <0:
                            print ("ERROR::Technology::loadTech: Minimum area must be positive.")
                            err=1
                            break
                        tlay.minArea = float(tok[1])
                    elif tokw == 'viaEnc':
                        if (float(tok[1])) <0:
                            print ("ERROR::Technology::loadTech: Via enclosure must be positive.")
                            err=1
                            break
                        tlay.viaEnc = float(tok[1])
                    elif tokw == 'viaSize':
                        if (float(tok[1])) <0:
                            print ("ERROR::Technology::loadTech: Via size must be positive.")
                            err=1
                            break
                        tlay.viaSize = float(tok[1])
                    elif tokw == 'viaSpace':
                        if (float(tok[1])) <0:
                            print ("ERROR::Technology::loadTech: Via spacing must be positive.")
                            err=1
                            break
                        tlay.viaSpace = float(tok[1])
                    elif tokw == 'enclosure':
                        if (float(tok[1])) <0:
                            print ("ERROR::Technology::loadTech: Enclosure must be positive.")
                            err=1
                            break
                        tlay.enclosure = float(tok[1])                        

                    elif tokw == 'color':
                        # tok[1] = '(rval,gval,bval)'
                        # remove ( and )
                        tmp = tok[1].strip()
                        tmp = tmp[2:len(tmp)]
                        tmp = tmp[1:len(tmp)-1]
                        ltmp = tmp.split(',')
                        red = int(ltmp[0])
                        green = int(ltmp[1])
                        blue = int(ltmp[2])
                        tlay.color = (red,green,blue)
                    elif tokw == 'alpha':
                        if (int(tok[1]) <0) or (int(tok[1]) > 255):
                            print ("ERROR::Technology::loadTech: Alpha must be between 0 and 255")
                            err=1
                            break
                        tlay.alpha = int(tok[1])
                    elif tokw == 'stipple':
                        tlay.strStipple = tok[1]
                    else:
                        print ("ERROR::Technology::loadTech: Unknown argument at line "+str(lineNo)+"\n"+line)
                        err=1
                        break
            
            if err==1:
                break 
            line=inFile.readline() # Read next line

        inFile.close()
        if err==1:
            # There was an error reading the technology file, return None
            return None            
        
        # Recalculate parameters
        

    def setGrid(self,grid):
        self._techGrid=grid
    
    def getGrid(self):
        return self._techGrid
        
   
    
