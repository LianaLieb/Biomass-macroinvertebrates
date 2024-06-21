# 1. Reads path and images and checks whether the Photos_Order folder is empty
# 2. Query which orders and how many images per order are to be used for calibration. 
# 3. Creating the data frame with the images randomly selected for calibration
# 4. Copy the randomly selected images to the Photos_order folder

from __future__ import print_function 
import os
import shutil
import pandas as pd
from glob import glob

#Leere Zeilen der Namen mit "None" auffüllen
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
            print(f + ": Photofile has wrong name layout")
            pass    
    
    return info

#Read save file and main path
CUR_DIR = os.path.abspath(".")
path_to_save = open(CUR_DIR+'/Save.txt')  
string_saves = path_to_save.read() 
path_to_save.close()
list_saves = string_saves.split(",")
path_to_main = list_saves[0] 
path = path_to_main+'\Photos\*.jpg'

files = glob(path) #creates a list from filenames
folders = []
metadata = []

#Check if Orders Folder is empty
if len(os.listdir(path_to_main+'\Photos_Order')) == 1: 
    print("Order Ordner ist leer. Programmw wird weiter ausgeführt.\n")
else:    
    print("Bitte 'Photos_Order'-Ordner Überprüfen ob keine alten Bilder vorhanden sind!\n")

#Reading the image names (creating the metadata list)
for f in files:
    folders.append(os.path.dirname(f)) 
    info = os.path.basename(f).split(".")[:-1]  
    name_infos(info)  
    metadata.append(info)
    
#Creating the data frame 
df_order = pd.DataFrame(metadata, columns=["Site_ID", "Date", "Order", "Specie", "Lower sieve", "[%]", "Amount"])
df_order = df_order.sort_values("Order")
orders=[]
a = "n"

#Selecting the orders and number of images to be calibrated
if input("Wollen Sie alle Ordnungen betrachten?\ny oder n\n") == "y":
    orders = ["Arachn", "Eph", "Trich", "Plec", "Dipt", "Coleo", "Mega", "Oligo", "Crust", "Biva", "Gastr", "Turb", "Hiru", "Hetero", "Tenthr", "Odon"]
else:
    print("Ordnungen:\n","Arachn", "Eph", "Trich", "Plec", "Dipt", "Coleo", "Mega", "Oligo", "Crust", "Biva", "Gastr", "Turb", "Hiru", "Hetero", "Tenthr", "Odon")
    while a == "n":
        orders.append(input("Bitte auszuwählende Ordnung eingeben: "))
        a = input("Fertig? y oder n\n")

anzahl_test = int(input("Geben Sie die Anzahl der pro Ordnung zufällig auszuwählenden Bilder an:\n"))
order_list = pd.DataFrame()

#Create a data frame that contains the randomly selected images 
for i, o in enumerate(orders):
    df_new = df_order[df_order['Order'] == o]       
    l = int(len(df_new.axes[0]))        
    if l < anzahl_test:
        anzahl = l
        print(l,o,"gefunden")
    else:
        anzahl = anzahl_test     
        print(anzahl,o,"gefunden")           
    if i == 0: 
        if l == 0:
            continue
        elif l <= 3:
            order_list = (df_new.sample(n = l, replace = False))
        elif l > 3:
            order_list = (df_new.sample(n = anzahl, replace = False))
    elif i > 0:
        if l == 0:
            continue
        elif l <= 3:
            order_list = order_list.append(df_new.sample(n = l, replace = False))     
        elif l > 3:
            order_list = order_list.append(df_new.sample(n = anzahl, replace = False))
    else:
        print("Something went wrong respecting i(ndex) and l (num of respective files")
        continue

#Copy images from source folder to destination folder
order_list['index'] = order_list.index
for i in order_list['index']:
    src = files[i]
    dst = path_to_main+'/Photos_Order'
    shutil.copy(src, dst)

#Save the data frame containing the selected images
order_list = pd.DataFrame.drop(order_list,columns=['index'])
pd.DataFrame(order_list).to_excel(path_to_main+'/1_photo_selection.xlsx')
