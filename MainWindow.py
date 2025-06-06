from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QTextEdit,
    QScrollArea
)

from PySide6.QtCore import (
    Qt
)

from PySide6.QtGui import (
    QTextOption
)

from pathlib import Path
import requests
import json
import zipfile
import os
import sqlite3
import pickle
import shutil

import unicodedata
import pygsheets

from ItemSlot import ItemSlot
from WeaponDisplay import WeaponDisplay

class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.baseURL = "https://www.bungie.net"
        self.APIKey = ""
        self.setWindowTitle("DIM Wishlist Generator")

        print("Connecting to google Sheet")

        google = pygsheets.authorize(client_secret="Secret.json")
        spreadSheet = google.open("Copy of Destiny 2: Endgame Analysis 2")

        # Shotguns, Snipers, Fusions, BGLs, HGLs, Autos, HCs < all have special weapon types that need to be specifically accounted for
        weaponsToCheck = ["Glaives", "Traces", "Rocket Sidearms", "LMGs", "Swords", "Rockets", "LFRs", "Bows", "Pulses", "Scouts", "Sidearms", "SMGs"]

        self.bestWeapons = []

        print("Grabbing best weapons")

        self.CheckWeapons(spreadSheet, weaponsToCheck, None) # all non specific weapons

        self.CheckWeapons(spreadSheet, ["Shotguns"], ["Slug"]) # only slugs
        self.CheckWeapons(spreadSheet, ["Shotguns"], ["Slug"], True) # all other shotguns

        self.CheckWeapons(spreadSheet, ["Snipers"], ["Rapid"]) # only rapid snipers
        self.CheckWeapons(spreadSheet, ["Snipers"], ["Aggressive"]) # only aggressive snipers

        self.CheckWeapons(spreadSheet, ["Fusions"], ["Rapid"]) # only rapid fusions

        self.CheckWeapons(spreadSheet, ["BGLs"], ["Area Denial"]) # only aread denial
        self.CheckWeapons(spreadSheet, ["BGLs"], ["Wave"]) # only wave
        self.CheckWeapons(spreadSheet, ["BGLs"], ["Area Denial", "Wave"], True) # all other BGLs

        self.CheckWeapons(spreadSheet, ["HGLs"], ["Compressed Wave"]) # only compressed wave HGLs
        self.CheckWeapons(spreadSheet, ["HGLs"], ["Compressed Wave"], True) # all other HGLs

        self.CheckWeapons(spreadSheet, ["Autos"], ["Support"]) # only support autos
        self.CheckWeapons(spreadSheet, ["Autos"], ["Support"], True) # all other autos

        self.CheckWeapons(spreadSheet, ["HCs"], ["Heavy Burst"]) # only burst HCs
        self.CheckWeapons(spreadSheet, ["HCs"], ["Heavy Burst"], True) # all other HCs

        print("Cleaning best weapons")

        self.bestWeapons = [weapon for weapon in self.bestWeapons if weapon != "None"]

        with open("Credentials.txt", "r") as creds:
            self.APIKey = creds.readline()

        mainLayout = QVBoxLayout()
        topLayout = QHBoxLayout()

        bodyLayout = QHBoxLayout()
        leftLayout = QVBoxLayout()
        self.middleLayout = QVBoxLayout()
        rightLayout = QVBoxLayout()
        
        bottomLayout = QHBoxLayout()

        #####Top Layout#####
        mainLayout.addLayout(topLayout)
        #Force Get Manifest
        forceGetManifest = QPushButton("Force Get Manifest")
        forceGetManifest.clicked.connect(lambda: self.CheckForUpdates())
        topLayout.addWidget(forceGetManifest)

        #####Left Layout#####
        bodyLayout.addLayout(leftLayout, 20)
        self.inputTextBox = QTextEdit()
        leftLayout.addWidget(self.inputTextBox, 100)

        #####Middle Layout#####
        bodyLayout.addLayout(self.middleLayout, 40)
        self.outputTextBox = QTextEdit()
        self.middleLayout.addWidget(self.outputTextBox)

        #####Right Layout#####
        bodyLayout.addLayout(rightLayout, 40)

        self.weaponDisplay = WeaponDisplay()
        rightLayout.addWidget(self.weaponDisplay)

        #####Body Layout#####
        mainLayout.addLayout(bodyLayout)

        #####Bottom Layout#####
        mainLayout.addLayout(bottomLayout)
        exportWishlist = QPushButton("Export Wishlist")
        exportWishlist.clicked.connect(self.ExportWishlist)
        bottomLayout.addWidget(exportWishlist)
        bottomLayout.addWidget(QPushButton("Load Wishlist"))
        bottomLayout.addWidget(QPushButton("Clear Wishlist"))

        #Create Central Widget
        mainWidget = QWidget()
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

        #Get Data
        self.CheckForUpdates()

    def CheckWeapons(self, spreadSheet, weaponsToCheck, weaponTypeFilter, invert = False):
        for weaponList in weaponsToCheck:
            weaponSheet = spreadSheet.worksheet_by_title(weaponList)
            weaponData = weaponSheet.get_values_batch(["B3:B1000","C3:C1000","D3:D1000"])

            weaponConvert = list(zip(
                [word[0] for word in weaponData[0]], # name
                [word[0] for word in weaponData[1]], # element
                [word[0] for word in weaponData[2]])) # weapon type
            
            if weaponTypeFilter != None and len(weaponTypeFilter) > 0:
                weaponConvert = [wep for wep in weaponConvert if (wep[2] not in weaponTypeFilter if invert else (wep[2] in weaponTypeFilter))]

            self.bestWeapons.append(str(next((name for name, element, weaponType in weaponConvert if element == "Kinetic" if name != "Ideal"), None)).replace("BRAVE version", ""))
            self.bestWeapons.append(str(next((name for name, element, weaponType in weaponConvert if element == "Strand"  if name != "Ideal"), None)).replace("BRAVE version", ""))
            self.bestWeapons.append(str(next((name for name, element, weaponType in weaponConvert if element == "Stasis"  if name != "Ideal"), None)).replace("BRAVE version", ""))
            self.bestWeapons.append(str(next((name for name, element, weaponType in weaponConvert if element == "Solar"   if name != "Ideal"), None)).replace("BRAVE version", ""))
            self.bestWeapons.append(str(next((name for name, element, weaponType in weaponConvert if element == "Arc"     if name != "Ideal"), None)).replace("BRAVE version", ""))
            self.bestWeapons.append(str(next((name for name, element, weaponType in weaponConvert if element == "Void"    if name != "Ideal"), None)).replace("BRAVE version", ""))

    def CheckForUpdates(self):
        self.headers = {"X-API-Key":self.APIKey}
        self.all_data = {}

        #get current manifest
        manifest_url = self.baseURL+"/Platform/Destiny2/Manifest"
        r = requests.get(manifest_url, headers=self.headers)
        manifest = r.json()

        #if we already have a Res folder, get the newest manifest and check it with our existing manifest
        if os.path.isdir("Res"):
            with open("Res/ManifestData", "r") as manifestData:
                currentManifestName = manifestData.readline()

            newManifestName = str(manifest["Response"]["mobileWorldContentPaths"]["en"]).split("/").pop()

            print("Checking versions: \ncur:" + currentManifestName, "\nnew:"+newManifestName)

            if currentManifestName != newManifestName:
                print("Manifest mismatch, getting new")
                #clear Res folder
                shutil.rmtree("Res")
                os.mkdir("Res")
                self.DownloadManifest(self.baseURL+manifest['Response']['mobileWorldContentPaths']['en'])
            else:
                print("Manifest version is up to date, checking for pickle")
                self.CheckForPickle()
        else:
            os.mkdir("Res")
            self.DownloadManifest(self.baseURL+manifest['Response']['mobileWorldContentPaths']['en'])

    def DownloadManifest(self, manifest_url):
        #download the current zipped manifest file
        r = requests.get(manifest_url, headers=self.headers)
        print("downloading current manifest")
        with open("Res/MANZIP", "wb") as zip:
            zip.write(r.content)
        print("downloaded")

        #Extract zip to .content file
        print("extracting")
        with zipfile.ZipFile('Res/MANZIP') as zip:
            name = zip.namelist()
            zip.extractall()
            os.rename(name[0], "Res/"+name[0])
        
        #save the current manifest version
        with open("Res/ManifestData", "w") as manifestVersion:
            manifestVersion.write(name[0])

        print("extracted")
        self.CheckForPickle()

    hash_dict = [
        "DestinyInventoryItemDefinition"
    ]

    def CheckForPickle(self):
        #check if pickle exists
        self.all_data = {}

        if os.path.isfile("Res/manifest.pickle"):
            print("pickle found!")
            #read pickle and output to all_items
            with open("Res/manifest.pickle", "rb") as pickleRead:
                self.all_data = pickle.load(pickleRead)
        else:
            with open("Res/ManifestData", "r") as manifestData:
                    currentManifestData = manifestData.readline()

            con = sqlite3.connect("Res/"+currentManifestData)
            cur = con.cursor()

            for table_name in self.hash_dict:
                #get a list of all the jsons from the table
                cur.execute('SELECT json from '+table_name)
                print('Generating '+table_name+' dictionary....')

                #this returns a list of tuples: the first item in each tuple is our json
                items = cur.fetchall()

                #create a list of jsons
                item_jsons = [json.loads(item[0]) for item in items]

                item_dict = {}

                for item in item_jsons:
                    item_dict[item["hash"]] = item
                
                self.all_data[table_name] = item_dict

            #save pickle
            with open('Res/manifest.pickle', 'wb') as data:
                pickle.dump(self.all_data, data)

        self.GenDict()

    def GenDict(self):
        self.weapon_dict = {}

        for itemHash in self.all_data["DestinyInventoryItemDefinition"]:
            if self.all_data["DestinyInventoryItemDefinition"][itemHash]["itemType"] == 3:
                self.weapon_dict[itemHash] = self.all_data["DestinyInventoryItemDefinition"][itemHash]["displayProperties"]["name"]

        self.outputTextBox.setText("\n".join(self.weapon_dict.values()))
        self.inputTextBox.setText("\n".join(self.bestWeapons))

        return
        x = 0
        for weaponHash in self.weapon_dict:
            weaponButton = ItemSlot(self.weapon_dict[weaponHash])
            #weaponButton.itemButton.clicked.connect(lambda: self.WeaponSelected(weaponButton.weaponHash))
            self.middleLayout.addWidget(weaponButton)

            x+=1
            if x >= 10:
                break

    def ExportWishlist(self):
        print("exporting wishlist!")

        inputList = self.inputTextBox.toPlainText().split("\n")

        outputList = []
        outputListName = []

        for item in inputList:
            #outputs = [key for key, value in self.weapon_dict.items() if str(value).lower() == item.lower()]
            outputs = [key for key, value in self.weapon_dict.items() if 
                       "".join(c for c in unicodedata.normalize('NFD', str(value).lower()) if unicodedata.category(c) != 'Mn') == 
                       "".join(c for c in unicodedata.normalize('NFD', item.lower().replace("\"", "")) if unicodedata.category(c) != 'Mn')]
            if len(outputs) == 0:
                if item.lower() != "Brave Version\"".lower():
                    print("couldnt find", item)
            outputList.extend(list(map(str,outputs)))


            outputsNames = [value for key, value in self.weapon_dict.items() if 
                       "".join(c for c in unicodedata.normalize('NFD', str(value).lower()) if unicodedata.category(c) != 'Mn') == 
                       "".join(c for c in unicodedata.normalize('NFD', item.lower().replace("\"", "")) if unicodedata.category(c) != 'Mn')]
            outputListName.extend(list(map(str,outputsNames)))

        print("\n".join(outputListName))

        outputListString = "dimwishlist:item="+"\ndimwishlist:item=".join(outputList)

        self.outputTextBox.setText(outputListString)
