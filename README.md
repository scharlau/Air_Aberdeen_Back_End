# Air Aberdeen Data Stack 
An expirement in creating a compute and data analytics stack for Air Aberdeen data so that some of the data can be analysed more effectively. This part generates a JSON file of data from air quality sensors, which is then read by a front-end application for the visualisations.

## Background
This approach started from this article 
https://towardsdatascience.com/how-to-build-a-modern-data-stack-for-free-e1e983963062 so that we could work with the air aberdeen devices as started from the CTC16 Data Gathering repo to pull data from Luftdaten sources
https://github.com/AirAberdeen/CTC16-Data-Gathering 

    pip install beautifulsoup4
    pip install requests
    pip install python-dateutils


This is the basic version at the moment.
This generates a JSON file of readings.
The file is not as large as previously, so something is not being read. Howevever, it provides a starting point.

The workflow/schedule.yml file 'should' be run each day at 06:05 if the scheduler is set up correctly, and thus refresh the bq_data.json file.

Run get_luftdaten_data.py file to generate JSON file.
Start flask server and then read JSON from link on landing page.



