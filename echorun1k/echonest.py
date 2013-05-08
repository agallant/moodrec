import csv
import shelve
import simplejson
import sys
import urllib2
from time import time, sleep
csv.field_size_limit(sys.maxsize)

API_KEY = ''
BASE_URL = 'http://developer.echonest.com/api/v4/artist/terms?api_key=' + API_KEY + '&format=json&type=mood&id=musicbrainz:artist:'
RATE_LIMIT = 120  # calls per minute
# radiohead example: a74b1b7f-71a5-4011-9441-d0b5e4122711


playsfile = open('../lastfm-dataset-1K/userid-timestamp-artid-artname-traid-traname.tsv', 'rb')
playsreader = csv.reader(playsfile, delimiter='\t')
## extract unique artists
artists = set()
for row in playsreader:
  if row[2] != '':
    artists.add(row[2])

playsfile.close()
moods = shelve.open('moods')
opener = urllib2.build_opener()

#i = 1000
failed = []
art = 0
num = 0
start = time()
for artist in artists:
  print art
  #if not i:
  #  break
  url = BASE_URL + artist
  try:
    req = urllib2.Request(url)
    f = opener.open(req)
    json = simplejson.load(f)
    if json['response']['status']['code'] == 0:  # success
      if json['response']['terms']:  # and it found moods
        moods[artist] = json['response']['terms']
    num += 1
  except:  # something went wrong, try waiting a minute
    print 'WAITING'
    failed.append(artist)
    sleep(60)
    num = 0
    start = time()
  if num == RATE_LIMIT:  # Rate limit wait
    elapsed_time = time() - start
    sleep_time = 60 - elapsed_time
    sleep(sleep_time)
    num = 0
    start = time()
  #i -= 1
  art += 1

moods.close()
