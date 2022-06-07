import cv2, numpy as np
import argparse


parser = argparse.ArgumentParser(description='Image Aligner')
parser.add_argument('main_image', metavar='image', type=str, nargs='+',help='Path of image')
parser.add_argument('aligned_image', metavar='toAlign', type=str, nargs="+", help="Path of image")

args=parser.parse_args()

key=-1
xOffset=0
yOffset=-1
im1=cv2.imread(args.main_image[0],0).astype(np.float64)
im2=cv2.imread(args.aligned_image[0],0).astype(np.float64)
black_thresh=100
white_thresh=150
imageShown="contrast"



blank1=np.zeros( (max(im1.shape[0],im2.shape[0]) ,max(im1.shape[1],im2.shape[1])) )
blank2=blank1.copy()
blank1[0:im1.shape[0],0:im1.shape[1]]=im1
blank2[0:im2.shape[0],0:im2.shape[1]]=im2

im1,im2=blank1,blank2

while(key!=13):
    
    im2Shifted=im2.copy()
    im1Shifted=im1.copy()

    if(xOffset)>0:
        border=np.zeros((im2Shifted.shape[0],xOffset), dtype=np.float64)

        im2Shifted=np.concatenate((border,im2Shifted),axis=1)
        im1Shifted=np.concatenate((im1Shifted,border),axis=1)
    elif(xOffset)<0:
        border=np.zeros((im2Shifted.shape[0],-xOffset), dtype=np.float64)

        im2Shifted=np.concatenate((im2Shifted,border),axis=1)
        im1Shifted=np.concatenate((border,im1Shifted),axis=1)


    if yOffset>0:
        border=np.zeros((yOffset,im2Shifted.shape[1]), dtype=np.float64)

        im2Shifted=np.concatenate((border,im2Shifted),axis=0)
        im1Shifted=np.concatenate((im1Shifted,border),axis=0)
    elif yOffset<0:
        border=np.zeros((-yOffset,im2Shifted.shape[1]), dtype=np.float64)

        im2Shifted=np.concatenate((im2Shifted,border),axis=0)
        im1Shifted=np.concatenate((border,im1Shifted),axis=0)


    contrast=np.subtract(im2Shifted,im1Shifted)
    contrastMean=np.mean(contrast)
    contrastStd=np.std(contrast)
    print(contrastMean,contrastStd)
    contrast=np.interp(contrast,(contrast.min(),contrast.max()),(0,255))
    contrast=contrast.astype(np.float32)

    # //contrast=cv2.GaussianBlur(contrast,(3,3),0)
    #contrast = cv2.adaptiveThreshold(contrast,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,127,0)

    #_,contrast=cv2.threshold(contrast,100,255,cv2.THRESH_TOZERO)
    #_,contrast=cv2.threshold(contrast,200,255,cv2.THRESH_TOZERO_INV)
    contrast[contrast<black_thresh]=0
    contrast[contrast>white_thresh]=255
    print(f"black: {black_thresh} white: {white_thresh} key: {key}")
    

    contrast=contrast.astype(np.uint8)
    im1Shifted=im1Shifted.astype(np.uint8)
    im2Shifted=im2Shifted.astype(np.uint8)

    #print(xOffset,yOffset)


    show=None
    if imageShown=="contrast": show=contrast
    elif imageShown=="im1": show=im1Shifted
    elif imageShown=="im2": show=im2Shifted

    cv2.imshow("window",show)
    key=cv2.waitKey(0)

    if(key==83):
        xOffset+=1
    elif(key==81):
        xOffset-=1
    elif(key==82):
        yOffset-=1
    elif(key==84):
        yOffset+=1
    elif(key==39):
        imageShown="im1"
    elif(key==44):
        imageShown="im2"
    elif(key==46):
        imageShown="contrast"
    elif(key==99):
        black_thresh+=1
    elif(key==116):
        black_thresh-=1
    elif(key==114):
        white_thresh+=1
    elif(key==110):
        white_thresh-=1
    elif(key==115):
        cv2.imwrite("im1.png",im1Shifted)
        cv2.imwrite("im2.png",im2Shifted)
        cv2.imwrite("contrast.png",contrast)
