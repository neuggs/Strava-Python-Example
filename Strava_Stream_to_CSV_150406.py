import stravalib
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import urllib
import webbrowser
import numpy
import pandas as pd
import datetime

client_id = '31196'
athlete_id = '721568'
access_token_site = 'a2e9dc9caf7ebe57e8f60b7994052e27b9b929bd'
secret = '628d8f82fecf138a30c149b5b9b21d4a12419e47'

port = 5000
url = 'http://localhost:%d/authorized' % port
allDone = False
types = ['time', 'distance', 'latlng', 'altitude', 'velocity_smooth', 'moving', 'grade_smooth', 'temp']
limit = 100

#Create the strava client, and open the web browser for authentication
client = stravalib.client.Client(access_token=access_token_site)
authorize_url = client.authorization_url(client_id=client_id, redirect_uri=url)
print('Opening: %s' % authorize_url)
webbrowser.open(authorize_url)

#Define the web functions to call from the strava API
def UseCode(code):
  #Retrieve the login code from the Strava server
  access_token = client.exchange_code_for_token(client_id=client_id, client_secret=secret, code=code)
  # Now store that access token somewhere (for now, it's just a local variable)
  client.access_token = access_token
  athlete = client.get_athlete()
  #print("For %(id)s, I now have an access token %(token)s" %
  #      {'id': athlete.id, 'token': access_token})
  return client

def GetActivities(client,limit):
    #Returns a list of Strava activity objects, up to the number specified by limit
    activities = client.get_activities(limit=limit)
    for item in activities:
        print(item)
    return activities

def GetStreams(client, activity, types):
    #Returns a Strava 'stream', which is timeseries data from an activity
    streams = client.get_activity_streams(activity, types=types, series_type='time')
    return streams

def DataFrame(dict,types):
    #Converts a Stream into a dataframe, and returns the dataframe
    print(dict, types)
    df = pd.DataFrame()
    for item in types:
        if item in dict.keys():
            df.append(item.data)
    df.fillna('',inplace=True)
    return df

def ParseActivity(act,types):
    act_id = act.id
    name = act.name
    print(str(act_id), str(act.name), act.start_date)
    streams = GetStreams(client,act_id,types)
    df = pd.DataFrame()

    #Write each row to a dataframe
    for item in types:
        if item in streams.keys():
            df[item] = pd.Series(streams[item].data,index=None)
        df['act_id'] = act.id
        df['act_startDate']= pd.to_datetime(act.start_date)
        df['act_name'] = name
    return df

def calctime(time_sec, startdate):
    try:
        timestamp = startdate + datetime.timedelta(seconds=int(time_sec))
    except:
        print('time processing error : ' + str(time_sec))
        timestamp = startdate
    return timestamp

def split_lat(series):
    lat = series[0]
    return lat

def split_long(series):
    long = series[1]
    return long

def concatdf(df_lst):
    return pd.concat(df_lst, ignore_index=False)

class MyHandler(BaseHTTPRequestHandler):
  #Handle the web data sent from the strava API

  def do_HEAD(self):
    return self.do_GET()

  def do_GET(self):
    #Get the API code for Strava
    output = b""
    output += b"<script>window.close();</script>"
    self.wfile.write(output)
    the_path = self.path
    parsed = urlparse(the_path)
    print(parsed.query)
    qs = urllib.parse.parse_qs(parsed.query)
    code = qs['code']
    print(code)

    #Login to the API
    client = UseCode(code)

    #Retrieve the last limit activities
    activities = GetActivities(client,limit)

    #Loop through the activities, and create a dict of the dataframe stream data of each activity
    print("looping through activities...")
    df_lst = {}
    for act in activities:
        df_lst[act.start_date] = ParseActivity(act,types)

    #create the concatenated df and fill null values
    df_total = concatdf(df_lst)
    df_total.fillna('',inplace=True)

    #Calculate the timestamp column
    df_total = df_total.reset_index(level=0)
    df_total['timestamp'] = pd.to_datetime(map(calctime, df_total['time'], df_total['level_0'])).to_pydatetime()

    #Split out lat and long columns
    df_total['lat'] = map(split_lat, (df_total['latlng']))
    df_total['long'] = map(split_long, (df_total['latlng']))

    #Index by startdate and timestamp, and drop arbitrary columns
    df_total = df_total.set_index(['act_startDate','timestamp'])
    df_total.drop(['latlng', 'level_0'], axis=1, inplace=True)
    print(df_total.head(2))

    #Write the file to a CSV - this will end up in your working directory
    now = datetime.datetime.now()
    df_total.to_csv('RideData_' + str(now.strftime('%Y%m%d%H%M%S')) + '.csv')

###Run the program to login and grab data###
httpd = HTTPServer(('localhost', port), MyHandler)
while not allDone:
    httpd.handle_request()
