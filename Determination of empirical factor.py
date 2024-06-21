# 1. Read out all files
# 2. Run for each image in the reference folder
# 3. Display option for drawn ellipses and rectangles
# 4. Calculate the arithmetic mean of all images and save the empirical factor in a save file

#Format for reference images:
    #Site-ID.Date.Referenz.LangeSeitexKurzeSeite 
    #Example NL_AltREF.202106.Referenz.2x1 

from __future__ import print_function
import cv2 as cv
import numpy as np
import random as rng
import os
from glob import glob
       
    

def thresh_callback(val):
    threshold = val
    threshold, output = cv.threshold(
        src_final, thresh=threshold, maxval=255, type=cv.THRESH_BINARY)
    # calculate contours, second argument contains info on levels of contours
    contours = cv.findContours(output, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[0]
    
    # Find the rotated rectangles and ellipses for each contour
    # Create empty list in which n (=number of contours) rectangles,
        #ellipses and areas will be stored
    minRect = [None]*len(contours)
    minEllipse = [None]*len(contours)

    # iterate through all contours and get rectangles/ellipses
    for i, c in enumerate(contours):
        minRect[i] = cv.minAreaRect(c)
        if c.shape[0] > 5:
            minEllipse[i] = cv.fitEllipse(c)
    
    drawing = np.zeros((output.shape[0], output.shape[1], 3), dtype=np.uint8)
    for i, c in enumerate(contours):
        color = (rng.randint(0, 256), rng.randint(0, 256),
                 rng.randint(0, 256))  
        # contour
        cv.drawContours(drawing, contours, i, color)
        # ellipse
        if c.shape[0] > 5:
           cv.ellipse(drawing, minEllipse[i], color, 2)
        # rotated rectangle
        box = cv.boxPoints(minRect[i])
        box = np.intp(box)
        cv.drawContours(drawing, [box], 0, color)  
        #Hier auskommentieren um Bild nicht anzeigen zu lassen
        cv.imshow('Contours', drawing)
        cv.waitKey()

    return minEllipse

#Auslesen von Mainpath
CUR_DIR = os.path.abspath(".")
path_to_save = open(CUR_DIR+'/Save.txt')  
string_saves = path_to_save.read() 
path_to_save.close()
list_saves = string_saves.split(",")
path_to_main = list_saves[0] 
x = int(list_saves[1])
y = int(list_saves[2])

files = glob(path_to_main+'\Referenz\*.jpg')
final_pos = False
E_Factor_sum = int(0)
Amount_sum = int(0)

for f in files:
    info = os.path.basename(f).split(".")[:-1] 
    if "Ref" in info:
        src = cv.imread(f)
        # Convert image to gray and blur it
        src_gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)
        src_gray = cv.blur(src_gray, (3, 3))                                         
        # Morphological erosion and dilatation, before setting kernel
        kernel = np.ones((7, 7), np.uint8)
        src_gray = cv.erode(src_gray, kernel, iterations=1)
        src_gray = cv.dilate(src_gray, kernel, iterations=1)
        # Morphological opening: Vanish legs etc - small contours
        src_gray = cv.morphologyEx(
            src_gray, cv.MORPH_OPEN, cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5)))  
        # downscale as test image is too large for easy display
        src_gray = cv.resize(src_gray, (0, 0), fx=0.2, fy=0.2) #Adjust according to the images
        src_cut = src_gray[50:750, 50:750] #Adjust according to the images      
        # creating circle mask
        mask = np.zeros(src_cut.shape)
        mask = cv.circle(mask, (x, y), 110, 255, -1) #Adjust according to the images
        # apply mask
        src_final = np.where(mask == 0, 255, src_cut)
        # setting ellipses
        minEllipse = thresh_callback(100)
        #cv.imshow('Bild',src_gray)
        #cv.waitKey()
        print(os.path.basename(f))
        major_axis = minEllipse[1][1][1]
        minor_axis = minEllipse[1][1][0]
        major = float(info[3].split("x")[0])
        minor = float(info[3].split("x")[1])
        E_Factor_major = float(major/(major_axis))
        print("Empirischer Faktor nur fuer Major: ",E_Factor_major)
        E_Factor_minor = float(minor/(minor_axis))
        print("Empirischer Faktor nur fuer Minor: ",E_Factor_minor)
        E_Factor = ((E_Factor_major+E_Factor_minor)/2)
        print("Der gemittelte empirische Faktor ist: ",E_Factor,"\n")
        E_Factor_sum = E_Factor_sum + E_Factor
        Amount_sum = Amount_sum + int(1)
        
Final_E_Factor = E_Factor_sum/Amount_sum
print("Empirischer Faktor aus arithmetischem Mittel aller Bilder: ",Final_E_Factor)
with open('Save.txt','w') as Save:
    list_saves[3] = Final_E_Factor
    string_saves =','.join([str(item) for item in list_saves])
    Save.write(string_saves)        













