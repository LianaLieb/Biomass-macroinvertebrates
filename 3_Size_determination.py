# 1. Read out all data
# 2. Fully automatic evaluation of the images. Possibility of displaying what the programme does either after painting each individual ellipse or after overall evaluation of an image.
# 3. Direct output of the image name and for each individual: number, major, minor and extent
# 4. Saving the evaluation in the output folder: "3_indiviudals_final" and "3_overview_final"

# Load all packages:
from __future__ import print_function
import cv2 as cv
import numpy as np
import random as rng
from glob import glob
import os
import pandas as pd
from matplotlib import pyplot as plt

# set seed for random number generation
rng.seed(12345)

#apply threshold, mini and maxi from previous steps
##if you may identify families etc. strongly deviating from the order:
    ##give them an extra path within this loop
def apply_values(df_values):
    
    if info[2] == "Coleo": #variable "info"
        if info[3] == "Ad":
            if "Elmis" in info[3] or "Elodes" in info[3] or "Limnius" in info[3] or "Riolus" in info[3]: # very small adult animals, therefore it takes smaller values
                row = df_values.loc[df_values['Order'] == "Coleo_Ad_small"]
            else:
                row = df_values.loc[df_values['Order'] == "Coleo_Ad"]
        elif info[3] == "Lv":
            row = df_values.loc[df_values['Order'] == "Coleo_Lv"]
        else:
            row = df_values.loc[df_values['Order'] == "Coleo_Ad"]
    elif  info[2] == "Crust":
        if info[4] == "None":
            row = df_values.loc[df_values['Order'] == "Crust"]
        else:
            row = df_values.loc[df_values['Order'] == "Crust_Lower_sieve"]
    elif info[2] == "Eph":
        if "Ecdy" in info[3] or "danica" in info[3]:
            row = df_values.loc[df_values['Order'] == "Eph_big"]
        else:
            row = df_values.loc[df_values['Order'] == "Eph"]
    elif info[2] == "Dipt":
        if "Tany" in info[3] or "Chiro" in info[3]:
            row = df_values.loc[df_values['Order'] == "Dipt_small"] #for new species, see for yourself which are large and which are small
        else:
            row = df_values.loc[df_values['Order'] == "Dipt"]
    elif info[2] == "Trich":
        if "_small" in info[3]:
            row = df_values.loc[df_values['Order'] == "Trich_small"]
        else:
            row = df_values.loc[df_values['Order'] == "Trich"] 
    else: #df_values["Order"].str.contains(str(info[2])):
        row = df_values.loc[df_values['Order'] == str(info[2])]

    threshold = float(row["Threshold"])
    mini = float(row["Mini"])
    maxi = float(row["Maxi"])
    #else:
        #print(f + ": For this order, no values has been stored in excel file yet.")
        #pass
        
    return threshold, mini, maxi

#threshholding, find ellipses
def thresh_callback(val):
    threshold = val 
    # classify pixels whether under or above threshold
    threshold, output = cv.threshold(
        src_final, thresh=threshold, maxval=255, type=cv.THRESH_BINARY)
    # calculate contours, second argument contains info on levels of contours
    contours = cv.findContours(output, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[0]
    # Find the rotated rectangles and ellipses for each contour
    # Create empty list in which n (=number of contours) rectangles,
        #ellipses and areas will be stored
    minRect = [None]*len(contours)
    minEllipse = [None]*len(contours)
    AreaContour = [None]*len(contours)
    AxisLenghts = [None]*len(contours)
    output = src_final.copy()

    # iterate through all contours and get rectangles/ellipses
    for i, c in enumerate(contours):
        minRect[i] = cv.minAreaRect(c)
        if c.shape[0] > 5:
            e = cv.fitEllipse(c)
            #store contourArea in AereaEllipses
            AreaContour[i] = cv.contourArea(c)
            #store axis lenghts under AxisLenghts (major , minor axis)
            p = e[1]
            AxisLenghts[i] = p
            minEllipse[i] = e

    #store number of setted ellipses (>= 5 points necessary to set them)
    ell = len([e for e in minEllipse if e is not None])
    ellipses_number.append(ell)


    return minRect, minEllipse, AreaContour, ellipses_number


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
        print(f + ": Photofile has wrong name layout")# photo name is wrong must be renamed

    return info

# select ellipses in spec range of area (now identified as individuals)
# and draw those ellipses in the photofile output
def find_individuals(AreaContour, minEllipse, mini, maxi):
    major_lengths = []
    minor_lengths = []  
    Perimeters = []  
    Counter = 0    
    for i, ellipse in enumerate(AreaContour):
        if ellipse is not None:
            v = minEllipse[i]

            if mini < ellipse < maxi:
                individuals.append(ellipse)
                draw_ellipses(output, v)
                major = minEllipse[i][1][1]
                minor = minEllipse[i][1][0]
                a = major*0.5
                b = minor*0.5
                h = ((a-b)**2)/((a+b)**2)
                Perimeter = 3.14159265359*(a+b)*(1+((3*h)/(10+((4-(3*h))**(1/2)))))
                major_lengths.append(major)
                minor_lengths.append(minor)
                Perimeters.append(Perimeter)
                Counter = Counter +1
                print("Individuum: ",Counter,"\nMajor: ",major,"\nMinor: ",minor,"\nPerimeter: ",Perimeter,"\n\n")
                #Hier auskommentieren zur Ueberpruefung:
                #cv.imshow("Active", output)
                #cv.waitKey()
                #Filename = os.path.basename(f)
                #cv.imwrite(Filename, output)
    return individuals, major_lengths, minor_lengths, Perimeters


def draw_ellipses(output, v):
    center_coordinates = (int(v[0][0]), int(v[0][1]))
    mi = int((v[1][0]) / 2)
    ma = int((v[1][1]) / 2)
    axesLengths = (mi, ma)
    #axesLengths = (int(v[1][0]), (int(v[1][1])))              
    angle = int(v[2])# Ellipses are drawn in saved output images
    startAngle = 0# Ellipses are drawn in saved output images
    endAngle = 360
    color = (0, 0, 0)
    thickness = 1
    
    cv.ellipse(output, center_coordinates, axesLengths, angle, startAngle, endAngle, color, thickness)

    return output


#gain sublists as pre-step for individual_list 
def individual_sublist(individuals, major_lenghts, minor_lenghts, Perimeters):
    sublist = [None]*len(individuals)
    for n, i in enumerate(individuals):
        l = []
        l = info.copy()
        l.append(i)
        ma = major_lenghts[n]
        l.append(ma)
        mi = minor_lenghts[n]
        l.append(mi)
        Per = Perimeters[n]
        l.append(Per)
        sublist[n] = l
    df_sublist = pd.DataFrame(sublist)
    
    return sublist, df_sublist


# Individual_List: merge sublists(list with all ellipses)
def individual_list(main_list):
    df3 = pd.DataFrame(main_list)# columns = ["Site_ID", "Date", "Order", "Specie", "Lower sieve", "[%]", "Amount", "Threshold", "Area ellipse"])
    df3.rename(columns = {0: "Site_ID", 1:"Date", 2:"Order", 3:"Specie", 4:"Lower sieve", 5:"[%]", 6:"Amount", 7:"Threshold", 8:"Area contour", 9: "Major axis", 10: "Minor axis", 11: "Perimeter"}, inplace = True)
    pd.DataFrame(df3).to_excel(
        r"path..\3_individuals_final.xlsx", sheet_name="Individuals") # enter right filepath !!!
        
    return df3


# Overview-List (with information about photo content)
def overview_list(metadata, ellipses_number, individual_number):
    df4 = pd.DataFrame(metadata, columns = ["Site_ID", "Date", "Order",
                                            "Specie","Lower sieve", "[%]", "Amount", "Threshold"])
    df4["Number ellipses"] = ellipses_number
    df4["Number individuals"] = individual_number
    df4.columns
    pd.DataFrame(df4).to_excel(
        r"path..\3_overwiev_final.xlsx", sheet_name="Overview") # enter right filepath !!
        #columns = ["Site_ID", "Date", "Order", "Specie", "Lower sieve", "[%]",
                   #"Amount", "Threshold", "Number ellipses", "Number individuals"])
    return df4

click_events = []    
def click_callback(event, x, y, flags, params):
    # checking for left mouse clicks
    if event == cv.EVENT_LBUTTONDOWN:
        #print(f"X: {x}; Y: {y}")
        click_events.append([x, y])
        # remove callback so we dont get more than 1 num
               
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


#----------------------------
# parser = argparse.ArgumentParser(description='Code for Creating Bounding rotated boxes and ellipses for contours tutorial.')
# parser.add_argument('--input', help='Path to input image.', default='stuff.jpg')
# args = parser.parse_args()
# src = cv.imread(args.input)

#----------------------------

CUR_DIR = os.path.abspath(".")
path_to_save = open(CUR_DIR+'/Save.txt')  
string_saves = path_to_save.read() 
path_to_save.close()
list_saves = string_saves.split(",")
path_to_main = list_saves[0] 
x = int(list_saves[1])
y = int(list_saves[2])


##update to path in which thresh, mini and maxci are listed
df_values = pd.read_excel(path_to_main+'thresh_mini_maxi.xlsx')

## update to path in which photoseletion is stored, (* = Platzhalter)
files = glob(path_to_main+'Photos\*.jpg')

folders = []
metadata = []
ellipses_number = []
individual_number = []
individuals = []
main_list = []

for f in files:    
    folders.append(os.path.dirname(f))  # Add the names to folders
    info = os.path.basename(f).split(".")[:-1]  
    name_infos(info) 
    
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
    # downscale as test image is too large for easy display, cut it
    #src_gray = cv.resize(src_gray, (0, 0), fx=0.1, fy=0.1) #neue Bilder (Heidi)
    #src_gray = cv.resize(src_gray, (0, 0), fx=0.2, fy=0.2) #neue Bilder (Manu)
    src_gray = cv.resize(src_gray, (0, 0), fx=0.1, fy=0.1) #fuer alte Bilder (Fabian)  
    #src_cut = src_gray[0:300, 0:300] #neue Bilder (Heidi)
    #src_cut = src_gray[50:750, 50:750] #neue Bilder (Manu)
    src_cut = src_gray[0:300, 0:300] #alte Bilder (Fabian)
    #src_cut = src_gray[50:300, 0:300] #alte Bilder (Kai)
    # creating circle mask
    mask = np.zeros(src_cut.shape)
    #mask = cv.circle(mask, (x, y), 110, 255, -1) # alte Bilder (Heidi)
    #mask = cv.circle(mask, (x, y), 85, 255, -1) # alte Bilder (Fabian)
    mask = cv.circle(mask, (x, y), 80, 255, -1) # alte Bilder (Kai,Maja,Eva)
    #mask = cv.circle(mask, (x, y), 110, 255, -1) #neue Bilder (Manu)
    #apply mask
    src_final = np.where(mask == 0, 255, src_cut)
    #cv.imshow('Final', src_final)
    #cv.waitKey()
    # create copy to draw individual ellipses in
    output = src_final.copy()
    
    #setting ellipses
    threshold, mini, maxi = apply_values(df_values)
    minRect, minEllipse, AreaContour, ellipses_number = thresh_callback(threshold)

    #save identified treshhold in a list
    info.append(threshold)
    metadata.append(info)
    
    individuals = []
    individuals, major_lengths, minor_lengths, Perimeters = find_individuals(AreaContour, minEllipse, mini, maxi)
    
    print(info) 
    
    ###um jede gemalte Ellipse anzuschauen:
    #cv.imshow("Active", output)
    #cv.waitKey()
    
    # save final picture into seperated file
    path_final = path_to_main+'Photos_final'
    cv.imwrite(path_final + f[52:-6] + ".final.eroded.jpg", output)
    individual_number.append(len(individuals))
    sublist, df_sublist = individual_sublist(individuals, major_lengths, minor_lengths, Perimeters)
    if f == files[0]:
        main_list = df_sublist
    else:
        main_list = main_list.append(df_sublist, ignore_index = True) 
    print("Insgesamt gefunden: ",len(individuals), "Individuen")
    print()

        
#Abspeichern der Ergebnisse
# Overview-List
overview_list(metadata, ellipses_number, individual_number)

# individual-List
individual_list(main_list)
