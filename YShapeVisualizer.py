import csv
import cv2
import numpy as np
import math




def degToRad(ang):
    return ang*np.pi/180
def cosDeg(ang):
    return np.cos(degToRad(ang))
def sinDeg(ang):
    return np.sin(degToRad(ang))
def map(num,inMin,inMax,outMin,outMax):
    return (num-inMin)/(inMax-inMin)*(outMax-outMin)+outMin



class YIsland:
    def __init__(self, row, col, angle, color1, color2, color3, centerColor):
        #assert color1+color2+color3==-centerColor

        self.row=row
        self.col=col
        self.legAngle=angle
        self.colors=[color1,color2,color3]
        self.centerColor=centerColor

    def getLegAngles(self):
        return [self.legAngle, (self.legAngle+120)%360, (self.legAngle+240)%360]
    def getLegColors(self):
        return self.colors
    
    def getCharge(self):
        return Charge(self.row,self.col,self.centerColor)

    def __repr__(self):
        return f"({self.row},{self.col})"


    


class YLattice:
    def __init__(self):
        self.islands=[]

    def addIsland(self,island):
        self.islands.append(island)

    def rowRange(self):
        rowValues=[island.row for island in self.islands]
        return min(rowValues), max(rowValues)

    def colRange(self):
        colValues=[island.col for island in self.islands]
        return min(colValues),max(colValues)
    
    def draw(self,image):
        minRow,maxRow=self.rowRange()
        minCol,maxCol=self.colRange()

        padding=30
        minX=padding
        minY=padding
        maxX=len(image[0])-padding
        maxY=len(image)-padding

        legRadius=0.2

        for island in self.islands:
            x=int(np.interp(island.col,[minCol,maxCol],[minX,maxX]))
            y=int(np.interp(island.row,[minRow,maxRow],[minY,maxY]))

            if island.centerColor==-1:
                    color=(0,0,0)
            elif island.centerColor==1:
                color=(255,255,255)
            cv2.circle(image,(x,y),3,color,-1)

            rowCol=np.array([island.row,island.col])
            for angle,colorCode in zip(island.getLegAngles(), island.getLegColors()):

                #this code is kind of weird because relativeLocation is stored like (y,x)
                relativeLocation=rowCol+legRadius*np.array([sinDeg(angle),cosDeg(angle)])
                x=int(map(relativeLocation[1],minCol,maxCol,minX,maxX))
                y=int(map(relativeLocation[0],minRow,maxRow,minY,maxY))

                if colorCode==-1:
                    color=(0,0,0)
                elif colorCode==1:
                    color=(255,255,255)
                cv2.circle(image,(x,y),3,color,-1)



            

def genLattice(filename):
    lattice=YLattice()

    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        headers=next(reader)
        assert headers==["row","col","leg 1 angle", "leg 1 color", "leg 2 color","leg 3 color","center color"]

        
        for row in reader:
            island=YIsland(float(row[0]),float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5]),float(row[6]))
            lattice.addIsland(island)
    
    return lattice


if __name__=="__main__":
    lattice=genLattice("weirdYShapes/snowflake/Phase00398.csv")


    image=np.zeros((800,800,3),np.uint8)
    image[:]=(127,127,127)
    lattice.draw(image)

    cv2.imshow("window",image)
    cv2.waitKey(0)