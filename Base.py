import cv2
import numpy as np
import argparse
from nodeNetwork import *

#Set up argparser to allow for input image
parser = argparse.ArgumentParser(description='MFM image analysis')
parser.add_argument('image', metavar='image', type=str, nargs='+',help='Path of image')
args=parser.parse_args()

try:
    image = cv2.imread(args.image[0])
    image = cv2.resize(image, (1000,1000))
except:
    raise Exception("File not found")

#constants
WHITE=(255,255,255)
BLACK=(0,0,0)
GREEN=(0,255,0)
BLUE=(255,0,0)
RED=(0,0,255)

shiftConstant=0.25

class SquareNodeNetwork(NodeNetwork):

    #this will return the four points inside a square
    def getSamplePointsFromSquare(self,topLeft,topRight,bottomLeft,bottomRight,row=0,col=0):
        return []
    
    #this shows when two sides are both black/white which means the data is being read wrong
    def hasError(self, samplePoints, rowI, vertexI, pointI):
        return False

    
    def drawData(self,im):
        super().drawData(im)

n=SquareNodeNetwork(Node(10,10),Node(800,10),Node(30,800),Node(700,700),10,10,image)




def show():
    imWidth=1000;
    imHeight=1000;

    outputImage=image.copy()
    n.draw(outputImage)
    cv2.imshow("window",outputImage)

    outputImage=np.zeros((imHeight,imWidth,3), np.uint8)
    outputImage[:,:]=(127,127,127)
    n.drawData(outputImage)
    cv2.imshow("output",outputImage)





lastMouse=(0,0)
def mouse_event(event, x, y,flags, param):
    if event == cv2.EVENT_RBUTTONDOWN:
        n.splitAtClosestPoint(x,y)
    elif event ==cv2.EVENT_LBUTTONDOWN:
        n.selectNearestFixedPoint(x,y)
        n.dragging=True
    elif event==cv2.EVENT_MOUSEMOVE:
        n.updateDragging(x,y)
    elif event==cv2.EVENT_LBUTTONUP:
        n.dragging=False
        n.setSamplePoints()
    elif event == cv2.EVENT_RBUTTONDOWN:
        pass
    lastMouse=(x,y)
    show()

show();
cv2.setMouseCallback('window', mouse_event)
#TODO add a button to cycle a point (correct errors manually)
while True:
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
    
    show()

with open('output.csv', 'w') as file:
    file.write(n.dataAsString())

outputImage=np.zeros((1000,1000,3), np.uint8)
outputImage[:,:]=(127,127,127)
n.drawData(outputImage)
cv2.imwrite("output.jpg", np.float32(outputImage));

cv2.destroyAllWindows()
