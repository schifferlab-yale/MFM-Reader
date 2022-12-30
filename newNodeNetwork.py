"""
This file contains the class NodeNetwork which is meant to be an abstract class to contain a network of points over an image.
The class is given an image, 4 corners of a quadrangle, and a number of rows and columns, it then creates a grid over the image of sample points.
You must implement the method getSamplePointsFromSquare() in order to get the sample points to show up in the image.
One "square" should generally be a small repeatable unit for the pattern of the sample. (e.g. one island cluster, one island, etc)

Once the grid is created, it can be split at a given row/col in order to create another "fixed point" which can be moved around.
The NodeNetwork will interpolate a grid between every quadrangle of four fixed points, allowing flexibility for a user to account for distortion in an image.
The output of the nodenetwork will generally just be reading the color of each of the sample points.
"""

from functools import cache
import cv2
import numpy as np
import math
from random import random, sample
import time

#constants
WHITE=(255,255,255)
BLACK=(0,0,0)
GREEN=(0,255,0)
BLUE=(255,0,0)
RED=(0,0,255)

#takes in an [x1,y1] and [x2,y2] and returns their distance
def dist(point1, point2):
    return math.sqrt(math.pow(point1[0] - point2[0], 2)+math.pow(point1[1] - point2[1], 2))
#takes in an [x1,y1] and [x2,y2] and returns a point a certain percent between the two
def getIntermediate(point1,point2,percent):
    return [(point2[0]-point1[0])*percent+point1[0], (point2[1]-point1[1])*percent+point1[1]]

def map(num,inMin,inMax,outMin,outMax):
    return (num-inMin)/(inMax-inMin)*(outMax-outMin)+outMin



#Basic class to hold an x and y value
class Node:
    def __init__(self,x,y):
        self.x=x;
        self.y=y;
    def xyAsIntTuple(self):
        return (int(self.x),int(self.y))
    def xyAsArray(self):
        return [self.x,self.y]
    def drawLineTo(self,node,im):
        im=cv2.line(im, self.xyAsIntTuple(), node.xyAsIntTuple(), RED, 2)
    def copy(self):
        return Node(self.x,self.y)
    def __str__(self):
        return "("+str(self.x)+","+str(self.y)+")"

#turns [x,y] into (x,y)
def xyArrayToIntTuple(arr):
    return (int(arr[0]),int(arr[1]))


#main class
class NodeNetwork:
    def __init__(self,topLeft,topRight,bottomLeft,bottomRight,rows, cols):

        #number of rows and columns
        self.rows=rows;
        self.cols=cols;

        #variables to help with point dragging
        self.selectedPoint=None;
        self.dragging=False

        #format {row: rowIndex, col:colIndex, node:Node}
        self.fixedPoints=[
        {"row":0,"col":0,"node":topLeft},
        {"row":0,"col":cols-1,"node":topRight},
        {"row":rows-1,"col":0,"node":bottomLeft},
        {"row":rows-1, "col":cols-1, "node":bottomRight}
            ]

        #defines boundaries
        self.topLeft=self.fixedPoints[0]["node"];
        self.topRight=self.fixedPoints[1]["node"];
        self.bottomLeft=self.fixedPoints[2]["node"];
        self.bottomRight=self.fixedPoints[3]["node"];

        #rows and columns which contain fixed points
        self.fixedRows=[0,rows-1]
        self.fixedCols=[0,cols-1]





    #draws the current grid onto an image
    def draw(self,im,showGrid=True):

        #draw all fixed points
        sortedPoints=self.getSortedFixedPoints()
        for (i,point) in enumerate(self.getSortedFixedPoints()):
            #draw fixed point
            im=cv2.circle(im,point["node"].xyAsIntTuple(), 5,RED,-1)

            #hasGrid represents if the point is the topLeft corner of a subgrid
            hasGrid=True;
            topLeft=point
            topLeftCoord=point["node"].xyAsArray()
            if(i==len(sortedPoints)-1):#bottomLeftCorner
                hasGrid=False
            elif(point["row"]==self.rows-1):#bottomRow
                hasGrid=False
            elif(point["col"]==self.cols-1):#last col
                hasGrid=False
            else:#has a valid grid
                #if it has a valid grid then get the coordinants of the verticies
                topRight=sortedPoints[i+1]
                bottomLeft=sortedPoints[i+len(self.fixedCols)]
                bottomRight=sortedPoints[i+len(self.fixedCols)+1]
                cols=topRight["col"]-topLeft["col"]
                rows=bottomLeft["row"]-topLeft["row"]

                topRightCoord=topRight["node"].xyAsArray()
                bottomLeftCoord=bottomLeft["node"].xyAsArray()
                bottomRightCoord=bottomRight["node"].xyAsArray()

                #draw the outline and grid
                if showGrid or self.dragging:
                    im=cv2.line(im,xyArrayToIntTuple(topLeftCoord),xyArrayToIntTuple(topRightCoord),BLACK,1)
                    im=cv2.line(im,xyArrayToIntTuple(topLeftCoord),xyArrayToIntTuple(bottomLeftCoord),BLACK,1)
                    im=cv2.line(im,xyArrayToIntTuple(bottomLeftCoord),xyArrayToIntTuple(bottomRightCoord),BLACK,1)
                    im=cv2.line(im,xyArrayToIntTuple(topRightCoord),xyArrayToIntTuple(bottomRightCoord),BLACK,1)

                    for (startX,startY,endX,endY) in zip(np.linspace(topLeftCoord[0],topRightCoord[0],cols+1), np.linspace(topLeftCoord[1],topRightCoord[1],cols+1), np.linspace(bottomLeftCoord[0],bottomRightCoord[0],cols+1), np.linspace(bottomLeftCoord[1],bottomRightCoord[1],cols+1)):
                        im=cv2.line(im,(int(startX),int(startY)),(int(endX),int(endY)),RED,1)
                    for (startX,startY,endX,endY) in zip(np.linspace(topLeftCoord[0],bottomLeftCoord[0],rows+1), np.linspace(topLeftCoord[1],bottomLeftCoord[1],rows+1), np.linspace(topRightCoord[0],bottomRightCoord[0],rows+1), np.linspace(topRightCoord[1],bottomRightCoord[1],rows+1)):
                        im=cv2.line(im,(int(startX),int(startY)),(int(endX),int(endY)),RED,1)


    def invalidateCache(self):
        self.getGrid.cache_clear()
        self.getXY.cache_clear()

    @cache
    #generates the grid based on the subgrids
    def getGrid(self):
        #generate an empty grid representing each point
        grid=[]
        for row in range(self.rows):
            grid.append([])
            for col in range(self.cols):
                grid[len(grid)-1].append("")

        #loop through each fixed point and draw the grid that it is the top left of
        sortedPoints=self.getSortedFixedPoints()
        for (i,point) in enumerate(self.getSortedFixedPoints()):

            #make sure that point is the topleft ofo a grid and not an edge
            hasGrid=True;
            topLeft=point
            topLeftCoord=point["node"].xyAsArray()
            if(i==len(sortedPoints)-1):#bottomLeftCorner
                hasGrid=False
            elif(point["row"]==self.rows-1):#bottomRow
                hasGrid=False
            elif(point["col"]==self.cols-1):#last col
                hasGrid=False
            else:#has a valid grid
                #get grid coordinates if valid grid
                topRight=sortedPoints[i+1]
                bottomLeft=sortedPoints[i+len(self.fixedCols)]
                bottomRight=sortedPoints[i+len(self.fixedCols)+1]
                cols=topRight["col"]-topLeft["col"]
                rows=bottomLeft["row"]-topLeft["row"]

                topRightCoord=topRight["node"].xyAsArray()
                bottomLeftCoord=bottomLeft["node"].xyAsArray()
                bottomRightCoord=bottomRight["node"].xyAsArray()

            #get all the points in that subgrid
            if(hasGrid):
                for (rowI, rowStartX,rowStartY,rowEndX,rowEndY) in  zip(range(0,rows+1), np.linspace(topLeftCoord[0],bottomLeftCoord[0],rows+1), np.linspace(topLeftCoord[1],bottomLeftCoord[1],rows+1), np.linspace(topRightCoord[0],bottomRightCoord[0],rows+1), np.linspace(topRightCoord[1],bottomRightCoord[1],rows+1)):
                    for(colI, pointX, pointY) in zip(range(0,cols+1), np.linspace(rowStartX,rowEndX,cols+1), np.linspace(rowStartY,rowEndY,cols+1)):
                        grid[point["row"]+rowI][point["col"]+colI]=[pointX,pointY]
        return grid

    @cache
    def getXY(self,row,col):
        grid=self.getGrid()

        topLeftPoint=np.array(grid[math.floor(row)][math.floor(col)])
        topRightPoint=np.array(grid[math.floor(row)][math.ceil(col)])
        bottomLeftPoint=np.array(grid[math.ceil(row)][math.floor(col)])
        bottomRightPoint=np.array(grid[math.ceil(row)][math.ceil(col)])
        
        iHatPrime=(topRightPoint-topLeftPoint)/2+(bottomRightPoint-bottomLeftPoint)/2
        jHatPrime=(bottomLeftPoint-topLeftPoint)/2+(bottomRightPoint-topRightPoint)/2




        matrix=np.vstack([iHatPrime,jHatPrime]).transpose()

        
        offsetVector=np.array([[col%1],[row%1]])


        out=topLeftPoint.reshape(-1,1)+np.matmul(matrix,offsetVector)


        return (math.floor(out[0][0]),math.floor(out[1][0]))

        

    #gets the nearest point on the grid to (x,y)
    def getNearestPoint(self,x,y):
        nearestPointRow=-1
        nearestPointCol=-1
        nearestPointDist=100000000000
        nearestPoint=[];
        for (rowI,row) in enumerate(self.getGrid()):
            for (colI, point) in enumerate(row):
                distance=dist([x,y],point)
                if(distance<nearestPointDist):
                    nearestPointDist=distance
                    nearestPointRow=rowI
                    nearestPointCol=colI
                    nearestPoint=point
        return {"row":nearestPointRow, "col":nearestPointCol,"point":nearestPoint}


    #gets the nearest fix point to (x,y)
    def getNearestFixedPoint(self,x,y):
        nearestPoint=self.fixedPoints[0];
        nearestPointDist=100000000000
        for point in self.fixedPoints:
            distance=dist([x,y],point["node"].xyAsArray())
            if(distance<nearestPointDist):
                nearestPointDist=distance
                nearestPoint=point
        return nearestPoint
  

    def selectNearestFixedPoint(self,x,y):
        self.selectedPoint=self.getNearestFixedPoint(x,y)

    #splits gridi into four at the closest ponit
    def splitAtClosestPoint(self,x,y):
        a=self.getNearestPoint(x,y)
        self.addFixedPointRecursive(Node(a["point"][0], a["point"][1]), a["row"], a["col"])

    #get the position of a point at given row and column
    def getPointPosition(self,row,col):
        return self.getGrid()[row][col]

    #adds a fixed point to a row and col
    #BE CAREFUL IT WILL NOT CHECK IF OTHER POINTS NEED TO BE ADDED TO MAKE EVERYTHING SQUARE
    def addFixedPointNotRecursive(self,node,row,col):
        for fixedPoint in self.fixedPoints:
            if(fixedPoint["row"]==row and fixedPoint["col"]==col):
                return;


        if row not in self.fixedRows:
            self.fixedRows.append(row)
        if col not in self.fixedCols:
            self.fixedCols.append(col)
        self.fixedPoints.append({"row":row, "col":col, "node":node})

    #safe to use function to make a given row and col location a fixed point
    #(not actually recursive, it is just called that from when it used to be)
    def addFixedPointRecursive(self,node,row,col):

        toAdd=[(node,row,col)]


        for rowIndex in self.fixedRows:
            xy=self.getPointPosition(rowIndex,col)
            node=Node(xy[0],xy[1])
            toAdd.append((node,rowIndex,col))
        for colIndex in  self.fixedCols:
            xy=self.getPointPosition(row,colIndex)
            node=Node(xy[0],xy[1])
            toAdd.append((node,row,colIndex))

        #we have to add them all at the end like this so that the getPointPosition function doesn't get messed up by an invalid grid
        for i in toAdd:
            self.addFixedPointNotRecursive(*i)

    #get fixed points sorted left-to-right, top-to-bottom
    def getSortedFixedPoints(self):
        def eval(node):
            return node["row"]*2*self.cols+node["col"]
        self.fixedPoints.sort(key=eval)
        return self.fixedPoints

    #drag to x,y
    def updateDragging(self,x,y):
        if(self.dragging):
            self.selectedPoint["node"].x=x;
            self.selectedPoint["node"].y=y;

    #stop dragging and update the sample points
    def stopDragging(self):
        if(self.dragging):
            self.dragging=False;
            self.invalidateCache()



    #add row to end of lattice
    def addRow(self):
        self.invalidateCache()
        self.rows+=1;
        #make the last row fixed
        self.fixedRows.append(self.rows-1)

        #move all teh fixed points on the last row to the new last row
        for point in self.fixedPoints:
            if(point["row"]==self.rows-2):
                point["row"]+=1
        #the second to last row is no longer fixed
        self.fixedRows.remove(self.rows-2)


    #add col to end of lattice
    def addCol(self):
        self.invalidateCache()
        self.cols+=1
        self.fixedCols.append(self.cols-1)
        for point in self.fixedPoints:
            if(point["col"]==self.cols-2):
                point["col"]+=1;

        self.fixedCols.remove(self.cols-2)


    #remove last row
    def removeRow(self):
        self.invalidateCache()
        if self.rows<=2:
            return

        #Save the positions of the fixed points in the row to be removed
        savedPoints=[point for point in self.getSortedFixedPoints() if point["row"]==self.rows-1]

        self.rows-=1
        self.fixedRows.remove(self.rows)
        self.fixedRows.append(self.rows-1)

        #remove fixed points in removed row
        self.fixedPoints=[point for point in self.fixedPoints if point["row"]<self.rows]
        self.fixedCols.sort()
        for (point,col) in zip(savedPoints, self.fixedCols):
            self.addFixedPointNotRecursive(point["node"],self.rows-1,col)



    #removes the last column from the lattice
    def removeCol(self):
        self.invalidateCache()
        #must have at least two columns
        if self.cols<=2:
            return;

        #save the fixed points in the last column because we have to move them up one
        savedPoints=[point for point in self.getSortedFixedPoints() if point["col"]==self.cols-1]

        #remove column
        self.cols-=1
        self.fixedCols.remove(self.cols)

        #fix the last column
        if self.cols-1 not in self.fixedCols:
            self.fixedCols.append(self.cols-1)

        #add back in the fixed points
        self.fixedPoints=[point for point in self.fixedPoints if point["col"]<self.cols]
        self.fixedRows.sort()
        for (point,row) in zip(savedPoints, self.fixedRows):
            self.addFixedPointNotRecursive(point["node"],row,self.cols-1)

