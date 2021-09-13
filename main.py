"""Ohjelman tarkoituksena on muuttaa tiettyjä kahden API:n xml-data JSON-tiedostoon, 
jossa data on esitetty vertailuarvoina"""
#Version: 3.9.5

#API:n osoitteet
def getAPIkeys():
    with open("keyfile.ini", 'r') as keyfile:
        keys = keyfile.read()
        keys = keys.split(" ")
        return keys

keys=getAPIkeys()

city = "Tampere"

provider1 = "openweathermap"
requestProvider1 = "https://api.openweathermap.org/data/2.5/weather?q={}&units=metric&mode=xml&{}".format(city,keys[0])

provider2 = "HERE"
requestProvider2 = "https://weather.cc.api.here.com/weather/1.0/report.xml?oneobservation=true&product=observation&{}&product=observation&name={}".format(keys[1],city)


outputfile = "comparison.json"
#Koodi

import requests
import xml.etree.ElementTree as ET
import time
import datetime
import json



def getTimeZone():  #Määritä kuinka monta tuntia edellä suomi on GMT:stä (määritä onko Suomi kesä vai talviajassa)
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    hours = offset / 60 / 60 * -1
    hours = int(hours)
    return hours

def adjustTime(time): #Muuta GMT -aika Suomen aikaan ISO-standardin mukaisesti
    f = time.replace("T", " ")
    dif = getTimeZone()
    convertedTime = datetime.datetime.strptime(f, '%Y-%m-%d %H:%M:%S')
    adjustedTime = convertedTime + datetime.timedelta(hours = dif)
    adjustedTime = str(adjustedTime).replace(" ", "T")
    adjustedTime = ''.join((adjustedTime,"+0{}:00".format(dif)))
    return adjustedTime


def requestAPI(address): #Pyydä API:ltä XML-dataa
    attempts = 0 #Tietty määrä yrityksiä vastata ennen kuin ajo keskeytetään
    while attempts < 3:
        try:
            resp = requests.get(address) 
            attempts = 3
            return resp
        except requests.exceptions.InvalidSchema as HE:
            attempts += 1
            print("{}, kelvoton osoite.".format(HE))
        except requests.ConnectionError as CE:
            attempts += 1
            print("{}, ei saada yhteyttä ohjelmointirajapintaan.".format(CE))
    else:
        input("Paina ENTER lopettaaksesi ")
        exit() 

def findChildren(response): #Etsi XML-puusta tietyt arvot
    varList = []
    xml_string = response.content
    tree = ET.fromstring(xml_string) #Tee API:n vastauksesta xml-puu
    for root in tree.iter():    #Etsi xml:n kaikki keyt
        #Lisää säähavaintojen aika
        for children in root.findall("lastupdate"):
            if children == None:
                pass
            else:
                temp = children.attrib["value"]
                temp = adjustTime(temp)
                varList.append(temp)
        for children in root.findall("observation"):
            temp = children.attrib["utcTime"]
            varList.append(temp)
        #Etsi molemmista puista lämpötilaa vastaavat arvot
        for children in root.findall("temperature"):
            if children.text == None:
                temp = children.attrib["value"]
                varList.append(temp)
            else:
                varList.append(children.text)
        #Etsi molemmista puista kosteus% vastaavat arvot
        for children in root.findall("humidity"):
            if children.text == None:
                temp = children.attrib["value"]
                varList.append(temp)
            else:
                varList.append(children.text)
        #Etsi molemmista puista taivasta kuvaavat merkinnät.
        for children in root.findall("weather"):
            if children == None:
                pass
            else:
                temp = children.attrib["value"]
                varList.append(temp)
        for children in root.findall("skyDescription"):
            if children == None:
                continue
            else:
                varList.append(children.text)
    return varList

def createJSON(val1, val2): #Luo JSON vertailuarvoille
    data = {}
    data['Comparison'] = []
    data['Comparison'].append({
        'Provider': provider1,
        'City': city,
        'Time': val1[0],
        'Temperature': val1[1],
        'Humidity': val1[2],
        'SkyDesc': val1[3]
    })
    data['Comparison'].append({
        'Provider': provider2,
        'City': city,
        'Time': val2[0],
        'Temperature': val2[1],
        'Humidity': val2[2],
        'SkyDesc': val2[3]
    })

    with open(outputfile, 'w') as outfile: #Luo JSON ja kirjoita siihen ylempänä olevat määritteet
        json.dump(data, outfile, indent=4)


def ready():
    print("Säätiedot kirjoitettu tiedostoon {}".format(outputfile))
    input("Paina ENTER lopettaaksesi ")
    exit() 

if __name__ == "__main__": #Suorita funktiot
    resp1 = requestAPI(requestProvider1)
    resp2 = requestAPI(requestProvider2)
    values1 = findChildren(resp1)
    values2 = findChildren(resp2)
    createJSON(values1, values2)
    ready()


