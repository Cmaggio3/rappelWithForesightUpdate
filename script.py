import time
import urllib.request, json
import statistics
#import matplotlib.pyplot as plt
import datetime
import xlsxwriter
import statistics
import requests
import json
import datetime
import dateutil.relativedelta

def populateWeatherData(appid):

    headers = {'content-type':'application/json'}
    API_ENDPOINT = "https://rappelwithforesightapi.herokuapp.com/locations"

    r = requests.get(url = API_ENDPOINT, headers=headers)
    workingData = r.json()

    for locationIndex, location in enumerate(workingData):
        danger = False
        caution = False
        lat = location["Latitude"]
        lng = location["Longitude"]


        #weatherapi
        url = "https://api.openweathermap.org/data/2.5/weather?"\
              +"lat="+str(lat)\
              +"&lon="+str(lng)\
              +"&appid="+appid

        #get weather
        with urllib.request.urlopen(url) as url:
            data = json.loads(url.read().decode())
        weatherId = data["weather"][0]["id"]
        weatherDesc = data["weather"][0]["description"]

        #weather is mildly bad
        if((weatherId >= 200 and weatherId < 300)\
           or (weatherId >=600 and weatherId < 700)\
           or weatherId == 701\
           or weatherId == 721\
           or weatherId == 731\
           or weatherId == 741):

            caution = True

        #weather is bad
        if((weatherId >= 300 and weatherId < 400)\
           or (weatherId >=500 and weatherId < 600)\
           or weatherId == 711\
           or weatherId == 751\
           or weatherId == 761\
           or weatherId == 762\
           or weatherId == 771\
           or weatherId == 781):

            danger = True

        workingData[locationIndex]["Weather"] = weatherDesc
        API_ENDPOINT = "https://rappelwithforesightapi.herokuapp.com/locations"
        #data = workingData[locationIndex]
        dataSubmit = {"LocationId":workingData[locationIndex]["LocationId"],"Weather":weatherDesc}
        r = requests.post(url = API_ENDPOINT, data = json.dumps(dataSubmit), headers=headers)




def populateGaugeData(radius,threshold,months):

    headers = {'content-type':'application/json'}
    API_ENDPOINT = "https://rappelwithforesightapi.herokuapp.com/locations"

    r = requests.get(url = API_ENDPOINT, headers=headers)
    workingData = r.json()

    total = 0;
    values=[]

    risingArray = []
    highArray = []

    previousVal = 0

    aArray = [0,0,0,0,0,0,0,0,0,0]

    allValues = []
    valueAverage = 0

    months = months * -1

    endDate = datetime.datetime.now().date()
    startDate = str(endDate + dateutil.relativedelta.relativedelta(months=months))
    endDate = str(endDate)

    for locationIndex, location in enumerate(workingData):
        lat = location["Latitude"]
        lng = location["Longitude"]

        url = "https://waterservices.usgs.gov/nwis/iv/?format=json&indent=on&bBox="\
                  +str(float(lng-radius))+","\
                  +str(float(lat-radius))+","\
                  +str(float(lng+radius))+","\
                  +str(float(lat+radius))+"&startDT="\
                  +startDate+"&endDT="+endDate+"&parameterCd=00060,00065&siteStatus=all"

        nearbyGauges = 0

        with urllib.request.urlopen(url) as url:
            data = json.loads(url.read().decode())

        #for each gauge
        for iindex, i in enumerate(data["value"]["timeSeries"]):
            #gather all values for this gauge
            for jindex, j in enumerate(i['values'][0]['value']):
                curVal = int(float(j['value']))
                if (curVal > -1):
                    allValues.append(curVal)
                    aArray[jindex%10] = curVal
            #if this gauge has enough values get the average value and stdev
            if (len(allValues) > 2):
                valueAverage = sum(allValues)/len(allValues)
                stdev = statistics.stdev(allValues)
                #if the average and stdev are reasonable
                if (valueAverage > 10 and stdev > 2):
                    #if this gauge is currently much higher than average
                    recentVal = float(i['values'][0]['value'][0]['value'])
                    if (recentVal > valueAverage+stdev):
                        #log this gauge as high
                        highArray.append(1)
                    else:
                        #log this gauge as low
                        highArray.append(0)
                    if (recentVal > (sum(aArray)/float(len(aArray)))*1.05):
                        risingArray.append(1)
                    else:
                        risingArray.append(0)
            allValues = []
        averageHigh = sum(highArray)/len(highArray)
        averageRising = sum(risingArray)/len(risingArray)
        print("This location has "+str(averageHigh)+" of gauges high")
        print("this location has "+str(averageRising)+" of gauges rising")
        danger = 0
        if(averageHigh > .25):
            danger += 2
        if(averageRising > .75):
            danger += 1
        
        API_ENDPOINT = "https://rappelwithforesightapi.herokuapp.com/locations"
        dataSubmit = {"LocationId":workingData[locationIndex]["LocationId"],\
                      "Danger":danger}
        r = requests.post(url = API_ENDPOINT, data = json.dumps(dataSubmit), headers=headers)



count = 0
while 1:
    time.sleep(60*60)
    count += 1
    print("populating weather")
    populateWeatherData("7e6f01af1e22a22c27c3ddeadd242517")
    if(count == 6):
        print("populating gauge")
        populateGaugeData(.5,.25,2)
        count = 0
