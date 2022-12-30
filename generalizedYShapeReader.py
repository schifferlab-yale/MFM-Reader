
from functools import cache
from random import random
import time
from generalizedYShapeAnalysis import YLattice
from newNodeNetwork import NodeNetwork, Node
import numpy as np
import cv2
import math
import argparse

#Set up argparser to allow for input image
parser = argparse.ArgumentParser(description='MFM image analysis')
parser.add_argument('image', metavar='image', type=str, nargs='+',help='Path of image')
parser.add_argument('-s', "--spacing",  help="how dense the islands are packed small=denser (default=0.25)", type=float, default=0.25)
parser.add_argument("-t", "--trim", help="Set if the offset row is shorter than the non-offset rows",action="store_true", default=False)
parser.add_argument("-a", "--reference_image", help="image of the height(to help line up the sample points)", type=str)
args=parser.parse_args()

WINDOWSIZE=800


#read image and reference image
try:
    phase_image = cv2.imread(args.image[0])
    phase_image=cv2.resize(phase_image,(WINDOWSIZE,WINDOWSIZE))
except:
    raise Exception("File not found")

if args.reference_image is not None:
    try:
        height_image = cv2.imread(args.reference_image)
        height_image = cv2.resize(height_image, (WINDOWSIZE,WINDOWSIZE))
    except:
        raise Exception("File not found")
else:
    height_image=np.zeros((WINDOWSIZE,WINDOWSIZE,3), np.uint8)



def getBWImage(image):
        pointSampleWidth=1
        avg_color_per_row = np.average(image, axis=0)
        avg_color = np.average(avg_color_per_row, axis=0)
        avg=np.average(avg_color,axis=0)


        print("Average color:",avg)
        blur = cv2.GaussianBlur(image,(pointSampleWidth,pointSampleWidth),15)

        blurredImage=blur
        blur=cv2.cvtColor(blur,cv2.COLOR_RGB2GRAY)
        BWImage=cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11,0)
        #BWImage=cv2.cvtColor(BWImage,cv2.COLOR_GRAY2RGB)

        return BWImage

global lastMouse

def degToRad(ang):
    return ang*np.pi/180
def cosDeg(ang):
    return np.cos(degToRad(ang))
def sinDeg(ang):
    return np.sin(degToRad(ang))

class RowCol:
    def __init__(self,row,col):
        self.row=row
        self.col=col
    def __str__(self) -> str:
        return f"r{self.row}c{self.col}"
    def __hash__(self):
        return hash(str(self))


class YIsland():
    def __init__(self,row,col,leg1Angle,radius):
        self.leg1Angle=leg1Angle
        self.row=row
        self.col=col
        self.radius=radius

    def getPoints(self):
        
        center=np.array([self.col,self.row])
        points=[center]
        for angle in [self.leg1Angle, self.leg1Angle+120, self.leg1Angle+240]:
            points.append(center+self.radius*np.array([cosDeg(angle),sinDeg(angle)]))

        return [RowCol(point[1],point[0]) for point in points]

    def hasError(colorPattern):
        return sum(colorPattern)!=0

class Pattern:
    def __init__(self,repeatRow,repeatCol):
        self.repeatRow=repeatRow
        self.repeatCol=repeatCol
        self.islands=[]

        self.colOffset=0
        self.rowOffset=0

        self.colEndOffset=0
        self.rowEndOffset=0


    def addIsland(self,island):
        self.islands.append(island)

    def invalidateCache(self):
        self.getSamplePoints.cache_clear()




    @cache
    def getSamplePoints(self,maxRow,maxCol):
        if self.colOffset>0:self.colOffset-=self.repeatCol
        if self.colOffset<-self.repeatCol: self.colOffset+=self.repeatCol
        if self.rowOffset>0:self.rowOffset-=self.repeatRow
        if self.rowOffset<-self.repeatRow: self.rowOffset+=self.repeatRow
        if self.colEndOffset>0:self.colEndOffset=0
        if self.rowEndOffset>0:self.rowEndOffset=0

        legAngles=[]
        points=[]
        for island in self.islands:
            islePoints=island.getPoints()
            for point in islePoints:
                point.row-=2*self.rowOffset
                point.col-=2*self.colOffset
            points.append(islePoints)
            legAngles.append(island.leg1Angle)


        newPoints=[]
        for i in range(math.floor(self.rowOffset),math.ceil(maxRow/self.repeatRow)):
            for island,legAngle in zip(points,legAngles):
                pointGroup=[]
                for point in island:
                    pointGroup.append(RowCol(point.row+i*self.repeatRow,point.col))
                newPoints.append(pointGroup)
                legAngles.append(legAngle)
        points+=newPoints


        newPoints=[]
        for i in range(math.floor(self.colOffset),math.ceil(maxCol/self.repeatCol)):
            for island,legAngle in zip(points,legAngles):
                pointGroup=[]
                for point in island:
                    pointGroup.append(RowCol(point.row,point.col+i*self.repeatCol))
                newPoints.append(pointGroup)
                legAngles.append(legAngle)
        points+=newPoints



        validPoints=[]
        validLegAngles=[]
        for island,legAngle in zip(points,legAngles):
            valid=True
            for point in island:
                if point.row<0 or point.col<0 or point.row>=maxRow+self.rowEndOffset or point.col>=maxCol+self.colEndOffset:
                    valid=False
                    break
            
            if valid: 
                validPoints.append(island)
                validLegAngles.append(legAngle)
        points=validPoints
        legAngles=validLegAngles



        #remove duplicates
        seenHashes=[]
        validPoints=[]
        validLegAngles=[]
        for island,legAngle in zip(points,legAngles):
            thisHash=hash(",".join([str(point) for point in island]))
            if thisHash not in seenHashes:
                validPoints.append(island)
                validLegAngles.append(legAngle)
                seenHashes.append(thisHash)

        assert len(validPoints)==len(validLegAngles)

        return validPoints, validLegAngles
    
    def incrementYRadius(self):
        for island in self.islands:
            island.radius*=1.01
        self.invalidateCache()
    def decrementYRadius(self):
        for island in self.islands:
            island.radius*=0.99
        self.invalidateCache()


latticeType="bethe"

if latticeType=="normal":
    yLattice=Pattern(math.sqrt(3),2)
    yLattice.addIsland(YIsland(0,0.5,90,0.1))
    yLattice.addIsland(YIsland(0,1.5,90,0.1))
    yLattice.addIsland(YIsland(math.sqrt(3)/2,1,90,0.1))
    yLattice.addIsland(YIsland(math.sqrt(3)/2,2,90,0.1))
elif latticeType=="YOnKag":
    yLattice=Pattern(math.sqrt(3),2)
    yLattice.addIsland(YIsland(0,0,90,0.1))
    yLattice.addIsland(YIsland(0,1,90,0.1))
    yLattice.addIsland(YIsland(math.sqrt(3)/2,0.5,90,0.1))
elif latticeType=="YOnHex":
    yLattice=Pattern(math.sqrt(3),3)
    yLattice.addIsland(YIsland(0,0,90,0.1))
    yLattice.addIsland(YIsland(0,1,90,0.1))
    yLattice.addIsland(YIsland(math.sqrt(3)/2,1.5,90,0.1))
    yLattice.addIsland(YIsland(math.sqrt(3)/2,2.5,90,0.1))
elif latticeType=="hex":
    yLattice=Pattern(math.sqrt(3),3)
    yLattice.addIsland(YIsland(0,0,0,0.1))
    yLattice.addIsland(YIsland(0,1,60,0.1))
    yLattice.addIsland(YIsland(math.sqrt(3)/2,1.5,0,0.1))
    yLattice.addIsland(YIsland(math.sqrt(3)/2,2.5,60,0.1))
elif latticeType=="snowflake":
    r3o2=math.sqrt(3)/2

    yLattice=Pattern((math.sqrt(5)/2+4/8),1)
    yLattice.addIsland(YIsland(1/8,0,30,0.1))
    yLattice.addIsland(YIsland(-1/8,0.5,90,0.1))
    yLattice.addIsland(YIsland(math.sqrt(5)/4+1/8,0,90,0.1))
    yLattice.addIsland(YIsland(math.sqrt(5)/4+3/8,0.5,30,0.1))
    #yLattice.addIsland(YIsland(0,,90,0.1))
    #yLattice.addIsland(YIsland(0,1.5,30,0.1))
elif latticeType=="chiral":
    angle=15
    print(f"chiral angle: {angle} degrees")


    yLattice=Pattern(math.sqrt(3),2)
    yLattice.addIsland(YIsland(0,0.5,90-angle,0.1))
    yLattice.addIsland(YIsland(0,1.5,90-angle,0.1))
    yLattice.addIsland(YIsland(math.sqrt(3)/2,1,90-angle,0.1))
    yLattice.addIsland(YIsland(math.sqrt(3)/2,2,90-angle,0.1))
elif latticeType=="bethe":
    yLattice=Pattern(10,10)
    n=2
    gamma=0
    r3o2=math.sqrt(3)/2


    def addBetheIslands(yLattice,x,y,n,vectorAngle,islandSpacing,radius,gamma):
        if n==0:
            return
        
        if vectorAngle is None:
            angle=-90
            nextAngles=[90,210,330]
        else:
            angle=vectorAngle
            print(vectorAngle)
            nextAngles=[vectorAngle+60,vectorAngle-60]
        yLattice.addIsland(YIsland(y,x,-angle,radius))

        islandSpacing=islandSpacing*((1-gamma))
        for angle in nextAngles:
            addBetheIslands(yLattice,x+islandSpacing*cosDeg(angle),y+islandSpacing*sinDeg(angle),n-1,angle,islandSpacing,radius*(1-gamma),gamma)



    addBetheIslands(yLattice,1,1,n,None,2,0.5,gamma)

    # if N>1:
    #     dist=(1-gamma)+(1-2*gamma)
    #     yLattice.addIsland(YIsland(1/2*dist,-r3o2*dist,90,1-gamma))
    #     yLattice.addIsland(YIsland(0,dist,90,1-gamma))
    #     yLattice.addIsland(YIsland(-1/2*dist,-r3o2*dist,90,1-gamma))






BWImage=getBWImage(phase_image)

imageShown="phase"



def show():
    image=[]
    if imageShown=="phase":
        image=phase_image.copy()
    elif imageShown=="height":
        image=height_image.copy()
    elif imageShown=="bw":
        image=cv2.cvtColor(BWImage.copy(),cv2.COLOR_GRAY2RGB)

    n.draw(image,showGrid=False)

    
    if not n.dragging:
        points,_=yLattice.getSamplePoints(n.rows-1,n.cols-1)
        for island in points:
            colorPattern=[]
            for point in island:
                coord=n.getXY(point.row,point.col)
                bwColor=BWImage[coord[1]][coord[0]]
                if bwColor==0: 
                    color=(255,0,0)
                    colorPattern.append(-1)
                elif bwColor==255: 
                    color=(0,0,255)
                    colorPattern.append(1)
                else:
                    color=(0,255,0)
                    colorPattern.append(0)
                cv2.circle(image,coord,2,color,-1)
            
            if YIsland.hasError(colorPattern):
                cv2.circle(image,n.getXY(island[0].row,island[0].col),5,(0,255,0),3)

    cv2.imshow("window",image)


def cycleArea(x,y):
    type=BWImage[y][x]
    blankSquare=np.zeros((4,4))
    if type==255:
        blankSquare[::]=0
    elif type==0:
        blankSquare[::]=127
    elif(type==127):
        blankSquare[::]=255

    BWImage[(y-2):(y+2),(x-2):(x+2)]=blankSquare

def countTotalErrors():
    total=0
    points,_=yLattice.getSamplePoints(n.rows-1,n.cols-1)
    for island in points:
        colorPattern=[]
        for point in island:
            coord=n.getXY(point.row,point.col)
            bwColor=BWImage[coord[1]][coord[0]]
            if bwColor==0: 
                colorPattern.append(-1)
            elif bwColor==255:
                colorPattern.append(1)
            else:
                colorPattern.append(0)
        
        if YIsland.hasError(colorPattern):
            total+=1
    return total

def jiggle(x,y):
    fixedPoint=n.getNearestFixedPoint(x,y)

    errorsBefore=countTotalErrors()

    node=fixedPoint["node"]
    originalNode=node.copy()

    radius=5

    node.x+=random()*2*radius-radius
    node.y+=random()*2*radius-radius
    n.invalidateCache()



    if(errorsBefore<countTotalErrors()):
        fixedPoint["node"]=originalNode

    n.invalidateCache()

def dataAsString():
    string="row,col,leg 1 angle,leg 1 color,leg 2 color,leg 3 color,center color\n"
    points,legAngles=yLattice.getSamplePoints(n.rows-1,n.cols-1)
    for island,legAngle in zip(points,legAngles):
        colorPattern=[]
        for point in island:
            coord=n.getXY(point.row,point.col)
            bwColor=BWImage[coord[1]][coord[0]]
            if bwColor==0: 
                colorPattern.append(-1)
            elif bwColor==255:
                colorPattern.append(1)
            else:
                colorPattern.append(0)
        colorCode=colorPattern
        string+=f"{island[0].row},{island[0].col},{legAngle},{colorCode[1]},{colorCode[2]},{colorCode[3]},{colorCode[0]}\n"

    return string



def mouse_event(event, x, y,flags, param):
    global lastMouse
    if event == cv2.EVENT_RBUTTONDOWN:
        n.splitAtClosestPoint(x,y)
    elif event ==cv2.EVENT_LBUTTONDOWN:
        n.selectNearestFixedPoint(x,y)
        n.dragging=True
    elif event==cv2.EVENT_MOUSEMOVE:
        n.updateDragging(x,y)
    elif event==cv2.EVENT_LBUTTONUP:
        n.stopDragging()
    elif event == cv2.EVENT_RBUTTONDOWN:
        pass

    lastMouse=(x,y)

    show()



n=NodeNetwork(Node(10,10),Node(600,10),Node(10,600),Node(600,600),15,15)



    


show()
cv2.setMouseCallback('window', mouse_event)

while(True):
    show()

    key=cv2.waitKey(0)
    if(key==ord("\r")):
        break;
    elif(key==ord("r")):
        n.addRow()
    elif(key==ord("e")):
        n.removeRow()
    elif(key==ord("c")):
        n.addCol()
    elif(key==ord("x")):
        n.removeCol()
    elif(key==ord("q")):
        if imageShown=="phase":imageShown="height"
        elif imageShown=="height":imageShown="bw"
        elif imageShown=="bw":imageShown="phase"
    elif(key==ord("+")):
        yLattice.incrementYRadius()
    elif(key==ord("-")):
        yLattice.decrementYRadius()
    elif(key==ord("g")):
        yLattice.rowOffset-=0.01
        yLattice.invalidateCache()
    elif(key==ord("h")):
        yLattice.colOffset-=0.01
        yLattice.invalidateCache()
    elif(key==ord("a")):
        cycleArea(*lastMouse)
    elif(key==ord("j")):
        start=time.time()
        while(time.time()-start<0.25):
            jiggle(*lastMouse)
        print(countTotalErrors())
    elif(key==ord("b")):
        yLattice.colEndOffset-=0.25
        yLattice.invalidateCache()
    elif(key==ord("n")):
        yLattice.colEndOffset+=.25
        yLattice.invalidateCache()
    elif(key==ord("k")):
        yLattice.rowEndOffset-=0.25
        yLattice.invalidateCache()
    elif(key==ord("l")):
        yLattice.rowEndOffset+=0.25
        yLattice.invalidateCache()
    
    



outputname=args.image[0].split("/")[-1].split(".")[0]
print(outputname)

with open(outputname+".csv", 'w') as file:
    file.write(dataAsString())

outputImage=np.zeros((1000,1000,3), np.uint8)
outputImage[:,:]=(127,127,127)

cv2.imwrite("output.jpg", np.float32(outputImage));

cv2.destroyAllWindows()


