# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 09:22:37 2016

@author: gnakhleh
"""

'''
ECT 584: Web Data Mining
Final Project
Finding patterns in user logs
'''

#import packages we'll need to work with dataframes
import numpy as np
import pandas as pd

#Change directory
import os
os.chdir("C:\\Users\\gnakhleh\\Documents\\ECT584")

'''
This data comes from the French company Dataiku, which makes a platform for data analytics
It is user logs for the month of March 2014
'''
#Read in the data
dataiku_userlogs = pd.read_csv("dataiku_munged.csv")

dataiku_userlogs.head()
dataiku_userlogs.shape  # 10,849 records (events) and 24 columns

dataiku_userlogs.columns
### Variables: 'server_ts', 'client_ts', 'client_addr', 'visitor_id', 
### 'session_id', 'location', 'referer', 'user_agent', 'type', 'visitor_params',
### 'session_params', 'event_params', 'br_width', 'br_height', 'sc_width', 'sc_height', 'br_lang', 'tz_off'

'''
What do these variables mean?
Documentation: http://doc.dataiku.com/display/WT1/WT1+Analyst%27s+Guide
"ts" means timestamp, "br" browser, "sc" screen

Honestly, this would be easier to inspect in Excel, since the data fits

Details + example:
server_ts: 2014-03-12T23:01:16.372
client_ts: 2014-03-12T23:01:15.263
client_addr: 181.168.219.245
visitor_id: should be same as user_agent; 4f0bf6913915c00
session_id: automatically expires after 30min ef365b61dceff87
location (URL where event was recorded): http://dataiku.com/blog/2014/01/14/winning-kaggle.html
referer: http://www.datatau.com/
user_agent: Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:26.0) Gecko/20100101 Firefox/26.0
type: page
visitor_params: ALL NULL
session_params: ALL NULL
event_params: ALL BLANK
br_width: 1366
br_height: 599
sc_width: 1366
sc_height: 768
br_lang: pt-BR
tz_off (Timezone offset of user's browser, in minutes to UTC) : 180
'''

#To verify that visitor_params, session_params, and event_params are all blank
#If so, we'll drop

#dataiku_userlogs['visitor_params'].describe()
#dataiku_userlogs['visitor_params'].unique()

#dataiku_userlogs['session_params'].describe()
#dataiku_userlogs['session_params'].unique()

#dataiku_userlogs['event_params'].describe()
#dataiku_userlogs['event_params'].unique()

#Ok so we will drop all three of these variables
#(already dropped in the munged version): dataiku_userlogs.drop(['visitor_params','session_params', 'event_params'], axis=1, inplace=True)

#Did that work?
#dataiku_userlogs.shape #Yes

'''
Exploratory data analysis: Phase 1
What might we be interested in?

- Breakdown of browser types (user agent)
'''

#Lets look at types of browsers
dataiku_userlogs.user_agent.value_counts()  
#many different kinds, unclear whats safari vs chrome vs firefox ...
#useful reading: https://en.wikipedia.org/wiki/User_agent

#looks like what we want to do is user agent parsing, to get all the info out of the user agent clearly in the open
#package called ua-parser
#Note: can do pip install's in Spyder by opening the command line
from ua_parser import user_agent_parser
import pprint

pp = pprint.PrettyPrinter(indent=4)

#try with one entry from our user_agent column

ua_string = dataiku_userlogs.user_agent[4] #treat the column as a Series
parsed_string = user_agent_parser.Parse(ua_string)
pp.pprint(parsed_string)
type(parsed_string) #it converted the string into a dictionary!

#a script that will create new columns
#via: http://stackoverflow.com/a/37110774
def parse_ua(ua):
    p = user_agent_parser.Parse(ua)
    return [p.get('os').get('family'), p.get('user_agent').get('family'), p.get('device').get('family')]

user_agent_deetz = dataiku_userlogs.user_agent.apply(parse_ua).apply(pd.Series).rename(columns={0:'browser', 1:'os', 2:'device'})

#merge the two datasets on their index
#usually risky, and since we have no unique id in the dataframe to use anyways, we should do that now as well
dataiku_userlogs['uniqueid'] = dataiku_userlogs.index
dataiku_userlogs = dataiku_userlogs.merge(user_agent_deetz, right_index=True, left_index=True)

#ok so let's validate this a bit
#tool to validate: http://www.useragentstring.com/index.php
dataiku_userlogs[['user_agent', 'browser', 'os', 'device']].head(20) #checks out

'''
More data to generate:
- Location of IP address
- Categories of site (using what comes after main URL)
'''

#geolocating ip addresses

#NOTE: the reason this had trouble earlier is that there are IP's w/ commas
#We could make a new column that splits on commas, and then make THAT the column we use for IP address ...

#make a new column
main_ip = []
for row in dataiku_userlogs['client_addr']:
    if ',' in row:
        ips = row.split(',')
        main_ip.append(ips[0])
    else:
        main_ip.append(row)

dataiku_userlogs['main_ip'] = main_ip

import urllib

#use a diff locator: a local database downloaded from https://pypi.python.org/pypi/pygeoip
import pygeoip
geo_db = pygeoip.GeoIP('GeoLiteCity.dat')

from socket import gethostbyname, gaierror

def ipLocator(ip):
    try:
        geo_data = geo_db.record_by_name(ip)
        record = [geo_data.get('country_name'), geo_data.get('city'), geo_data.get('postal_code'), geo_data.get('latitude'), geo_data.get('longitude')]
    except (gaierror, AttributeError):
        record = ["Unknown","Unknown","Unknown","Unknown","Unknown"]
    return record
#test
print(ipLocator(dataiku_userlogs.client_addr[5]))

#ok lets use this version
ip_geo = dataiku_userlogs.main_ip.apply(ipLocator).apply(pd.Series)
ip_geo.head(40)

#We'll turn this array into a dataframe
#We'll merge this df w/ our main
ip_geo = ip_geo.rename(columns={0:'country', 1:'city', 2:'zipcode', 3:'latitude', 4:'longitude'})
dataiku_userlogs = dataiku_userlogs.merge(ip_geo, right_index=True, left_index=True)
dataiku_userlogs.head(10)

#Most common countries
dataiku_userlogs.country.value_counts()  #United States by far, then China. Many countries, though.
dataiku_userlogs.country.nunique() #139 unique countries

#Now let's make new columns for the category of page they went to
#NOT DONE: what's the regex??
#dataiku_userlogs['location'].head(20)
#subsection = []    

#The regex we want: (?<=dataiku\.com\/)(.*?)(?=\/)
#If the new column has a blank value, replace that blank w/ "home"

dataiku_userlogs['page_category'] = dataiku_userlogs['location'].str.extract('dataiku.com/(.*?)/')
dataiku_userlogs[['location', 'page_category']]

dataiku_userlogs['page_category'].fillna(value='home', inplace=True)

#Lets look at the most common pages and categories

dataiku_userlogs['page_category'].value_counts()
#looks like there are some blank categories

dataiku_userlogs[['location', 'page_category']][dataiku_userlogs['page_category'] == ""]  #they are all blog

#replace blank values with blog
dataiku_userlogs['page_category'][dataiku_userlogs['page_category'] == ""] = "blog"

dataiku_userlogs['page_category'].value_counts()
dataiku_userlogs['location'].nunique()  #only 58 unique pages: not small, not huge
dataiku_userlogs['location'].value_counts() #not surprising: home pg, landing pgs of main sections
#looks like we need to trim some trailing info from some urls: anything to the right of "?"

#How many repeat visits do we have in the data?
#That would be visit_id's w/ multiple session_id'
dataiku_userlogs.groupby(by=['visitor_id'])['session_id'].count()
# a lot of them have more than one session, but how could we count this up better?
dataiku_userlogs.pivot_table(values = ['session_id'], index=['visitor_id'], aggfunc = lambda x: x.nunique())

#So at this point we have done the following feature engineering:
#geolocate ip addresses: country, region, zip, lat, long
#parsed the user agent: os, browser, device
#categorized the url visited: page_category

#Still to do: time spent on each page

#Reorder the columns
dataiku_userlogs.columns.values
dataiku_userlogs.drop(['Unnamed: 0'], axis=1, inplace=True)
dataiku_userlogs.drop(['X'], axis=1, inplace=True)

dataiku_userlogs = dataiku_userlogs[['visitor_id', 'session_id','server_timestamp_sec', 'server_timestamp', 'server_date', 'server_time', 'client_date',
       'client_time', 'client_addr', 'main_ip', 'country', 'city', 'zipcode', 'latitude', 'longitude',
       'location', 'page_category', 'referer', 'user_agent', 'browser', 'os', 'device', 'type', 'br_width',
       'br_height', 'sc_width', 'sc_height', 'br_lang', 'tz_off',
       'path.completion.', 'pc.answer', 'needs.insert.', 'uniqueid']]

#HOW ARE WE GOING TO SESSIONIZE?

#Lets sort by session_id, server_timestamp_sec .. and then group by session id
agg = dataiku_userlogs[['server_date','server_time', 'server_timestamp_sec', 'session_id', 'location', 'referer', 'path.completion.', 'pc.answer']].sort(['session_id', 'server_timestamp_sec']).groupby('session_id')

#for name, group in agg:
#    print(name)
#    print(group)
#    print('\n')
    
len(agg.groups)  #there are 3946 session_ids
#verify
dataiku_userlogs['session_id'].nunique() #yep

'''
Intermediary reformatting
Our end goal is to create the session-pageview matrix for clustering, and the n-itemsets for association rules
The missing link is to make a dataframe of sessions, all-urls-visited (list), all-url-categories (list), and all-time-spent-on-page (list)

Steps: 
1) Calc the time spent on each page
2) For each group in the grouped dataframe, chain together the values of the location column
3) For each group in the grouped dataframe, chain together the values of the page_category column
4) For each group in the grouped dataframe, chain together the values of the newly created time_spent column
At this point, we should have 4 NEW variables
A list of every session_id
A list of lists: url path for each session
A list of lists: url cat's for each session
A list of lists: timespent for each page of the session
Smarter way to do this?
'''

#CREATE THE TIME SPENT PER PAGE COLUMN

#Practice using the shift function, which we'll use to get time differences
#df = pd.DataFrame({"A": [100, 110, 122, 151], "B": [12, 7, 5, 4]})
#df['timespent_A'] = abs(df['A'] - df['A'].shift(-1))
#df  #ok, this seems similar to what we want to apply to every group

def time_diff(column):
    return abs(column - column.shift(-1))

dataiku_userlogs['time_spent'] = agg['server_timestamp_sec'].transform(time_diff)

agg = dataiku_userlogs[['server_date','server_time', 'server_timestamp_sec', 'time_spent', 'session_id', 'location', 'referer', 'path.completion.', 'pc.answer']].sort(['session_id', 'server_timestamp_sec']).groupby('session_id')
#for name, group in agg:
#    print(name)
#    print(group)
#    print('\n')  #IT WORKS

#What are we going to do about 1-page visits (bounces) and time spent on last page?
#methodologies here: https://cran.r-project.org/web/packages/reconstructr/vignettes/Introduction.html
dataiku_userlogs['time_spent'].describe() #mean: 21, std: 29 !
dataiku_userlogs['time_spent'].median() #10 sec.
#Don't want to remove bounces and/or last pages. Instead, let's buffer with the median timespent: 10 sec
dataiku_userlogs['time_spent'].fillna(10, inplace=True)
dataiku_userlogs['time_spent'].describe() #mean now down to 17 sec, std 24
dataiku_userlogs['time_spent'].median()  #median has moved to 21


#CHAIN TOGETHER VALUES OF THE LOCATION COLUMN
import itertools

#Chain together the clickpath for each session
dataiku_userlogs['session_path_full'] = agg['location'].transform(itertools.chain)

agg = dataiku_userlogs[['server_date','server_time', 'server_timestamp_sec', 'time_spent', 'session_id', 'location', 'session_path_full', 'page_category', 'referer', 'path.completion.', 'pc.answer']].sort(['session_id', 'server_timestamp_sec']).groupby('session_id')
#for name, group in agg:
#    print(name)
#    print(group)
#    print('\n')

dataiku_userlogs['session_path_full'] = dataiku_userlogs['session_path_full'].apply(list)

#Keey going with the creation of session_categories and session_timespent, and we'll create the new df via drop_duplicates
dataiku_userlogs['session_categories'] = agg['page_category'].transform(itertools.chain)
dataiku_userlogs['session_categories'] = dataiku_userlogs['session_categories'].apply(list)

dataiku_userlogs[['session_id', 'location', 'session_path_full', 'session_categories']].head(11)

#something wrong here: thinks we're trying to turn itertools.chain into a float() ...
#dataiku_userlogs['session_times_spent'] = agg['time_spent'].transform(itertools.chain)
#cheap solution: turn the times into strings, and we'll convert them all back
dataiku_userlogs['time_spent'] = dataiku_userlogs['time_spent'].astype(str)
agg = dataiku_userlogs[['server_date','server_time', 'server_timestamp_sec', 'time_spent', 'session_id', 'location', 'session_path_full', 'page_category', 'referer', 'path.completion.', 'pc.answer']].sort(['session_id', 'server_timestamp_sec']).groupby('session_id')
dataiku_userlogs['session_times_spent'] = agg['time_spent'].transform(itertools.chain)
dataiku_userlogs['session_times_spent'] = dataiku_userlogs['session_times_spent'].apply(list)
#ok, let's turn the values of all those lists back into float

#convert values of each list to float
dataiku_userlogs['session_times_spent'] = dataiku_userlogs['session_times_spent'].apply(lambda x: map(float, x))
#convert the map objects into lists as they should be
dataiku_userlogs['session_times_spent'] = dataiku_userlogs['session_times_spent'].apply(list)
#ok, that's fixed

'''
Now we have all the variables we need to make a dataframe we want:
The new df will include:
session_id
clickstream
clickstream categories
times spent on each page of the clickstream
'''
#making column values that are lists has caused some trouble with Pandas
#solution: https://stackoverflow.com/questions/26112785/where-clause-on-a-list-in-a-pandas-dataframe
mask = dataiku_userlogs['session_path_full'] != pd.Series([[]] * len(dataiku_userlogs))
clickstream_df = dataiku_userlogs[mask]
clickstream_df = clickstream_df[['session_id', 'server_date', 'country', 'browser', 'os', 'sc_width', 'referer', 'session_path_full', 'session_categories', 'session_times_spent']]

clickstream_df_basic = clickstream_df[['session_id', 'session_path_full', 'session_categories', 'session_times_spent']]

#We can do some more EDA now:
#What is the average visit length, page count?
clickstream_df['session_total_time'] = clickstream_df['session_times_spent'].apply(sum)
clickstream_df['session_total_pages'] = clickstream_df['session_path_full'].apply(len)

clickstream_df['session_total_time'].mean()  #under a minute: 47.5 sec
clickstream_df['session_total_pages'].mean() #2.7 pages
#bounce rate
clickstream_df['session_total_pages'][clickstream_df['session_total_pages'] == 1].count() / clickstream_df['session_total_pages'].count()  #over half of visits are bounces

clickstream_df['session_total_pages'].value_counts()
clickstream_df['session_total_pages'].describe() #half of the data is bounces, avg session clickpath is 2 pgs long

clickstream_df['session_total_time'].describe() #since we filled in bounces w/ 10 sec pg duration, 50% of visits last 10 sec. Avg visit length is 47 sec

clickstream_df['session_total_time'].where(clickstream_df['session_total_pages'] > 1).describe()
clickstream_df['session_total_pages'].where(clickstream_df['session_total_pages'] > 1).describe()

clickstream_df['session_total_pages'].value_counts().plot("bar")

#We can now do more EDA at the session level
#common browsers, os, devices
clickstream_df['browser'].value_counts() #Windows 7, Mac OS X top 2 by far
clickstream_df['os'].value_counts() #Chrome by far. Firefox next.

clickstream_df['country'].value_counts()  #United State by far. Interesting that French is so much smaller, given it is a French company. 


#How could we analyze the entry page, entry referrer?
landing_pgs = []
clickstream_df['session_path_full'].apply(lambda x: landing_pgs.append(x[0]))
landing_pgs = pd.Series(landing_pgs)
landing_pgs.value_counts() #home page by far, followed by products, and blog posts

#How about exit page?
exit_pgs = []
clickstream_df['session_path_full'].apply(lambda x: exit_pgs.append(x[-1]))
exit_pgs = pd.Series(exit_pgs)
exit_pgs.value_counts()

#Same info, but categorized
landing_cats = []
clickstream_df['session_categories'].apply(lambda x: landing_cats.append(x[0]))
pd.Series(landing_cats).value_counts()  #home still leads, but blog posts not very far behind: may imply marketing success


#What about top referrer to the website?
#This would be the referrer to the very first page. Since this is from a tracker, it might include it
#Let's check it out
#Since the clickpath's and times were chained to the top row of each session grouping (sorted by session and time), our clickstream_df has this

clickstream_df['referer'].value_counts() #too messy, let's get everything to the left of the first '/'
clickstream_df['referer_clean'] = clickstream_df['referer'].str.extract('(.*?)/')
clickstream_df['referer_clean'].value_counts() #top referrers: google.fr, dataiku itself (these are sessions, keep in mind)

clickstream_df['referer_clean'].str.contains('google').value_counts() #Google refers nearly half of the sessions in our dataset

#How about engagement on each page?
dataiku_userlogs['time_spent'] = dataiku_userlogs['time_spent'].apply(float)
dataiku_userlogs.pivot_table(values = ['time_spent'], index = ['location'], aggfunc = np.median).sort_values(by=['time_spent'])
#most are 10, since we set bounces to 10

#We can use sc_width to define mobile or not
#Very few phones/tablets are wider than 1000
clickstream_df['sc_width'].describe()
clickstream_df['mobile/tablet?'] = np.where(clickstream_df['sc_width'] < 1000, 1, 0)

clickstream_df.pivot_table(values = ['mobile/tablet?'], index=['sc_width'], aggfunc = np.count_nonzero)
clickstream_df.pivot_table(values = ['session_total_time'], index=['mobile/tablet?'], aggfunc = np.mean)  #pretty much the same, maybe because the site is generally simple?





clickstream_df.head(4)
#test that we got all the rows we wanted: should be 3946
clickstream_df.shape #yep

'''
We now have our intermediate dataframe
What do we want to do now?

Association rules:
look at common sequences
'''

#WE ARE GOING TO WRITE OUT OUR DATA SO THAT WE CAN USE Python 2.7 for ASSOCIATION RULES
############################################################################################

clickstream_df.to_csv("data.csv")
############################################################################################


'''
Markov models

If we wanted to look at the path from one page to another ...
Couldn't we use a crosstab of url and referrer?
This would be moderately different data than our constructed paths, since we forced direct paths for that

'''

#Lets use the original data for this

dataiku_userlogs['referrer_clean'] = dataiku_userlogs['referer'].str.extract('(.*?)/')

dataiku_userlogs['referrer_clean'].value_counts()

'''
CLUSTERING

What kind of view of the data do we need?

We need every possible page category (or url), and whether or not a visit includes that category (/url), OR if it does include it, the time spent on that site

It might make sense to create a new blank df w/ columns of this view
... and use the original event-level data to test for conditions, SQL style

First, let's try to think of how we can leverage the session-level view
'''


#What's going in the clustering model
#per session_id: time spent on every url, total time spent, total pgs visited, 
        






