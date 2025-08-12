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
from requests_oauthlib import OAuth2Session

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

        try:
            google = pygsheets.authorize(client_secret="Secret.json")
        except:
            os.remove("sheets.googleapis.com-python.json")
            google = pygsheets.authorize(client_secret="Secret.json")

        google = pygsheets.authorize(client_secret="Secret.json")
        spreadSheet = google.open("Copy of Destiny 2: Endgame Analysis 3")

        self.bestWeapons = []

        print("Grabbing best weapons")

        self.CheckWeapons(spreadSheet, "G", "H", "I", ["Shotguns"], ["Slug"]) # only slugs
        self.CheckWeapons(spreadSheet, "G", "H", "I", ["Shotguns"], ["Slug"], True) # all other shotguns

        self.CheckWeapons(spreadSheet, "G", "H", "I", ["Snipers"], ["Rapid"]) # only rapid snipers
        self.CheckWeapons(spreadSheet, "G", "H", "I", ["Snipers"], ["Aggressive"]) # only aggressive snipers

        self.CheckWeapons(spreadSheet, "G", "H", "I", ["Fusions"], ["Rapid"]) # only rapid fusions

        self.CheckWeapons(spreadSheet, "G", "H", "I", ["BGLs"], ["Area Denial"]) # only aread denial
        self.CheckWeapons(spreadSheet, "G", "H", "I", ["BGLs"], ["Wave"]) # only wave
        self.CheckWeapons(spreadSheet, "G", "H", "I", ["BGLs"], ["Area Denial", "Wave"], True) # all other BGLs

        self.CheckWeapons(spreadSheet, "H", "I", "J", ["Glaives"])
        self.CheckWeapons(spreadSheet, "G", "H", "I", ["Traces"])
        self.CheckWeapons(spreadSheet, "F", "G", "H", ["Rocket Sidearms"])
        self.CheckWeapons(spreadSheet, "G", "H", "I", ["LMGs"])

        self.CheckWeapons(spreadSheet, "G", "H", "I", ["HGLs"], ["Compressed Wave"]) # only compressed wave HGLs
        self.CheckWeapons(spreadSheet, "G", "H", "I", ["HGLs"], ["Compressed Wave"], True) # all other HGLs

        self.CheckWeapons(spreadSheet, "I", "J", "K", ["Swords"])
        self.CheckWeapons(spreadSheet, "G", "H", "I", ["Rockets"])
        self.CheckWeapons(spreadSheet, "G", "H", "I", ["LFRs"])

        self.CheckWeapons(spreadSheet, "F", "G", "H", ["Autos"], ["Support"]) # only support autos
        self.CheckWeapons(spreadSheet, "F", "G", "H", ["Autos"], ["Support"], True) # all other autos

        self.CheckWeapons(spreadSheet, "F", "G", "H", ["Bows"])

        self.CheckWeapons(spreadSheet, "F", "G", "H", ["HCs"], ["Heavy Burst"]) # only burst HCs
        self.CheckWeapons(spreadSheet, "F", "G", "H", ["HCs"], ["Heavy Burst"], True) # all other HCs

        self.CheckWeapons(spreadSheet, "F", "G", "H", ["Pulses"])
        self.CheckWeapons(spreadSheet, "F", "G", "H", ["Scouts"])
        self.CheckWeapons(spreadSheet, "F", "G", "H", ["Sidearms"])
        self.CheckWeapons(spreadSheet, "F", "G", "H", ["SMGs"])

        print("Cleaning best weapons")

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

        loadWishlist = QPushButton("Load Wishlist")
        loadWishlist.clicked.connect(self.LoadWishlist)
        bottomLayout.addWidget(loadWishlist)
        
        bottomLayout.addWidget(QPushButton("Clear Wishlist"))

        #Create Central Widget
        mainWidget = QWidget()
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

        #Get Data
        self.CheckForUpdates()

    def CheckWeapons(self, spreadSheet, perk1, perk2, origin, weaponsToCheck, weaponTypeFilter = None, invert = False):
        for weaponList in weaponsToCheck:
            weaponSheet = spreadSheet.worksheet_by_title(weaponList)
            weaponData = weaponSheet.get_values_batch(["B3:B1000",
                                                       "C3:C1000",
                                                       "D3:D1000",
                                                       perk1+"3:"+perk1+"1000",
                                                       perk2+"3:"+perk2+"1000",
                                                       origin+"3:"+origin+"1000"])

            weaponConvert = list(zip(
                [word[0] for word in weaponData[0]], # name
                [word[0] for word in weaponData[1]], # element
                [word[0] for word in weaponData[2]], # weapon type
                [word[0] for word in weaponData[3]], # perk 1
                [word[0] for word in weaponData[4]], # perk 2
                [word[0] for word in weaponData[5]], # origin trait
                ))
            
            if weaponTypeFilter != None and len(weaponTypeFilter) > 0:
                weaponConvert = [weapon for weapon in weaponConvert if (weapon[2] not in weaponTypeFilter if invert else (weapon[2] in weaponTypeFilter))]

            kinetic = [(str(name).replace("\nBRAVE version", ""), element, weaponType, perk1, perk2, origin) for name, element, weaponType, perk1, perk2, origin in weaponConvert if element == "Kinetic" if name != "Ideal"]
            strand  = [(str(name).replace("\nBRAVE version", ""), element, weaponType, perk1, perk2, origin) for name, element, weaponType, perk1, perk2, origin in weaponConvert if element == "Strand" if name != "Ideal"]
            stasis  = [(str(name).replace("\nBRAVE version", ""), element, weaponType, perk1, perk2, origin) for name, element, weaponType, perk1, perk2, origin in weaponConvert if element == "Stasis" if name != "Ideal"]
            solar   = [(str(name).replace("\nBRAVE version", ""), element, weaponType, perk1, perk2, origin) for name, element, weaponType, perk1, perk2, origin in weaponConvert if element == "Solar" if name != "Ideal"]
            arc     = [(str(name).replace("\nBRAVE version", ""), element, weaponType, perk1, perk2, origin) for name, element, weaponType, perk1, perk2, origin in weaponConvert if element == "Arc" if name != "Ideal"]
            void    = [(str(name).replace("\nBRAVE version", ""), element, weaponType, perk1, perk2, origin) for name, element, weaponType, perk1, perk2, origin in weaponConvert if element == "Void" if name != "Ideal"]

            self.bestWeapons.append(kinetic[0] if kinetic else None)
            self.bestWeapons.append(strand[0] if strand else None)
            self.bestWeapons.append(stasis[0] if stasis else None)
            self.bestWeapons.append(solar[0] if solar else None)
            self.bestWeapons.append(arc[0] if arc else None)
            self.bestWeapons.append(void[0] if void else None)
            
            self.bestWeapons = [w for w in self.bestWeapons if w != None]

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
        self.perks_dict = {}

        # TODO: rewrite with list comprehension
        for itemHash in self.all_data["DestinyInventoryItemDefinition"]:
            if self.all_data["DestinyInventoryItemDefinition"][itemHash]["itemType"] == 3: # itemtype 3 == weapon
                self.weapon_dict[itemHash] = self.all_data["DestinyInventoryItemDefinition"][itemHash]["displayProperties"]["name"]

            if "itemTypeDisplayName" in self.all_data["DestinyInventoryItemDefinition"][itemHash] and self.all_data["DestinyInventoryItemDefinition"][itemHash]["itemTypeDisplayName"] == "Trait":
                self.perks_dict[itemHash] = self.all_data["DestinyInventoryItemDefinition"][itemHash]["displayProperties"]["name"]

        self.outputTextBox.setText("\n".join(self.weapon_dict.values()))
        self.inputTextBox.setText("\n".join([w[0] for w in self.bestWeapons]))

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

        for inputItem in inputList:
            itemAppend = [(perk1, perk2, origin) for weaponName, element, weaponType, perk1, perk2, origin in self.bestWeapons if weaponName == inputItem]

            outputMatches = [(itemID, weaponName, itemAppend[0][0], itemAppend[0][1], itemAppend[0][2]) for itemID, weaponName in self.weapon_dict.items() if 
                             "".join(c for c in unicodedata.normalize('NFD', inputItem.lower()) if unicodedata.category(c) != 'Mn') ==
                             "".join(c for c in unicodedata.normalize('NFD', str(weaponName).lower()) if unicodedata.category(c) != 'Mn')]

            outputMatchesAdept = [(itemID, weaponName, itemAppend[0][0], itemAppend[0][1], itemAppend[0][2]) for itemID, weaponName in self.weapon_dict.items() if 
                             "".join(c for c in unicodedata.normalize('NFD', inputItem.lower()+" (") if unicodedata.category(c) != 'Mn') in
                             "".join(c for c in unicodedata.normalize('NFD', str(weaponName).lower()) if unicodedata.category(c) != 'Mn')]

            outputList.extend((itemID, 
                               weaponName, 
                               [key for key,value in zip(self.perks_dict.keys(), self.perks_dict.values()) if value in [p1 for p1 in str(perk1).split("\n")]], 
                               [key for key,value in zip(self.perks_dict.keys(), self.perks_dict.values()) if value in [p2 for p2 in str(perk2).split("\n")]], perk1, perk2) 
                               for itemID, weaponName, perk1, perk2, origin in outputMatches)
            outputList.extend((itemID, 
                               weaponName, 
                               [key for key,value in zip(self.perks_dict.keys(), self.perks_dict.values()) if value in [p1 for p1 in str(perk1).split("\n")]], 
                               [key for key,value in zip(self.perks_dict.keys(), self.perks_dict.values()) if value in [p2 for p2 in str(perk2).split("\n")]], perk1, perk2) 
                               for itemID, weaponName, perk1, perk2, origin in outputMatchesAdept)

            if len(outputMatches) == 0:
                print("couldnt find:", inputItem)

        finalWeaponList = []

        finalWeaponList.append("title:White Rice's Wishlist")

        for item in outputList:
            aegisNotes = "\n//notes:[" + ", ".join(i for i in str(item[4]).split("\n")) + "] [" + ", ".join(i for i in str(item[5]).split("\n")) + "]"

            finalWeaponList.append(aegisNotes)

            doublePerks = []
            singlePerks = []

            for perk1 in item[2]:
                singlePerks.append("dimwishlist:item=" + str(item[0]) + "&perks=" + str(perk1)) # first column match
                for perk2 in item[3]:
                    singlePerks.append("dimwishlist:item=" + str(item[0]) + "&perks=" + str(perk2)) # second column match
                    
                    doublePerks.append("dimwishlist:item=" + str(item[0]) + "&perks=" + str(perk1) + "," + str(perk2)) # dual match perk

            for perk1 in item[2]:
                for perk2 in item[2]:
                    if perk1 != perk2:
                        doublePerks.append("dimwishlist:item=" + str(item[0]) + "&perks=" + str(perk1) + "," + str(perk2)) # dual match perk

            for perk1 in item[3]:
                for perk2 in item[3]:
                    if perk1 != perk2:
                        doublePerks.append("dimwishlist:item=" + str(item[0]) + "&perks=" + str(perk1) + "," + str(perk2)) # dual match perk

            finalWeaponList.append("\n".join(doublePerks))
            #finalWeaponList.append("\n".join(singlePerks))

        #finalWeaponList.append("\n")

        #finalWeaponList.append("\n//double perks")
        #finalWeaponList.append("\n".join(doublePerks))
        #finalWeaponList.append("\n//single perks")
        #finalWeaponList.append("\n".join(singlePerks))

        self.outputTextBox.setText("\n".join(finalWeaponList))

    def LoadWishlist(self):
        print("connecting to API")

        client_id = ""
        client_secret = "67f37821d1974250b2fc2a9fbf26ed27"

        oauth = OAuth2Session(client_id)

        token = oauth.fetch_token("https://www.bungie.net/Platform/App/OAuth/token/", client_secret=client_secret)
        print("token:", token)

        #https://www.bungie.net/en/oauth/authorize?client_id=67f37821d1974250b2fc2a9fbf26ed27&response_type=code&state=goopygoober

        #resp = oauth.get("url to the resource")
        resp = oauth.get("https://www.bungie.net/en/oauth/authorize?client_id=67f37821d1974250b2fc2a9fbf26ed27&response_type=code&state=goopygoober")
