# 1. Opens first image. Click on the centre point of the circle area (the centre point that has already been saved is displayed as a small black circle). Close window.
# 2. Point in the centre? Enter "y" or "n". With "n", click again.
# 3. Save new centre point? "Enter "y" or "n
# 4. Images are displayed in sequence
#  4.1 Set the slider for the threshold so that all individuals are recognised correctly. Remember the threshold and count the number of individuals. Close both windows.
#  4.2 Specify threshold and number of individuals on request
# 5. Angabe des Schwellenwerts und der Anzahl der Personen auf Anfrage
# 6. Transferring the values from calibration to thresh_mini_maxi


# read information out of filenames
from __future__ import print_function
import cv2 as cv
import numpy as np
import random as rng
import os
import pandas as pd
from glob import glob
from matplotlib import pyplot as plt

#Functions for determining the pointer position on images  
click_events = []    
def click_callback(event, x, y, flags, params):
    # checking for left mouse clicks
    if event == cv.EVENT_LBUTTONDOWN:
        click_events.append([x, y])
               
def get_pos(image_name):
    cv.setMouseCallback(image_name, click_callback)
     
def rem_pos(image_name):
    try:
        cv.setMouseCallback(image_name, lambda *args : None)  
    except:
        pass

def get_final_pos(image_name):
    get_pos(image_name)
    cv.waitKey() 
    rem_pos(image_name)
    return click_events[-1]           
    
#    
def thresh_callback(val,show_image=True):
    threshold = val
    threshold, output = cv.threshold(src_final, thresh=threshold, maxval=255, type=cv.THRESH_BINARY)
    contours = cv.findContours(output, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)[0]
    minRect = [None]*len(contours)
    minEllipse = [None]*len(contours)
    AreaContour = [None]*len(contours)
    AreaEllipse = [None]*len(contours)
    for i, c in enumerate(contours):
        minRect[i] = cv.minAreaRect(c)
        if c.shape[0] > 5:
            e = cv.fitEllipse(c)
            widthE = e[1][0]
            heightE = e[1][1]
            AreaEllipse[i] = 3.14159265359 * (widthE/2.0) * (heightE/2.0)
            #print(heightE,"\n",widthE,"\n",Liste_true_AreaE[i],"\n""\n")
            AreaContour[i] = cv.contourArea(c)
            minEllipse[i] = e

    #store number of setted ellipses (>= 5 points necessary to set them)
    ell = len([e for e in minEllipse if e is not None])
    ellipses_number.append(ell)

    #Draw contours + rotated rects + ellipses
    drawing = np.zeros((output.shape[0], output.shape[1], 3), dtype=np.uint8)
    for i, c in enumerate(contours):
        color = (rng.randint(0, 256), rng.randint(0, 256),
                 rng.randint(0, 256))
        # contour
        cv.drawContours(drawing, contours, i, color)
        # ellipse
        if c.shape[0] > 5:
           cv.ellipse(drawing, minEllipse[i], color, 2)
        #rotated rectangle
        box = cv.boxPoints(minRect[i])
        box = np.intp(box)
        cv.drawContours(drawing, [box], 0, color)
    if show_image:   
        cv.imshow('Contours', drawing)
    #cv.waitKey()

    return minRect, minEllipse, AreaContour, ellipses_number, AreaEllipse

#Fill empty lines of the names with "None"
def name_infos(info):
    if len(info) == 6:
        info.insert(-1, str(info[4].split("_")[-1]))
    elif len(info) == 4:
        info.append("None")
        info.append("None")
        info.append(1)
    elif len(info) == 5:
        index4 = info[4]
        if len(index4) == 1:
            info.insert(4, "None")
            info.insert(4, "None")
        elif len(index4) > 2:
            info.append(str(info[4].split("_")[-1]))
            info.append(1)
    else:
        pass
        print(f + ": Photofile has wrong name layout")

    return info

#select ellipses in spec range of area (now identified as individuals)
def find_individuals(AreaContour, mini, maxi):
    for n in [e for e in AreaContour if e is not None]:
        if mini < n < maxi:
            individuals.append(n)
            
    return individuals

#gain sublists as pre-step for individual_list 
def individual_sublist(individuals):
    sublist = [None]*len(individuals)
    for n, i in enumerate(individuals):
        l = []
        l = info.copy()
        l.append(i)
        sublist[n] = l
    df_sublist = pd.DataFrame(sublist)
    
    return sublist, df_sublist

#Individual_List: merge sublists(list with all ellipses)
def individual_list(main_list):
    df2 = pd.DataFrame(main_list)
    return df2

#Overview-List (with information about photo content)
def overview_list(metadata, ellipses_number, individual_number):
    df1 = pd.DataFrame(metadata, columns = ["Site_ID", "Date", "Order",
                                            "Specie","Lower sieve", "[%]", "Amount", "Threshold"])
    df1["number ellipses"] = ellipses_number
    df1["number individuals"] = individual_number
    print(df1.columns)
    return df1

#Auslesen von Save-Datei: Mainpath + x und y Koordinate
CUR_DIR = os.path.abspath(".")
path_to_save = open(CUR_DIR+'/Save.txt')  
string_saves = path_to_save.read() 
path_to_save.close()
list_saves = string_saves.split(",")
path_to_main = list_saves[0] 
x = int(list_saves[1])
y = int(list_saves[2])

files = glob(path_to_main+'\Photos_Order\*.jpg')

folders = []
metadata = []
ellipses_number = []
individual_number = []
individuals = []
main_list = pd.DataFrame()
final_pos = False

for f in files:
    done = "n"
    folders.append(os.path.dirname(f))
    info = os.path.basename(f).split(".")[:-1]  
    name_infos(info) 
    src = cv.imread(f)
    #Convert image to gray and blur it
    src_gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)
    src_gray = cv.blur(src_gray, (3, 3))                                            #andere Blurverfahren nutzen?
    #Morphological erosion and dilatation, before setting kernel
    kernel = np.ones((7, 7), np.uint8)
    src_gray = cv.erode(src_gray, kernel, iterations=1)
    src_gray = cv.dilate(src_gray, kernel, iterations=1)
    #Morphological opening: Vanish legs etc - small contours
    src_gray = cv.morphologyEx(
        src_gray, cv.MORPH_OPEN, cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5)))
    #downscale as test image is too large for easy display
    #src_gray = cv.resize(src_gray, (0, 0), fx=0.2, fy=0.2) #neue Bilder (Manu)
    #src_gray = cv.resize(src_gray, (0, 0), fx=0.1, fy=0.1) #neue Bilder (Heidi)
    src_gray = cv.resize(src_gray, (0, 0), fx=0.1, fy=0.1) #fuer alte Bilder (Fabian)  
    #src_cut = src_gray[50:750, 50:750] #neue Bilder (Manu)
    #src_cut = src_gray[0:300, 0:300] #neue Bilder (Heidi)
    src_cut = src_gray[0:300, 0:300] #alte Bilder (Fabian)
    #src_cut = src_gray[50:300, 00:300] #alte Bilder (Kai)
    while not final_pos:
        src_cut_schleife = src_cut.copy()
        src_cut_schleife = cv.circle(src_cut_schleife, (x, y), 5, 0, -1)
        cv.namedWindow('New')
        cv.imshow('New',src_cut_schleife)
        x , y = get_final_pos('New')
        #src_cut_schleife = cv.circle(src_cut_schleife, (x, y), 85, 0, -1) #alte Bilder (Fabian)
        src_cut_schleife = cv.circle(src_cut_schleife, (x, y), 80, 0, -1) #alte Bilder (Kai,Maja)
        #src_cut_schleife = cv.circle(src_cut_schleife, (x, y), 110, 0, -1) #neue Bilder (Manu)
        #src_cut_schleife = cv.circle(src_cut_schleife, (x, y), 110, 0, -1) #neue Bilder (Heidi)
        cv.imshow('New',src_cut_schleife)
        cv.waitKey()
        if input("Punkt ist mittig? y/n\n") == "y":
            final_pos = True
            if input("Neuen Mittelpunkt abspeichern? (y/n)\n") == "y":
                with open('Save.txt','w') as Save:
                    list_saves[1] = x
                    list_saves[2] = y
                    string_saves =','.join([str(item) for item in list_saves])
                    Save.write(string_saves)
                    
    # creating circle mask
    mask = np.zeros(src_cut.shape)
    #mask = cv.circle(mask, (x, y), 85, 255, -1) # alte Bilder (Fabian)
    mask = cv.circle(mask, (x, y), 80, 255, -1) # alte Bilder (Kai,Maja)
    #mask = cv.circle(mask, (x, y), 110, 255, -1) #neue Bilder (Manu)
    #mask = cv.circle(mask, (x, y), 110, 255, -1) #neue Bilder (Heidi)
    #apply mask
    src_final = np.where(mask == 0, 255, src_cut)
    
    #setting ellipses
    print(os.path.basename(f))
    source_window = 'Source'
    cv.namedWindow(source_window)
    cv.imshow(source_window, src_final)
    max_thresh = 255
    thresh = 100  # initial threshold
    cv.createTrackbar('Threshold:', source_window, thresh, max_thresh, thresh_callback)
    cv.waitKey() 
    
    if done != "y" and done != "n":                            
        done == "n" 
        continue    
    
    while done == "n":
    #save identified treshhold in a dictionary
        fitting_thresh = float(input("Best fitting threshold: "))
        mini = float(3) #Hier kann Minimalwert zur Erkennung eingestellt werden
        maxi = float(400) #Hier kann Maximalwert zur Erkennung eingestellt werden
        minRect, minEllipse, AreaContour, ellipses_number, AreaEllipse = thresh_callback(fitting_thresh,False)
        cv.waitKey()
        individuals = []
        find_individuals(AreaContour, mini, maxi)
        individual_number.append(len(individuals))
        sublist, df_sublist = individual_sublist(individuals)
        if f == files[0]:
            main_list = df_sublist
        else:
            main_list = main_list.append(df_sublist, ignore_index = True)         
        print("Erkannte Individuen: ",len(individuals))
        
        done = str(input("Threshold results in same recognized individuals as there were counted? (y/n): \n")) 
    
    if done == "y":
        counted = float(input("Gezählte Individuen: "))
        #anhängen von infos an metadata
        #geht einfacher?
        info.append(len(individuals))
        info.append(counted)
        info.append(fitting_thresh)
        info.append(mini)
        info.append(maxi)
        metadata.append(info)
        continue
    
individual_list(main_list)

Kalibrierung = pd.DataFrame(metadata, columns=["Site_ID", "Date", "Order", "Specie", "Lower sieve", "[%]", "Amount","Gefunden","Gezählt","Thresh","Mini","Maxi"])
pd.DataFrame(Kalibrierung).to_excel(
      path_to_main+'\Kalibrierung.xlsx', sheet_name="ph_sel",
     columns=["Site_ID", "Date", "Order", "Specie", "Lower sieve", "[%]", "Amount","Gefunden","Gezählt","Thresh","Mini","Maxi"])

