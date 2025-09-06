from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QTextEdit,
    QLabel
)

# from pathlib import Path

# import unicodedata

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from unidecode import unidecode

import requests
import shutil
import zipfile
import sqlite3
import json

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

class MainWindow(QMainWindow):
    spreadSheetWeaponTypes = [
        #Special
        "Shotguns",
        "Snipers",
        "Fusions",
        "BGLs",
        "Glaives",
        "Traces",
        "Rocket Sidearms",
        #Heavy
        "LMGs",
        "HGLs",
        "Swords",
        "Rockets",
        "LFRs",
        #Primary
        "Autos",
        "Bows",
        "HCs",
        "Pulses",
        "Scouts",
        "Sidearms",
        "SMGs",
        "Other"
        ]

    aegisSpreadsheetID = "1JM-0SlxVDAi-C6rGVlLxa-J1WGewEeL8Qvq4htWZHhY"
    aegisSpreadsheetData = {}
    bestWeapons = []

    GoogleCredentials = None

    baseURL = "https://www.bungie.net"
    APIKey = ""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("DIM Wishlist Generator")

        # global holder
        mainLayout = QVBoxLayout()

        # top third
        topLayout = QHBoxLayout()

        # middle third
        bodyLayout = QHBoxLayout()
        leftLayout = QVBoxLayout()
        self.middleLayout = QVBoxLayout()
        rightLayout = QVBoxLayout()

        # bottom third
        bottomLayout = QHBoxLayout()

        ##### Top Layout #####
        mainLayout.addLayout(topLayout)
        connectToGoogle = QPushButton("Connect to Google")
        topLayout.addWidget(connectToGoogle)

        aegisSheet = QPushButton("Aegis Sheet")
        topLayout.addWidget(aegisSheet)

        getManifest = QPushButton("Get Destiny Manifest")
        topLayout.addWidget(getManifest)
        
        getBestWeapons = QPushButton("Get Best Weapons")
        topLayout.addWidget(getBestWeapons)

        ##### Body #####
        mainLayout.addLayout(bodyLayout)

        ##### Body - Left Layout #####
        bodyLayout.addLayout(leftLayout, 20)

        leftLayout.addWidget(QLabel("Every Weapon"))
        self.allWeaponsTextBox = QTextEdit()
        leftLayout.addWidget(self.allWeaponsTextBox, 100)

        ##### Body - Middle Layout #####
        bodyLayout.addLayout(self.middleLayout, 40)
        self.middleLayout.addWidget(QLabel("Best Weapons"))
        self.bestWeaponsTextBox = QTextEdit()
        self.middleLayout.addWidget(self.bestWeaponsTextBox)

        ##### Body - Right Layout #####
        bodyLayout.addLayout(rightLayout, 40)
        rightLayout.addWidget(QLabel("Dim Wishlist"))
        self.dimTextBox = QTextEdit()
        rightLayout.addWidget(self.dimTextBox)

        ##### Bottom Layout #####
        mainLayout.addLayout(bottomLayout)
        
        exportWishlist = QPushButton("Export Wishlist")
        bottomLayout.addWidget(exportWishlist)

        #Create Central Widget
        mainWidget = QWidget()
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

        #Get Data
        # get manifest
        self.GetDestinyManifest()
        # connect to google
        self.ConnectToGoogle()
        # check and copy aegis sheet
        self.AegisSheet()
        # get best weapons
        self.GetBestWeapons()
        # generate dim
        self.GenerateDimWishlist()
        # output to text
        # push to git

    def GetDestinyManifest(self):
        print("connecting to API")

        self.headers = {"X-API-Key":self.APIKey}

        #get current manifest
        manifest_url = self.baseURL+"/Platform/Destiny2/Manifest"
        r = requests.get(manifest_url, headers=self.headers)
        manifest = r.json()

        print("Checking for manifest")
        #if we already have a Res folder, get the newest manifest and check it with our existing manifest
        if os.path.isdir("Res"):
            print("Manifest exists!")

            with open("Res/ManifestData", "r") as manifestData:
                currentManifestName = manifestData.readline()

            newManifestName = str(manifest["Response"]["mobileWorldContentPaths"]["en"]).split("/").pop()

            print("Checking versions: \ncur:" + currentManifestName, "\nnew:"+newManifestName)

            if currentManifestName != newManifestName:
                print("Manifest mismatch, getting newer manifest")
                #clear Res folder
                shutil.rmtree("Res")
                os.mkdir("Res")
                self.DownloadManifest(self.baseURL+manifest['Response']['mobileWorldContentPaths']['en'])
            else:
                print("Manifest version is up to date, checking for pickle")
                self.CheckForPickle()
        else:
            print("No manifest, downloading!")
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

    def CheckForPickle(self):
        hash_dict = [
            "DestinyInventoryItemDefinition"]

        print("checking for pickle")
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

            for table_name in hash_dict:
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

        print("all done")

    def ConnectToGoogle(self):
        print("Connecting to google!")

        if os.path.exists("googleToken.json"):
            self.GoogleCredentials = Credentials.from_authorized_user_file("googleToken.json", SCOPES)

        if not self.GoogleCredentials or not self.GoogleCredentials.valid:
            if self.GoogleCredentials and self.GoogleCredentials.expired and self.GoogleCredentials.refresh_token:
                try:
                    self.GoogleCredentials.refresh(Request()) 
                except:
                    print("token expired, regetting")
                    os.remove("googleToken.json")
                    self.ConnectToGoogle()
                    return
            else:
                flow = InstalledAppFlow.from_client_secrets_file("googleCredentials.json", SCOPES)
                self.GoogleCredentials = flow.run_local_server(port=0)

            with open("googleToken.json", "w") as token:
                token.write(self.GoogleCredentials.to_json())

        print("authenticated!")

    def AegisSheet(self):
        print("Copying Aegis Sheet")

        try:
            service = build("sheets", "v4", credentials=self.GoogleCredentials)
            sheet = service.spreadsheets()

            result = (
                sheet.get(spreadsheetId=self.aegisSpreadsheetID, ranges=[i+"!B3:N" for i in self.spreadSheetWeaponTypes], includeGridData=True).execute()
            )

            values = result.get("sheets", [])

            if not values:
                print("no data found")
                return


            # regular weapons - NAME, ELEMENT, FRAME, PERK1, PERK2, ORIGIN, INDEX
            [self.AegisSheetWeaponType(sheet, 0, 2, 3, 6, 7, 8, 10) for sheet in [filteredWeaponTypes for filteredWeaponTypes in values if filteredWeaponTypes["properties"]["title"] not in ["Glaives", "Rocket Sidearms", "Traces", "Swords", "Other"]]]

            # special cases - because aegis is a freak and makes his shees non-standard
            
            # glaive
            [self.AegisSheetWeaponType(sheet, 0, 2, 3, 7, 8, 9, 11) for sheet in [filteredWeaponTypes for filteredWeaponTypes in values if filteredWeaponTypes["properties"]["title"] == "Glaives"]]
            
            # rocket sidearm
            [self.AegisSheetWeaponType(sheet, 0, 2, -1, 5, 6, 7, 9) for sheet in [filteredWeaponTypes for filteredWeaponTypes in values if filteredWeaponTypes["properties"]["title"] == "Rocket Sidearms"]]
            
            # traces
            [self.AegisSheetWeaponType(sheet, 0, 2, -1, 5, 6, 7, 9) for sheet in [filteredWeaponTypes for filteredWeaponTypes in values if filteredWeaponTypes["properties"]["title"] == "Traces"]]
            
            # sword
            [self.AegisSheetWeaponType(sheet, 0, 2, 3, 7, 8, 9, 11) for sheet in [filteredWeaponTypes for filteredWeaponTypes in values if filteredWeaponTypes["properties"]["title"] == "Swords"]]
            
            # other
            [self.AegisSheetWeaponType(sheet, 0, 2, 3, 6, 7, 8, -1) for sheet in [filteredWeaponTypes for filteredWeaponTypes in values if filteredWeaponTypes["properties"]["title"] == "Other"]]

            [[self.allWeaponsTextBox.append(weapon[0]) for weapon in self.aegisSpreadsheetData[category]] for category in self.aegisSpreadsheetData]

        except HttpError as err:
            print(err)

    def AegisSheetWeaponType(self, sheet, nameIndex, energyIndex, frameIndex, perk1Index, perk2Index, originIndex, rankIndex):
        print("Generating data for:", sheet["properties"]["title"])
        
        rowData = sheet["data"][0]["rowData"]
        
        weaponNames = [rowData[itemIndex]["values"][nameIndex]["formattedValue"] if nameIndex != -1 else "?"  for itemIndex in range(len(rowData))]
        weaponEnergy = [rowData[itemIndex]["values"][energyIndex]["formattedValue"] if energyIndex != -1 else "?"  for itemIndex in range(len(rowData))]
        weaponFrame = [rowData[itemIndex]["values"][frameIndex]["formattedValue"] if frameIndex != -1 else "?"  for itemIndex in range(len(rowData))]
        weaponPerk1 = [rowData[itemIndex]["values"][perk1Index]["formattedValue"] if perk1Index != -1 else "?"  for itemIndex in range(len(rowData))]
        weaponPerk2 = [rowData[itemIndex]["values"][perk2Index]["formattedValue"] if perk2Index != -1 else "?"  for itemIndex in range(len(rowData))]
        weaponOrigin = [rowData[itemIndex]["values"][originIndex]["formattedValue"] if originIndex != -1 else "?"  for itemIndex in range(len(rowData))]
        weaponRank = [rowData[itemIndex]["values"][rankIndex]["formattedValue"] if rankIndex != -1 else "?" for itemIndex in range(len(rowData))]

        self.aegisSpreadsheetData[sheet["properties"]["title"]] = [(weaponNames[index], weaponEnergy[index], weaponFrame[index], weaponPerk1[index], weaponPerk2[index], weaponOrigin[index], weaponRank[index]) for index in range(len(rowData))]

    def GetBestWeapons(self):
        print("getting best weapons")

        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Autos"], ["Support"], inverse=True) # non support autos
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Autos"], ["Support"]) # support autos

        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["HCs"], ["Heavy Burst", "Spread Shot"], inverse=True) # non heavy burst & spread shot HCs
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["HCs"], ["Spread Shot"]) # spread shot HCs
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["HCs"], ["Heavy Burst"]) # heavy burst HCs

        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Bows"], [""], inverse=True)
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Pulses"], [""], inverse=True)
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Scouts"], [""], inverse=True)
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Sidearms"], [""], inverse=True)
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["SMGs"], [""], inverse=True)
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Glaives"], [""], inverse=True)
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Rocket Sidearms"], [""], inverse=True)
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Traces"], [""], inverse=True)
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["LFRs"], [""], inverse=True)
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["LMGs"], [""], inverse=True)
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Rockets"], [""], inverse=True)
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Swords"], [""], inverse=True)

        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["BGLs"], ["Area Denial"]) # area denial BGLs
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["BGLs"], ["Wave"]) # wave BGLs
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["BGLs"], ["Area Denial", "Wave"], inverse=True) # all other BGLs
        
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Fusions"], ["Rapid"]) # only rapidfire fusions

        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Shotguns"], ["Pinpoint Slug", "Heavy Burst", "Rapid Slug"]) # slug shotguns
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Shotguns"], ["Pinpoint Slug", "Heavy Burst", "Rapid Slug"], inverse=True) # non slug shotguns

        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Snipers"], ["Aggressive"]) # rapid Snipers
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Snipers"], ["Rapid"]) # aggressive Snipers

        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["HGLs"], ["Compressed Wave"]) # compressed wave HGLs
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["HGLs"], ["Compressed Wave"], inverse=True) # normal HGLs
        
        self.GetBestWeaponsFromCategory(self.aegisSpreadsheetData["Other"], [""], inverse=True) # other weapons

        [self.bestWeaponsTextBox.append(str(weapon[0])) for weapon in self.bestWeapons]

    def GetBestWeaponsFromCategory(self, category, frameFilter, inverse=False):
        filteredWeaponsInCategory = [weapon for weapon in category if (weapon[2] in frameFilter) != inverse]

        bestInCategory = []

        bestInCategory.append(next((weapon for weapon in filteredWeaponsInCategory if weapon[1] in "Solar"), None))
        bestInCategory.append(next((weapon for weapon in filteredWeaponsInCategory if weapon[1] in "Arc"), None))
        bestInCategory.append(next((weapon for weapon in filteredWeaponsInCategory if weapon[1] in "Void"), None))

        bestInCategory.append(next((weapon for weapon in filteredWeaponsInCategory if weapon[1] in "Kinetic"), None))
        bestInCategory.append(next((weapon for weapon in filteredWeaponsInCategory if weapon[1] in "Stasis"), None))
        bestInCategory.append(next((weapon for weapon in filteredWeaponsInCategory if weapon[1] in "Strand"), None))

        [self.bestWeapons.append(weapon) for weapon in bestInCategory if weapon is not None]

    def GenerateDimWishlist(self):
        print("Generating DIM Wishlist")

        self.weapon_dict = {}
        self.perks_dict = {}

        for itemHash in self.all_data["DestinyInventoryItemDefinition"]:
            if self.all_data["DestinyInventoryItemDefinition"][itemHash]["itemType"] == 3: # itemtype 3 == weapon
                self.weapon_dict[itemHash] = self.all_data["DestinyInventoryItemDefinition"][itemHash]["displayProperties"]["name"]

            if "itemTypeDisplayName" in self.all_data["DestinyInventoryItemDefinition"][itemHash] and self.all_data["DestinyInventoryItemDefinition"][itemHash]["itemTypeDisplayName"] == "Trait":
                self.perks_dict[itemHash] = self.all_data["DestinyInventoryItemDefinition"][itemHash]["displayProperties"]["name"]
        
        for weapon in self.bestWeapons:
            perk1Hashes = [(hash, perkData) for hash, perkData in self.perks_dict.items() if perkData in str.split(weapon[3], "\n")]
            perk2Hashes = [(hash, perkData) for hash, perkData in self.perks_dict.items() if perkData in str.split(weapon[4], "\n")]
            weaponHashes = [(hash, weaponDict) for hash, weaponDict in self.weapon_dict.items() if str.split(str.lower(weapon[0]), "\n")[0] in str.lower(unidecode(weaponDict))]

            combinedWeapon = {hash: ([perk1[0] for perk1 in perk1Hashes], [perk2[0] for perk2 in perk2Hashes]) for hash, weapon in weaponHashes}

            for out in [(hash, combinedWeapon[hash]) for hash in [hash for hash in combinedWeapon]]:
                for perk1 in out[1][0]:
                    for perk2 in out[1][1]:
                        self.dimTextBox.append("dimwishlist:item=" + str(out[0]) + "&perks=" + str(perk1) + "," + str(perk2))

                #for perk1 in out[1][0]:
                    #self.dimTextBox.append("dimwishlist:item=" + str(out[0]) + "&perks=" + str(perk1))
                
                #for perk2 in out[1][1]:
                    #self.dimTextBox.append("dimwishlist:item=" + str(out[0]) + "&perks=" + str(perk2))



    def ExportWishlist(self):
        print("Exporting Wishlist to txt")