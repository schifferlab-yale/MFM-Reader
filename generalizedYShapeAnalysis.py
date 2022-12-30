import csv
import cv2
import numpy as np
import math

#constants
WHITE=(255,255,255)
BLACK=(0,0,0)
GREEN=(0,255,0)
BLUE=(255,0,0)
RED=(0,0,255)
GREY=(127,127,127)
ORANGE=(0,165,255)
PURPLE=(130,0,75)


def degToRad(ang):
    return ang*np.pi/180
def radToDeg(ang):
    return ang/np.pi*180
def cosDeg(ang):
    return np.cos(degToRad(ang))
def sinDeg(ang):
    return np.sin(degToRad(ang))
def map(num,inMin,inMax,outMin,outMax):
    return (num-inMin)/(inMax-inMin)*(outMax-outMin)+outMin

#restricts a number to be in between [0,2pi)
def restrictAngleRad(angle):
    while angle<0:
        angle+=2*math.pi;
    while angle>=2*math.pi:
        angle-=2*math.pi
    return angle

#restricts a number to be in between [0,360)
def restrictAngleDeg(angle):
    if angle is None: return None

    while angle<0:
        angle+=360;
    while angle>=360:
        angle-=360
    return angle

def angleDotProductRad(angle1,angle2):
    return math.cos(angle1-angle2)

#https://stackoverflow.com/questions/57400584/how-to-map-a-range-of-numbers-to-rgb-in-python
def num_to_rgb(val, max_val=1):
    i = (val * 255 / max_val);
    r = round(math.sin(0.024 * i + 0) * 127 + 128);
    g = round(math.sin(0.024 * i + 2) * 127 + 128);
    b = round(math.sin(0.024 * i + 4) * 127 + 128);
    return (r,g,b)


class Moment:
    def __init__(self,row,col,angle,mag):
        self.row=row
        self.col=col
        self.angle=angle
        self.mag=mag

class Charge:
    def __init__(self,row,col,charge):
        self.row=row
        self.col=col
        self.charge=charge

class ChargeGrid:
    def __init__(self):
        self.charges=[]
        self.distError=0.00000001
    def addCharge(self,charge):
        self.charges.append(charge)

    def rowRange(self):
        rowValues=[i.row for i in self.charges]
        return min(rowValues), max(rowValues)

    def colRange(self):
        colValues=[i.col for i in self.charges]
        return min(colValues),max(colValues)
    
    def draw(self,image):
        minRow,maxRow=self.rowRange()
        minCol,maxCol=self.colRange()

        padding=30
        minX=padding
        minY=padding
        maxX=len(image[0])-padding
        maxY=len(image)-padding

        for charge in self.charges:
            x=int(np.interp(charge.col,[minCol,maxCol],[minX,maxX]))
            y=int(np.interp(charge.row,[minRow,maxRow],[minY,maxY]))

            if charge.charge==-1:
                    color=(255,0,0)
            elif charge.charge==1:
                color=(0,255,0)

            cv2.circle(image,(x,y),3,color,-1)


    #given an row,col, all charges are sorted by their distance from that point 
    #output format: [(distance1, charge1), (distance2, charge2), (distance3, charge3)...]
    def chargesByDistance(self,row,col):
        out=[]
        for charge in self.charges:
            dist=np.sqrt((charge.row-row)**2+(charge.col-col)**2)
            out.append((dist,charge))

        out=sorted(out,key=lambda el:el[0])
        return out

    #given a row,col all charges are sorted by their distance. Charges with the same distance are grouped together
    #output format: [(distance1, [chargeA, chargeB, chargeC...]), (distance2, [chargeE, chargeF]), ... ]
    def getGroupedChargesByDistance(self,row,col):
        error=self.distError#for floating point error in distances

        chargesByDist=self.chargesByDistance(row,col)
        groupedCharges=[]
        lastDist=-100
        for dist,charge in chargesByDist:
            if abs(dist-lastDist)<error:
                groupedCharges[-1][1].append(charge)
            else:
                groupedCharges.append((dist,[charge]))
                lastDist=dist

        return groupedCharges

    #given a charge get the correlation as a function of distance
    #output format: [(dist1, correlation1), (dist2, correlation2)]
    def getChargeCorrelation(self,charge):
        groupedCharges=self.getGroupedChargesByDistance(charge.row,charge.col)
        correlations=[]
        for dist,charges in groupedCharges:
            sum=0
            for otherCharge in charges:
                sum+=otherCharge.charge*charge.charge
            avg=sum/len(charges)
            correlations.append((dist,avg))
        
        return correlations
    
    #find correlation between all charges
    #output format [(dist1, correlation1), (dist2,correlation2), ...] #note there might be duplicate distances
    def getAllCorrelationPairs(self,maxDist=100000,shouldCompare=lambda charge1, charge2: True ):
        pairs=[]
        for charge in self.charges:
            for otherCharge in self.charges:
                if shouldCompare(charge,otherCharge):
                    dist=math.sqrt((charge.row-otherCharge.row)**2+(charge.col-otherCharge.col)**2)
                    if dist<=maxDist+self.distError:
                        correlation=charge.charge*otherCharge.charge
                        pairs.append((dist,correlation))
        return pairs
    
    #convert the results from getAllCorrelationPairs so that there are no duplicates
    #output format [(dist1, [correlation1, correlation2, correlation3 ...]), (dist2,[correlation1, correlation2, correlation3...]), ...]
    def getOverallChargeCorrelation(self,maxDist=1000000,shouldCompare=lambda charge1, charge2: True ):
        correlations=self.getAllCorrelationPairs(maxDist=maxDist,shouldCompare=shouldCompare)
        correlations=sorted(correlations,key=lambda el:el[0])

        error=self.distError
        groupedCorrelations=[]
        lastDist=-100
        for dist,correlation in correlations:
            if abs(dist-lastDist)<error:
                groupedCorrelations[-1][1].append(correlation)
            else:
                groupedCorrelations.append((dist,[correlation]))
                lastDist=dist

        averageCorrelations=[]
        for el in groupedCorrelations:
            averageCorrelations.append((el[0],np.average(el[1])))
        return averageCorrelations


#WARNING: copied from an old file so some of the functions will produce innacurate results (mainly a degrees vs. radians issue)
class MomentGrid:
    def __init__(self):
        self.moments=[]
        self.distError=0.00000001
    
    def addMoment(self,moment):
        self.moments.append(moment)
    
    def draw(self,img,padding=50):
        xS=[moment.col for moment in self.moments]
        yS=[moment.row for moment in self.moments]
        minX=np.min(xS)
        maxX=np.max(xS)
        minY=np.min(yS)
        maxY=np.max(yS)

        height,width,channels=img.shape

        imgMinX=padding
        imgMinY=padding
        imgMaxX=width-padding
        imgMaxY=height-padding

        imgMax=min(imgMaxX,imgMaxY)
        imgMin=max(imgMinY,imgMinX)

        for moment in self.moments:
            imgX=np.interp(moment.col,[minX,maxX], [imgMin,imgMax])
            imgY=np.interp(moment.row,[minY,maxY], [imgMin,imgMax])

            spacing=(imgMax-imgMin)/math.sqrt(len(self.moments))

            cv2.circle(img,(int(imgX),int(imgY)),2,  BLACK,-1)

            arrowLength=spacing/4
            
            print(moment.angle)

            end=(int(imgX+cosDeg(moment.angle)*arrowLength),int(imgY+sinDeg(moment.angle)*arrowLength))
            start=(int(imgX-cosDeg(moment.angle)*arrowLength),int(imgY-sinDeg(moment.angle)*arrowLength))
            cv2.arrowedLine(img,start,end,BLACK,2,tipLength=0.2)
    
    #get all the moments sorted by their distance from (x,y)
    def momentsByDistance(self,x,y):
        out=[]
        for moment in self.moments:
            dist=math.sqrt((moment.x-x)**2+(moment.y-y)**2)
            out.append((dist,moment))

        out=sorted(out,key=lambda el:el[0])
        return out
    
    #group moments by their distance from a given point 
    def getGroupedMomentsByDistance(self,x,y):
        error=self.distError#for floating point error in distances

        momentsByDist=self.momentsByDistance(x,y)
        groupedMoments=[]
        lastDist=-100
        for dist,moment in momentsByDist:
            if abs(dist-lastDist)<error:
                groupedMoments[-1][1].append(moment)
            else:
                groupedMoments.append((dist,[moment]))
                lastDist=dist

        return groupedMoments

    def getNthClosestMoments(self,x,y,n):
        return self.getGroupedMomentsByDistance(x,y)[n][1]

    def getRelativeAngleVsDistance(self,maxNAway):


        angleDiffSum=[0]*maxNAway
        angleDiffCount=[0]*maxNAway

        angleCounts=[]
        for i in range(maxNAway):angleCounts.append({0:0,60:0,120:0,180:0,240:0,300:0})

        for moment in self.moments:
            groups=self.getGroupedMomentsByDistance(moment.x,moment.y)
            for n in range(maxNAway):
                if moment.angle is None:
                    continue

                otherMoments=groups[n][1]
                for otherMoment in otherMoments:
                    if otherMoment.angle is None:
                        continue
                    angle=round(180/math.pi*restrictAngleRad(otherMoment.angle-moment.angle))

                    angleDiffSum[n]+=angle
                    angleDiffCount[n]+=1

                    if angle in angleCounts[n].keys():
                        angleCounts[n][angle]+=1
                    else:
                        raise "Bad angle"
            
        anglePercent=[]
        for counts in angleCounts:
            total=0
            for key in counts.keys():
                total+=counts[key]
            dict={}
            for key in counts.keys():
                dict[key]=counts[key]/total
            anglePercent.append(dict)

        return anglePercent


    def getCorrelationByOffsetAngle(self):

        #format: data[centerMomentAngle][angleToOtherIsland]=correlation

        dataSum={}#sum of the corrolations for a given center moment angle and and offset angle
        dataCount={}#counts the total number of data points (for averaging)

        possibleCenterAngles=[30,90,150,210,270,330]#possible angles an island can be at
        possibleOffsetAngles=[0,60,120,180,240,300]#possible differences between island angles


        #populate empty dicts for all center and offset compbinations
        for i in possibleCenterAngles:
            dataSum[i]={}
            dataCount[i]={}
            for j in possibleOffsetAngles:
                dataSum[i][j]=0
                dataCount[i][j]=0
        
        for moment in self.moments:#loop through all islands in sample
            if moment.angle is None:#skip bad islands
                continue

            nearestNeighbors=self.getGroupedMomentsByDistance(moment.x,moment.y)[1]#returns an array islands at a distance of 1 away from center island
            #we take the first element because we are taking the group of closest islands

            assert nearestNeighbors[0]-1<0.0000001#confirm that the islands are 1 unit away

            centerAngle=round(restrictAngleRad(moment.angle)/math.pi*180)#make sure angle is between [0,2pi) and convert to degrees

            assert centerAngle in possibleCenterAngles

            for neighbor in nearestNeighbors[1]:#take element 1 from nearest neighbors (this is the array of neighbors)
                directionVector=(neighbor.x-moment.x,neighbor.y-moment.y)#vector pointing from the center island to the neighbor
                offsetAngle=round(restrictAngleRad(math.atan2(directionVector[1],directionVector[0]))*180/math.pi,4)#angle between the moment of the two islands
                assert offsetAngle in possibleOffsetAngles

                if moment.angle is not None and neighbor.angle is not None:
                    dataSum[centerAngle][offsetAngle]+=math.cos(moment.angle-neighbor.angle)
                    dataCount[centerAngle][offsetAngle]+=1
        

        dataAvg={}
        for key in dataSum.keys():
            dataAvg[key]={}
            for key2 in dataSum[key].keys():


                if dataCount[key][key2]==0:
                    dataAvg[key][key2]=0
                    #prevent divide by 0
                else:
                    dataAvg[key][key2]=dataSum[key][key2]/dataCount[key][key2]
        return dataAvg


                
    def getCorrelationVsDistance(self,maxNAway):
        correlationCount=[0]*maxNAway
        correlationSum=[0]*maxNAway

        for moment in self.moments:
            if moment.angle is None:
                continue

            groups=self.getGroupedMomentsByDistance(moment.x,moment.y)

            for n in range(maxNAway):
                otherMoments=groups[n][1]
                for otherMoment in otherMoments:

                    if otherMoment.angle is None:
                        continue
                    
                    dotProduct=angleDotProductRad(otherMoment.angle,moment.angle)

                    correlationSum[n]+=dotProduct
                    correlationCount[n]+=1
        
        correlation=[correlationSum[i]/correlationCount[i] for i in range(maxNAway)]
        return correlation

    def getCorrelationVsAbsoluteAngle(self,maxNAway):
        #correlationVsAngle[integer distance][angle]

        correlationSums=[]
        correlationCounts=[]
        for i in range(maxNAway):correlationSums.append({})
        for i in range(maxNAway):correlationCounts.append({})

        for moment in self.moments:
            if moment.angle is None:
                continue

            groups=self.getGroupedMomentsByDistance(moment.x,moment.y)
            for n in range(maxNAway):
                otherMoments=groups[n][1]
                for otherMoment in otherMoments:
                    if otherMoment.angle is None:
                        continue

                    directionVector=(otherMoment.x-moment.x,otherMoment.y-moment.y)
                    relativeAngle=round(restrictAngleRad(math.atan2(directionVector[1],directionVector[0]))*180/math.pi,4)
                    
                    dotProduct=angleDotProductRad(otherMoment.angle,moment.angle)

                    if relativeAngle in correlationCounts[n].keys():
                        correlationCounts[n][relativeAngle]+=1
                        correlationSums[n][relativeAngle]+=dotProduct
                    else:
                        correlationCounts[n][relativeAngle]=1
                        correlationSums[n][relativeAngle]=dotProduct
        

        correlations=[]
        for i in range(len(correlationCounts)):
            correlations.append({})
            for key in correlationCounts[i].keys():
                correlations[i][key]=correlationSums[i][key]/correlationCounts[i][key]
        
        return correlations



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

    def getMomentAngle(self):
        #remember y comes first because it is in row,col format

        #return resum([self.colors[i]*self.getLegAngles()[i] for i in range(3)])/3

        row=sinDeg(self.legAngle)*self.colors[0]+sinDeg(self.legAngle+120)*self.colors[1]+sinDeg(self.legAngle+240)*self.colors[2]
        col=cosDeg(self.legAngle)*self.colors[0]+cosDeg(self.legAngle+120)*self.colors[1]+cosDeg(self.legAngle+240)*self.colors[2]
        return radToDeg(math.atan2(row,col))

        return restrictAngleDeg((self.legAngle*self.colors[0]+(self.legAngle+120)*self.colors[1]+(self.legAngle+240)*self.colors[2])/3)


        """v1=self.color1*np.array([sinDeg(self.angle),cosDeg(self.angle)])
        v2=self.color2*np.array([sinDeg(self.angle+120),cosDeg(self.angle+120)])
        v3=self.color3*np.array([sinDeg(self.angle+240),cosDeg(self.angle+240)])

        total"""

    def getMoment(self):
        return Moment(self.row,self.col,self.getMomentAngle(),1)

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
    
    def draw(self,image,showVector=True):
        minRow,maxRow=self.rowRange()
        minCol,maxCol=self.colRange()

        padding=30
        minX=padding
        minY=padding
        maxX=len(image[0])-padding
        maxY=len(image)-padding

        legRadius=0.2

        overlay=np.zeros_like(image,np.uint8)

        for island in self.islands:
            x=int(np.interp(island.col,[minCol,maxCol],[minX,maxX]))
            y=int(np.interp(island.row,[minRow,maxRow],[minY,maxY]))


            if showVector:
                angle=island.getMomentAngle()
                if angle is not None:
                    
                    color=num_to_rgb(angle,max_val=360)
                    cv2.circle(overlay,(x,y),10,color,-1)


            #cv2.putText(image,str(island.getMomentAngle()),(x,y+15),cv2.FONT_HERSHEY_SIMPLEX,0.3,BLACK)

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

            

        mask=overlay.astype(bool)
        image[mask]=cv2.addWeighted(image,0.5,overlay,1-0.5,0)[mask]

    def getChargeGrid(self):
        cg=ChargeGrid()
        for island in self.islands:
            cg.addCharge(island.getCharge())
        return cg
    

    def getMomentGrid(self):
        m=MomentGrid()
        for island in self.islands:
            m.addMoment(island.getMoment())
        return m



            

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
    lattice=genLattice("../MFM-Reader/Phase00400.csv")
    #cg=lattice.getChargeGrid()
    m=lattice.getMomentGrid()

    #print(cg.getOverallChargeCorrelation())

    blank=np.zeros((800,800,3),np.uint8)
    blank[:]=(127,127,127)

    moments=blank.copy()
    m.draw(moments)
    cv2.imshow("moments",moments)

    latticeIm=blank.copy()
    lattice.draw(latticeIm)
    cv2.imshow("lattice",latticeIm)
    
    #cg.draw(blank)
    
    cv2.waitKey(0)