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
    raise FileNotFoundError("File not found")


shiftConstant=0.25

class SquareNodeNetwork(NodeNetwork):
    #this will return the four points inside a square
    def getSamplePointsFromSquare(self,topLeft,topRight,bottomLeft,bottomRight,row=0,col=0):
        
        shiftConstant=0.25#How far away the sample points are from the edqe of the square 0=right on the edge, 1=on the opposite edge

        #get center of sides of square
        centerTop=[topLeft[0]+(topRight[0]-topLeft[0])/2, topLeft[1]+(topRight[1]-topLeft[1])/2]
        centerLeft=[topLeft[0]+(bottomLeft[0]-topLeft[0])/2, topLeft[1]+(bottomLeft[1]-topLeft[1])/2]
        centerRight=[topRight[0]+(bottomRight[0]-topRight[0])/2, topRight[1]+(bottomRight[1]-topRight[1])/2]
        centerBottom=[bottomLeft[0]+(bottomRight[0]-bottomLeft[0])/2, bottomLeft[1]+(bottomRight[1]-bottomLeft[1])/2]

        #square width and height
        width=(centerRight[0]-centerLeft[0])
        height=(centerBottom[1]-centerTop[1])

        #sample points are stored as [x,y]
        topSamplePoint=[centerTop[0],centerTop[1]+height*shiftConstant]
        leftSamplePoint=[centerLeft[0]+width*shiftConstant,centerLeft[1]]
        rightSamplePoint=[centerRight[0]-width*shiftConstant,centerRight[1]]
        bottomSamplePoint=[centerBottom[0], centerBottom[1]-height*shiftConstant]

        #return the four sample points in this square
        fourSamplePoints=[topSamplePoint,leftSamplePoint,rightSamplePoint,bottomSamplePoint]
        return fourSamplePoints
    
    #this shows when two sides are both black/white which means the data is being read wrong
    def hasError(self, samplePoints, rowI, vertexI, pointI):

        #only look at the right and bottom sample points
        if pointI==0 or pointI==1:
            return False

        #get the current row and grid cell
        row = samplePoints[rowI]
        vertex=row[vertexI]

        if pointI==2:#if we are on the right side of the cell

            #if this is not the last cell in the row, check that the cell to the right has the opposite color
            if vertexI < len(row)-1:
                
                #if the colors are the same, this is the error
                if(vertex[2][2] == row[vertexI+1][1][2]):
                    return True

        #same process as above but for the bottom point
        if pointI==3:
            if rowI < len(samplePoints)-1:
                if(vertex[3][2] == samplePoints[rowI+1][vertexI][0][2]):
                    return True
        
        #false by default
        return False

    
#This specifies the four corners of the grid, the # of rows and columns, and the MFM image it is reading.
n=SquareNodeNetwork(Node(10,10),Node(800,10),Node(30,800),Node(700,700),10,10,image)

def show():
    imWidth=1000;
    imHeight=1000;

    outputImage=image.copy()
    n.draw(outputImage)#draw the grid over the image
    cv2.imshow("window",outputImage)



def mouse_event(event, x, y,flags, param):

    #add a reference point on right click
    if event == cv2.EVENT_RBUTTONDOWN:
        n.splitAtClosestPoint(x,y)
    
    #select a point for dragging on left click
    elif event ==cv2.EVENT_LBUTTONDOWN:
        n.selectNearestFixedPoint(x,y)
        n.dragging=True
    
    #update dragging
    elif event==cv2.EVENT_MOUSEMOVE:
        n.updateDragging(x,y)

    #stop dragging on mouse up
    elif event==cv2.EVENT_LBUTTONUP:
        n.dragging=False
        n.setSamplePoints()

    show()

show();
cv2.setMouseCallback('window', mouse_event)


while True:
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
    
    show()

with open('output.csv', 'w') as file:
    file.write(n.dataAsString())

outputImage=np.zeros((1000,1000,3), np.uint8)
outputImage[:,:]=(127,127,127)
n.drawData(outputImage)
cv2.imwrite("output.jpg", np.float32(outputImage));

cv2.destroyAllWindows()
