from bs4 import BeautifulSoup
import os.path
import pprint
import shutil
import requests
import sys
from datetime import datetime, tzinfo, timezone, date, timedelta
import os
import argparse
import csv
import json
import glob
from dateutil import parser

sensorvalues = ['P1', 'durP1', 'ratioP1', 'P2', 'durP2', 'ratioP2',
                'humidity', 'temperature', 'pressure', 'pressure_at_sealevel']
del_vals = ['altitude', 'durP1', 'ratioP1', 'durP2',
            'ratioP2', 'pressure_sealevel', 'lon', 'lat', 'location']

file_directory = './data/big_dump/'
bq_directory = './data/'

# use this to hold value of readings to convert to JSON file at end
sensor_readings = list()

# use this to fill list of objects for JSON file
class Reading:
    def __init__(self, location_id, longitude, latitude, sensor_id, sensor_type, humidity, temperature,  P1, P2, timestamp, pressure):
        self.location_id = location_id
        self.longitude = longitude
        self.latitude = latitude
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.humidity = humidity
        self.temperature = temperature
        self.P1 = P1
        self.P2 = P2
        self.pressure = pressure
        self.timestamp = timestamp
    
    def toJson(self):
        return json.dumps(self, default=lambda o:o.__dict__)

def get_historic_data(current_data, start_date):
    # Download data for each sensor.
    # start from 48hrs before today and workbackwards
    start_date = start_date - timedelta(days=2)

    for sensor in current_data:
        point_date = start_date
        # sensor flag is true until either:
        # 1. file already exits
        # 2. file cannot be downloaded (i.e. doesn't exists on server)
        sensor_flag = True
        while (sensor_flag == True):
            # construct file name
            str_date = point_date.isoformat()
            filename = str_date + '_' + sensor['sensor']['sensor_type']['name'].lower(
            ) + '_sensor_' + str(sensor['sensor']['id'])+'.csv'
            full_link = 'http://archive.luftdaten.info/' + str_date + '/' + filename

            # check if file has already been downloaded
            # if (os.path.isfile(file_directory +'done/'+ filename)):
            with open(file_directory + 'list.txt', 'r') as f:

                if (filename in f.read()):
                    # file exists, skip
                    sensor_flag = False
                else:
                    # file does not exist. Proceed to try download.
                    sensor_flag = downloader(full_link, filename)
            # point_date moves back a day
            for x in range(7):
                point_date = point_date - timedelta(days=1)
            sensor_flag = False
            # open file to clean it for the next run
            f = open(file_directory + 'list.txt', 'w')
            f.close()

def downloader(full_link, name):
    fname = file_directory + name
    try:
        r = requests.get(full_link)
        r.raise_for_status()
    except:
        print('  ', name, 'ERROR: Could not download file')
        return(False)

    else:
        # Save the string to a file
        r = requests.get(full_link, stream=True)
        with open(fname, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
        print('  ', name, '- complete')
        return(True)


def get_data(box):
    # gets luftdaten details for all sensors within a given lat/log box
    # box = 'lat_0,long_0,lat_1,long_1'
    r = requests.get('https://api.luftdaten.info/v1/filter/box=' + box)
    my_json = r.json()
    return my_json

def bq_json():
    outfilename = "./data/bq_data.json"
    with open(outfilename, "w") as outfile:
        outfile.write("[")
        print("opened bq_data file")
        for reading in sensor_readings:
            tmpjson = reading.toJson()
           # print('tmpjson: ', tmpjson)
            outfile.write(tmpjson)
            outfile.write(",")
        # remove last ',' from end of file, then close bracket to complete JSON file
        outfile.seek(0, os.SEEK_END)
        outfile.seek(outfile.tell() -1, os.SEEK_SET)
        outfile.truncate()
        outfile.write("]")
    print("closed json")

def MrParsy():
    format = "pretty"
    input_directory = file_directory
    if ((input_directory[-1:] != '\\') & (input_directory[-1:] != '/')):
        input_directory = input_directory + "\\"
    file_list = glob.iglob(input_directory + '*.csv')
    for input_file in file_list:
        print("Parsing next file...", input_file)
        read_csv(input_file, input_directory, format)


def read_csv(file, json_file, format):
    csv_rows = []
    with open(file) as csvfile:
        dictionary = csv.DictReader(csvfile, delimiter=";")
        title = dictionary.fieldnames
        for row in dictionary:
            csv_rows.extend([{title[i]:row[title[i]]
                              for i in range(len(title))}])
        tidy_dict = tidy_values(csv_rows)
        # pp = pprint.PrettyPrinter(indent=1)
        # pp.pprint(tidy_dict)
    write_json(tidy_dict, json_file, format)
    newfile = file.replace("./data/big_dump", "./data/big_dump/done")
    print(file, newfile)
    os.rename(file, newfile)


def write_json(data, json_file, format):

    location_id = list(data.keys())[0]
    d = {}
    if (os.path.isfile(json_file + location_id + '.json')):
        with open(json_file + location_id + '.json', "r") as f:
            d = json.load(f)

            d[location_id]['info'].update(
                data[location_id]['info']
            )
            for timestamp in data[location_id]['readings']:

                if (str(timestamp) in d[location_id]['readings']):
                    d[location_id]['readings'][str(timestamp)].update(
                        data[location_id]['readings'][timestamp])
                else:
                    d[location_id]['readings'].update(
                        {str(timestamp): data[location_id]['readings'][timestamp]})

        with open(json_file + location_id + '.json', "w") as f:
            if format == "pretty":
                f.write(json.dumps(d, sort_keys=True, indent=4))
            else:
                f.write(json.dumps(d))
            print(json_file + location_id + '.json' + " - updated")
    else:
        with open(json_file + location_id + '.json', "w") as f:
            d[location_id] = data[location_id]
            if format == "pretty":
                f.write(json.dumps(d, sort_keys=True, indent=4))
            else:
                f.write(json.dumps(d))
            print(json_file + location_id + '.json' + " - created")


def infolist():
    summary = {}
    file_list = glob.iglob(file_directory + '*.json')
    for input_file in file_list:
        if not(input_file[-9:] == 'info.json'):
            with open(input_file, "r") as f:
                d = json.load(f)
                location_id_temp = list(d.keys())[0]
                summary[location_id_temp] = {}
                summary[location_id_temp]['info'] = d[location_id_temp]['info']
    with open(file_directory + 'info.json', "w") as f:
        f.write(json.dumps(summary, sort_keys=True, indent=4))
        print(file_directory + 'info.json' + " - created")


def tidy_values(our_list):
    # add steps here to build data for bq
    # create item to build each entry
    bq_info = {}
    bq_reading = {}

    # organises our_list as a dictionary of dictionaries follows:
    new_dict = {}
    location_id = str(our_list[0]['location'])
    reading = our_list[0]
    if (new_dict.get(location_id, None) == None):
        new_dict[location_id] = {}
        new_dict[location_id]['info'] = {
            'latitude': reading['lat'],
            'longitude': reading['lon'],
            'location_id': location_id
        }
        new_dict[location_id]['readings'] = {}
        for option in sensorvalues:
            if (option in reading):
                if (reading[option]):
                    new_dict[location_id]['info'].update({
                        option: {
                            reading['sensor_type']: reading['sensor_id'],
                        }
                    })
    bq_info = new_dict[location_id]['info']
    # strip out unrequired values from dict
    for reading in our_list:
        for key in del_vals:
            if key in reading.keys():
                del reading[key]
        reading_ts = reading['timestamp']
        if reading_ts.find('+') < 0:
            # adds timezone if none given.
            # this is required for timestamp calculation below
            reading_ts = reading_ts + '+00:00'
            reading_ts = parser.parse(reading_ts)
        timestamp = int(
            (reading_ts - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds())
        timestamp = timestamp // 360 * 360  # round to nearest minute
        bq_reading = reading
        bq_info.update(bq_reading)

        # map item to sensor_reading object and add to list
        # add empty values to bq_info for reading constructor
        if (bq_info.get('humidity', None) == None):
            bq_info['humidity'] = '0.0'
        if (bq_info.get('temperature', None) == None):
            bq_info['temperature'] = '0.0'
        if (bq_info.get('pressure', None) == None):
            bq_info['pressure'] = '0.0'
        if (bq_info.get('P1', None) == None):
            bq_info['P1'] = '0.0'
        if (bq_info.get('P2', None) == None):
            bq_info['P2'] = '0.0'
        # print("bq_info-tidy: ", bq_info)
        location_id = bq_info['location_id']
        longitude = bq_info['longitude']
        latitude = bq_info['latitude']
        sensor_id = bq_info['sensor_id']
        sensor_type = bq_info['sensor_type']
        humidity = bq_info['humidity']
        temperature = bq_info['temperature']
        p1= bq_info['P1']
        p2= bq_info['P2']
        timestamp = bq_info['timestamp']
        pressure = bq_info['pressure']

        a_reading = Reading(location_id, longitude, latitude, sensor_id, sensor_type, humidity, temperature, p1, p2, timestamp, pressure)
        sensor_readings.append(a_reading)

        new_dict[location_id]['readings'][timestamp] = {}
        for option in sensorvalues:
            if (option in reading):
                if (reading[option]):
                    new_dict[location_id]['readings'][timestamp].update({
                        option: float(reading[option])
                    })

    return(new_dict)

def cleanUpCSVs():
    input_directory = file_directory
    if ((input_directory[-1:] != '\\') & (input_directory[-1:] != '/')):
        input_directory = input_directory + "\\"
    file_list = glob.iglob(input_directory+'/done/' + '*.csv')
    for input_file in file_list:
        with open(file_directory + 'list.txt', "a") as f:
            f.write(input_file[22:] + "\n")
            os.remove(input_file)
        print("recored & deleted", input_file)

def main():
    # These are pre-defined boxes for searching
    Aberdeen = [57.25, -2.40, 57.00, -2.00]
#	Aberdeenshire = [57.75, -4.00, 56.74, -1.70]
#	WesternEurope = [60, -10, 40, 20]

    # select a box to use for the search
    box = Aberdeen
    # stringify box array for use in API
    strbox = (str(box)[1:-1]).replace(" ", "")

    # Get current sensor data from luftdaten.
    print()
    print('Searching for current sensors in area...', strbox)
    current_data = get_data(strbox)
    print('Number of sensors found = ', len(current_data))

    # Pull out sensor IDs
    sensor_list = []
    for device in current_data:
        sensor_list.append(device['sensor']['id'])
    print("Looking for the following sensors:", sensor_list)

    # Get historic data for above sensors
    # Works backwards from today
    todays_date = date.today()
    print(f"Today is: {todays_date}")
    print('Getting historic data for sensors from', todays_date)
    get_historic_data(current_data, todays_date)

    # Parse new data into JSON
    print('Parsing data to JSON')
    MrParsy()
    print('Building summary file...')
    infolist()
    print('Removing csvs')
    cleanUpCSVs()
    bq_json()
    print("done and leaving the building")
    sys.exit()

    # weather_data = get_weather.main(box)
    # pp = pprint.PrettyPrinter(indent=1)
    # pp.pprint (current_data)
    # pp.pprint (weather_data)

    return ()


if __name__ == '__main__':
    main()
