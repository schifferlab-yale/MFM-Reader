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
parser.add_argument("-o", "--offset",  help="Set if the first row is shifted to the right, don't set if the second row is shifted to the right",action='store_true', default=False)
parser.add_argument("-t", "--trim", help="Set if the offset row is shorter than the non-offset rows",action="store_true", default=False)
parser.add_argument("-a", "--reference_image", help="image of the height(to help line up the sample points)", type=str)
args=parser.parse_args()

WINDOWSIZE=1000


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
class TriangleNodeNetwork(NodeNetwork):
    def getSamplePointsFromSquare(self,topLeft,topRight,bottomLeft,bottomRight,row=0,col=0):
    
        #get center of sides of square
        centerTop=[topLeft[0]+(topRight[0]-topLeft[0])/2, topLeft[1]+(topRight[1]-topLeft[1])/2]
        centerLeft=[topLeft[0]+(bottomLeft[0]-topLeft[0])/2, topLeft[1]+(bottomLeft[1]-topLeft[1])/2]
        centerRight=[topRight[0]+(bottomRight[0]-topRight[0])/2, topRight[1]+(bottomRight[1]-topRight[1])/2]
        centerBottom=[bottomLeft[0]+(bottomRight[0]-bottomLeft[0])/2, bottomLeft[1]+(bottomRight[1]-bottomLeft[1])/2]

        center=np.array([(topLeft[0]+topRight[0]+bottomLeft[0]+bottomRight[0])/4, (topLeft[1]+topRight[1]+bottomLeft[1]+bottomRight[1])/4])
        radius=(topRight[0]-topLeft[0])*shiftConstant

        offset1=radius*np.array([math.cos(4*math.pi/3),math.sin(4*math.pi/3)])
        offset2=radius*np.array([1,0])
        offset3=radius*np.array([math.cos(2*math.pi/3),math.sin(2*math.pi/3)])

        point1=(center+offset1).tolist()
        point2=(center+offset2).tolist()
        point3=(center+offset3).tolist()



        points=[point1,point2,point3]

        if((row%2==0 and args.offset==True) or (row%2==1 and args.offset==False) ):
            width=(centerRight[0]-centerLeft[0])
            for point in points:
                point[0]+=width/2

            #odd rows are shorter
            if(args.trim and col+1==self.cols-1):
                return [];



        return points
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
    def hasError(self, samplePoints, rowI, vertexI, pointI):

        top=samplePoints[rowI][vertexI][0][2]
        middle=samplePoints[rowI][vertexI][1][2]
        bottom=samplePoints[rowI][vertexI][2][2]


        if (top==bottom and top!=middle):
            return True
        return False
    
    def dataAsString(self):
        string=""
        for (rowI, row) in enumerate(self.samplePoints):
            for (vertexI, vertex) in enumerate(row):
                for (pointI, point) in enumerate(vertex):
                    value=point[2]
                    if pointI==1:#middle point is reversed
                        value*=-1
                    string+=str(value)+", "
                string+="\t"
            string+="\n"
        return string

n=TriangleNodeNetwork(Node(10,10),Node(800,10),Node(30,800),Node(700,700),args.rows+1, args.columns+1,image,pointSampleRadius=-1,colorBias=0)


xOff=0
yOff=0
def show():
    imWidth=1000;
    imHeight=1000;



    if(show_ref_image):
        refShifted=height_image.copy().astype(np.uint8)

        if(xOff)>0:
            border=np.zeros((refShifted.shape[0],xOff,3),dtype=np.uint8)
            refShifted=np.concatenate((border,refShifted),axis=1)
        elif(xOff)<0:
            refShifted=refShifted[:, -xOff:]

        if yOff>0:
            border=np.zeros((yOff,refShifted.shape[1],3),dtype=np.uint8)
            refShifted=np.concatenate((border,refShifted),axis=0)
        elif yOff<0:
            refShifted=refShifted[-yOff:, :]

        outputImage=refShifted
    else:
        outputImage=image.copy()
    n.draw(outputImage,showGrid=False,samplePointSize=1)
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

lastMouse=(0,0)


LEFT_ARROW=81
RIGHT_ARROW=83
DOWN_ARROW=84
UP_ARROW=82


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
    elif(key==ord("o")):
        args.offset=not args.offset
        n.setSamplePoints()
    elif(key==ord("t")):
        args.trim=not args.trim
        n.setSamplePoints()
    elif(key==ord("q")):
        show_ref_image=not show_ref_image
    elif(key==ord("j")):
        for i in range(10):
            n.jiggleNearestFixedPoint(*lastMouse)
    elif(key==UP_ARROW):
        yOff-=1
    elif(key==DOWN_ARROW):
        yOff+=1
    elif(key==RIGHT_ARROW):
        xOff+=1
    elif(key==LEFT_ARROW):
        xOff-=1
    else:
        print(f"Uknown key:{key}")
    show()

with open('output.csv', 'w') as file:
    if(args.offset==True):
        file.write("first row offset\n")
    else:
        file.write("second row offset\n")
    file.write("top, middle, bottom\n")
    file.write(n.dataAsString())

outputImage=np.zeros((1000,1000,3), np.uint8)
outputImage[:,:]=(127,127,127)
n.drawData(outputImage)
cv2.imwrite("output.jpg", np.float32(outputImage));

cv2.destroyAllWindows()
