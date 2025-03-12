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

from ItemSlot import ItemSlot
from WeaponDisplay import WeaponDisplay

class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.baseURL = "https://www.bungie.net"
        self.APIKey = ""
        self.setWindowTitle("DIM Wishlist Generator")

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

        for item in inputList:
            outputs = [key for key, value in self.weapon_dict.items() if value == item]
            outputList.extend(list(map(str,outputs)))

        outputListString = "dimwishlist:item="+"\ndimwishlist:item=".join(outputList)

        self.outputTextBox.setText(outputListString)