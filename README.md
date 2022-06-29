# Air Aberdeen Data Stack 
An expirement in creating a compute and data analytics stack for Air Aberdeen data so that some of the data can be analysed more effectively. This part generates a JSON file of data from air quality sensors, which is then read by a front-end application for the visualisations.

## Background
This approach started from this article 
https://towardsdatascience.com/how-to-build-a-modern-data-stack-for-free-e1e983963062 so that we could work with the air aberdeen devices as started from the CTC16 Data Gathering repo to pull data from Luftdaten sources
https://github.com/AirAberdeen/CTC16-Data-Gathering 

    pip install beautifulsoup4
    pip install requests
    pip install python-dateutils

### Run this yourself
You can run this locally to generate data from other air quality sensors.
Run get_luftdaten_data.py file to generate JSON file. Modify the settings to grab your sensors.
Modify the link in the index.html page to point to ./data/bq_data.json to show that data.
Start flask server and then read JSON from link on landing page.

## This pulls data from air quality sensors daily
The get_luftdaten_data.py file generates a JSON file of readings. It is run each day, which means the old data is lost as the file is overwritten.

The workflow/schedule.yml file is scheduled to be run each day at 06:05 if the scheduler is set up correctly, and thus refresh the bq_data.json file.

### This data is consumed by another site
The site at http://echo-air-sensor.herokuapp.com consumes this data and provides visualisations.

