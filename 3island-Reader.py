import cv2
import matplotlib.pyplot as plt
import math
import numpy as np
from random import randint
import argparse
from nodeNetwork import *

#Set up argparser to allow for input image
parser = argparse.ArgumentParser(description='MFM image analysis')
parser.add_argument('image', metavar='image', type=str, nargs='+',help='Path of image')
parser.add_argument('-r', "--rows",  help="number of rows", type=int, default=10)
parser.add_argument('-c', "--columns",  help="number of columns", type=int, default=10)
parser.add_argument('-s', "--spacing",  help="how dense the islands are packed small=denser (default=0.25)", type=float, default=0.25)
parser.add_argument("-t", "--trim", help="Set if the offset row is shorter than the non-offset rows",action="store_true", default=False)
parser.add_argument("-a", "--reference_image", help="image of the height(to help line up the sample points)", type=str)
args=parser.parse_args()

WINDOWSIZE=800


#read image and reference image
try:
    image = cv2.imread(args.image[0])
    image=cv2.resize(image,(WINDOWSIZE,WINDOWSIZE))
except:
    raise Exception("File not found")

if args.reference_image is not None:
    try:
        height_image = cv2.imread(args.reference_image)
        height_image = cv2.resize(height_image, (WINDOWSIZE,WINDOWSIZE))
    except:
        raise Exception("File not found")
else:
    height_image=np.zeros((1000,1000,3), np.uint8)



#constants
WHITE=(255,255,255)
BLACK=(0,0,0)
GREEN=(0,255,0)
BLUE=(255,0,0)
RED=(0,0,255)

shiftConstant=args.spacing;
show_ref_image=False

pattern=[[True,True],[True,False]]
rowOffset=0
colOffset=0

def isRowOffset(row):
    return (row%2==0 and rowOffset%2==1) or (row%2==1 and rowOffset%2==0) 

def hasIsland(row,col):
    return pattern[(row+rowOffset)%len(pattern)][(col+colOffset)%len(pattern[0])]





class YShapeNodeNetwork(NodeNetwork):
    def getSamplePointsFromSquare(self,topLeft,topRight,bottomLeft,bottomRight,row=0,col=0):

        if not hasIsland(row,col):
            return []

        
        boxWidth=((topRight[0]-topLeft[0])+(bottomLeft[1]-topLeft[1]))/2
        armRadius=shiftConstant*boxWidth


        center=np.array([topLeft[0]+topRight[0]+bottomLeft[0]+bottomRight[0], topLeft[1]+topRight[1]+bottomLeft[1]+bottomRight[1]])/4


        arm1Angle=math.pi/2
        arm2Angle=math.pi/6*7
        arm3Angle=math.pi/6*11

        
        armLocs=[
            center+armRadius*np.array([np.cos(arm1Angle),np.sin(arm1Angle)]),
            center+armRadius*np.array([np.cos(arm2Angle),np.sin(arm2Angle)]),
            center,
            center+armRadius*np.array([np.cos(arm3Angle),np.sin(arm3Angle)]),
        ]
        samplePoints=[list(i) for i in armLocs]


        if(isRowOffset(row)):
            for point in samplePoints:
                point[0]+=(topRight[0]-topLeft[0])/2

            #odd rows are shorter
            if(args.trim and col+1==self.cols-1):
                return [];

        return samplePoints

    def drawData(self, im):
        if not self.dragging:
            samplePoints=self.samplePoints;

            height, width, channels = im.shape

            for (rowI, row) in enumerate(samplePoints):
                for (vertexI, vertex) in enumerate(row):
                    for (pointI, point) in enumerate(vertex):
                        if(point[2]==1):
                            color=WHITE
                        elif(point[2]==0):
                            color=RED
                        else:
                            color=BLACK
                        if(pointI!=2):
                            im=cv2.line(im,(int(point[0]),int(point[1])),(int(vertex[2][0]),int(vertex[2][1])),color,2)
                        im=cv2.circle(im, (int(point[0]),int(point[1])), 3, color, -1)
    def hasError(self, samplePoints, rowI, vertexI, pointI):
        if(pointI==2):
            sum=0;
            for point in samplePoints[rowI][vertexI]:
                sum+=point[2]
            if(sum==0):
                return False
            else:
                return True
        else:
            return False
    
    def dataAsString(self):
        string="row,col,leg 1 angle,leg 1 color,leg 2 color,leg 3 color,center color\n"
        for (rowI, row) in enumerate(self.samplePoints):
            for (vertexI, vertex) in enumerate(row):
                if(len(vertex)==0):
                    continue
                leg1Angle=90
                colorCode=[vertex[0][2], vertex[1][2], vertex[3][2], vertex[2][2]]
                
                colOffset=isRowOffset(rowI)*0.5

                
                    
                string+=f"{rowI},{vertexI+colOffset},{leg1Angle},{colorCode[0]},{colorCode[1]},{colorCode[2]},{colorCode[3]}\n"

        return string

n=YShapeNodeNetwork(Node(10,10),Node(800,10),Node(30,800),Node(700,700),args.rows+1, args.columns+1,image)
n.pointSampleWidth=3



def show():
    imWidth=1000;
    imHeight=1000;

    if(show_ref_image):
        outputImage=height_image.copy()
    else:
        outputImage=image.copy()
    n.draw(outputImage)
    cv2.imshow("window",outputImage)

    outputImage=np.zeros((imHeight,imWidth,3), np.uint8)
    outputImage[:,:]=(127,127,127)
    n.drawData(outputImage)
    cv2.imshow("output",outputImage)






def mouse_event(event, x, y,flags, param):
    global lastMouse

    if event == cv2.EVENT_RBUTTONDOWN:
        n.splitAtClosestPoint(x,y)
    elif event ==cv2.EVENT_LBUTTONDOWN:
        if(flags==16 or flags==17 or flags==48):
            n.toggleNearestSamplePoint(x,y)
        else:
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

show();
cv2.setMouseCallback('window', mouse_event)

print("Enter: Quit and Save")
print("+/-: Increase/decrease island spacing")
print("r/e: Add/remove row")
print("c/x: Add/remove column")
print("o: toggle row offset")
print("t: toggle row trim")
print("q: toggle reference image")
print("g/h: adjust row/col offset")

lastMouse=(0,0)



while(True):
    key=cv2.waitKey(0)

    if(key==ord("\r")):
        break;
    elif(key==ord("+")):
        if shiftConstant<0.5:
            shiftConstant+=0.01
        n.setSamplePoints()
    elif(key==ord("-")):
        if shiftConstant>0:
            shiftConstant-=0.01
        n.setSamplePoints()
    elif(key==ord("r")):
        n.addRow()
    elif(key==ord("e")):
        n.removeRow()

    elif(key==ord("c")):
        n.addCol()
    elif(key==ord("x")):
        n.removeCol()
    elif(key==ord("t")):
        args.trim=not args.trim
        n.setSamplePoints()
    elif(key==ord("q")):
        show_ref_image=not show_ref_image
    elif(key==ord("j")):
        for i in range(10):
            n.jiggleNearestFixedPoint(*lastMouse)
    elif(key==ord("g")):
        rowOffset+=1
        n.setSamplePoints()
    elif(key==ord("h")):
        colOffset+=1
        n.setSamplePoints()
    show()


outputname=args.image[0].split("/")[-1].split(".")[0]
print(outputname)

with open(outputname+".csv", 'w') as file:
    file.write(n.dataAsString())

outputImage=np.zeros((1000,1000,3), np.uint8)
outputImage[:,:]=(127,127,127)
n.drawData(outputImage)
cv2.imwrite("output.jpg", np.float32(outputImage));

cv2.destroyAllWindows()
