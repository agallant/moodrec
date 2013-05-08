import cPickle as pickle
import csv
import numpy as np
import shelve
import sys
from scipy.spatial import cKDTree
csv.field_size_limit(sys.maxsize)
SQRT2 = 1.414214

# First build dict of 360k users to tracks listened
users360k = pickle.load(open('../moodrun360K/userlist', 'rb'))
playsreader360k = csv.reader(open('../lastfm-dataset-360K/usersha1-artmbid-artname-plays.tsv', 'rb'),
                             delimiter='\t')
artistmoods = shelve.open('../artistmoods')
plays360k = {}
for user in users360k:
  plays360k[user] = {}

i = 0
for row in playsreader360k:
  print i
  if plays360k.has_key(row[0]) and artistmoods.has_key(row[1]):
    plays360k[row[0]][row[1]] = plays360k[row[0]].get(row[1], 0) + int(row[3])
  i += 1

#pickle.dump(plays360k, open('plays360k', 'wb'))  # takes forever...

# Build tree for knn model based on 360k users
moods = ['aggressive', 'ambient', 'angry', 'bouncy', 'calming', 'carefree', 'cheerful', 'cold', 'dark', 'dramatic', 'dreamy', 'eerie', 'elegant', 'energetic', 'epic', 'funky', 'futuristic', 'gloomy', 'groovy', 'haunting', 'humorous', 'hypnotic', 'industrial', 'intense', 'intimate', 'light', 'lively', 'meditation', 'melancholia', 'mellow', 'mystical', 'party music', 'passionate', 'peaceful', 'poignant', 'quiet', 'reflective', 'relax', 'romantic', 'rowdy', 'sad', 'sentimental', 'sexy', 'smooth', 'soothing', 'sophisticated', 'spacey', 'spiritual', 'strange', 'theater', 'trippy', 'warm', 'whimsical']
moods360k = pickle.load(open('../moodrun360K/mooddata', 'rb'))
tree360k = cKDTree(moods360k)

# Paste in user class from moodrun1K code

# Rec methods
def getRecommendations(usernum, distance, n):
  weight = 1 - (distance / SQRT2)
  user = users360k[usernum]
  recs = {}
  artists = plays360k[user]
  topartists = sorted(artists, key=lambda key: artists[key],
                      reverse=True)[0:n]
  for artist in topartists:
    recs[artist] = plays360k[user][artist] * weight
  return recs

def runRecs(users1, users2):
  # Get recs for year 1
  recs = {}
  for user in users1.iterkeys():
    if users1[user].artplays:  # want users with plays this year
      try:
        recs[user] = tree360k.query(users1[user].getMoodDist(),
                                  k=k, p=p)
      except:
        pass  # in case of strange numerical errors
  
  # Evaluate on year 2
  for user in recs.iterkeys():
    # Only want to test if user listened to over 100 tracks
    if sum(users2[user].artplays.values()) > 100:
      # Get recommendations for each nearest neighbor
      urecs = {}
      for i in range(k):
        distance = recs[user][0][i]
        neighbor = recs[user][1][i]
        irecs = getRecommendations(neighbor, distance, n)
        for artist in irecs.iterkeys():
          urecs[artist] = urecs.get(artist, 0) + irecs[artist]
      # Extract top t overall recommendations
      topartists = sorted(urecs, key=lambda key: urecs[key],
                          reverse=True)[0:t]
      # Evaluate against new data, update weights for that model
      recsuccess = {}
      for artist in topartists:
        recsuccess[artist] = artist in users2[user].artplays.keys()
      users2[user].recordRecs(recsuccess)
  return recs, users2


# Evaluate results
# We can evaluate recommendation accuracy by looking at recweights
def recAccuracy(recs, users):
  numrecs = 0
  numsucc = 0
  for user in recs.iterkeys():
    if users[user].artplays:
      for weight in users[user].recweights.values():
        numsucc += weight[0] - 1
        numrecs += weight[1] - 1
  numarts = sum([len(users[user].artplays)
              for user in users.iterkeys()])
  precision = 1.0 * numsucc / numrecs
  recall = 1.0 * numsucc / numarts
  return (precision, recall)

# Rec parameters

k = 10  # number of neighbors
p = 2  # default distance metric, Euclidean
n = 1  # number of artist to recommend per neighbor
t = 10  # number of artists to recommend overall ("top")
# Now predict on user profiles for 1k users in 2005


# Rec runs
users1k05 = pickle.load(open('../moodrun1K/users05', 'rb'))
users1k06 = pickle.load(open('../moodrun1K/users06', 'rb'))
users1k07 = pickle.load(open('../moodrun1K/users07', 'rb'))
users1k08 = pickle.load(open('../moodrun1K/users08', 'rb'))
users1k09 = pickle.load(open('../moodrun1K/users09', 'rb'))

# Method run, with weights
recs05w, users1k06w = runRecs(users1k05, users1k06)
recs06w, users1k07w = runRecs(users1k06w, users1k07)
recs07w, users1k08w = runRecs(users1k07w, users1k08)
recs08w, users1k09w = runRecs(users1k08w, users1k09)

recAccuracy(recs05w, users1k06w)
recAccuracy(recs06w, users1k07w)
recAccuracy(recs07w, users1k08w)
recAccuracy(recs08w, users1k09w)


# Without weights
users1k05 = pickle.load(open('../moodrun1K/users05', 'rb'))
users1k06 = pickle.load(open('../moodrun1K/users06', 'rb'))
users1k07 = pickle.load(open('../moodrun1K/users07', 'rb'))
users1k08 = pickle.load(open('../moodrun1K/users08', 'rb'))
users1k09 = pickle.load(open('../moodrun1K/users09', 'rb'))
recs05nw, users1k06nw = runRecs(users1k05, users1k06)
users1k06 = pickle.load(open('../moodrun1K/users06', 'rb'))
recs06nw, users1k07nw = runRecs(users1k06, users1k07)
users1k07 = pickle.load(open('../moodrun1K/users07', 'rb'))
recs07nw, users1k08nw = runRecs(users1k07, users1k08)
users1k08 = pickle.load(open('../moodrun1K/users08', 'rb'))
recs08nw, users1k09nw = runRecs(users1k08, users1k09)

recAccuracy(recs05nw, users1k06nw)
recAccuracy(recs06nw, users1k07nw)
recAccuracy(recs07nw, users1k08nw)
recAccuracy(recs08nw, users1k09nw)



# Ad hoc mood-based queries
moods = ['aggressive', 'ambient', 'angry', 'bouncy', 'calming',
         'carefree', 'cheerful', 'cold', 'dark', 'dramatic',
         'dreamy', 'eerie', 'elegant', 'energetic', 'epic',
         'funky', 'futuristic', 'gloomy', 'groovy', 'haunting',
         'humorous', 'hypnotic', 'industrial', 'intense',
         'intimate', 'light', 'lively', 'meditation',
         'melancholia', 'mellow', 'mystical', 'party music',
         'passionate', 'peaceful', 'poignant', 'quiet',
         'reflective', 'relax', 'romantic', 'rowdy', 'sad',
         'sentimental', 'sexy', 'smooth', 'soothing',
         'sophisticated', 'spacey', 'spiritual', 'strange',
         'theater', 'trippy', 'warm', 'whimsical']
moods1 = [0 for i in range(len(moods))]
moods1[moods.index('cheerful')] = 1
moods2 = [0 for i in range(len(moods))]
moods2[moods.index('funky')] = 1
moods3 = [0 for i in range(len(moods))]
moods3[moods.index('cheerful')] = 0.5
moods3[moods.index('funky')] = 0.5

def adHocRecs(moodsdist, k, p):
  neighbors = tree360k.query(moodsdist, k=k, p=p)
  recs = {}
  for i in range(k):
    distance = neighbors[0][i]
    neighbor = neighbors[1][i]
    irecs = getRecommendations(neighbor, distance, n)
    for artist in irecs.iterkeys():
      recs[artist] = recs.get(artist, 0) + irecs[artist]
  # Extract top t overall recommendations
  topartists = sorted(recs, key=lambda key: recs[key],
                      reverse=True)[0:t]
  return topartists

k = 100  # number of neighbors
p = 2  # default distance metric, Euclidean
n = 1  # number of artist to recommend per neighbor
t = 1  # number of artists to recommend overall ("top")

adHocRecs(moods1, k, p)
adHocRecs(moods2, k, p)
adHocRecs(moods3, k, p)




# OLD STUFF
#########################
# And now finally, resuls

# 2005 recommendations in 2006 recweights
recs0506 = 0
succ0506 = 0
for user in recs05.iterkeys():
  if users1k06[user].artplays:
    for weight in users1k06[user].recweights.values():
      succ0506 += weight[0] - 1
      recs0506 += weight[1] - 1

# 2006 - 2007
recs0607 = 0
succ0607 = 0
for user in recs06.iterkeys():
  if users1k07[user].artplays:
    for weight in users1k07[user].recweights.values():
      succ0607 += weight[0] - 1
      recs0607 += weight[1] - 1

# 2007 - 2008
recs0708 = 0
succ0708 = 0
for user in recs07.iterkeys():
  if users1k08[user].artplays:
    for weight in users1k08[user].recweights.values():
      succ0708 += weight[0] - 1
      recs0708 += weight[1] - 1

# 2008 - 2009
recs0809 = 0
succ0809 = 0
for user in recs08.iterkeys():
  if users1k09[user].artplays:
    for weight in users1k09[user].recweights.values():
      succ0809 += weight[0] - 1
      recs0809 += weight[1] - 1

# PRECISION
1.0 * succ0506 / recs0506
1.0 * succ0607 / recs0607
1.0 * succ0708 / recs0708
1.0 * succ0809 / recs0809


# Recall is simply how many of listened artists were rec'd
# All recs are unique artists, so success recs / all artists
plays0506 = sum([len(users1k06[user].artplays)
                for user in users1k06.iterkeys()])
plays0607 = sum([len(users1k07[user].artplays)
                for user in users1k07.iterkeys()])
plays0708 = sum([len(users1k08[user].artplays)
                for user in users1k08.iterkeys()])
plays0809 = sum([len(users1k09[user].artplays)
                for user in users1k09.iterkeys()])

# RECALL
1.0 * succ0506 / plays0506
1.0 * succ0607 / plays0607
1.0 * succ0708 / plays0708
1.0 * succ0809 / plays0809



## OLD CRAPPY CODE


users1k05 = pickle.load(open('../moodrun1K/users05', 'rb'))
recs05 = {}
for user in users1k05.iterkeys():
  if users1k05[user].artplays:  # want users with plays this year
    recs05[user] = tree360k.query(users1k05[user].getMoodDist(),
                                  k=k, p=p)

# Evaluate on 2006 playbacks
users1k06 = pickle.load(open('../moodrun1K/users06', 'rb'))
for user in recs05.iterkeys():
  # Only want to test if user listened to over 100 tracks
  if sum(users1k06[user].artplays.values()) > 100:
    # Get recommendations for each nearest neighbor
    recs = {}
    for i in range(k):
      distance = recs05[user][0][i]
      neighbor = recs05[user][1][i]
      userrecs = getRecommendations(neighbor, distance, n)
      for artist in userrecs.iterkeys():
        if recs.has_key(artist):
          recs[artist] += userrecs[artist]
        else:
          recs[artist] = userrecs[artist]
    # Extract top t overall recommendations
    topartists = sorted(recs, key=lambda key: recs[key],
                        reverse=True)[0:t]
    # Evaluate against new data, update weights for that model
    recsuccess = {}
    for artist in topartists:
      recsuccess[artist] = artist in users1k06[user].artplays.keys()
    users1k06[user].recordRecs(recsuccess)


####### COPY PASTE EXTREME, significant refactoring needed...
# Recommend on 2006
recs06 = {}
for user in users1k06.iterkeys():
  if users1k06[user].artplays:  # want users with plays this year
    recs06[user] = tree360k.query(users1k06[user].getMoodDist(),
                                  k=k, p=p)

# Evaluate on 2007
users1k07 = pickle.load(open('../moodrun1K/users07', 'rb'))
for user in recs06.iterkeys():
  # Only want to test if user listened to over 100 tracks
  if sum(users1k07[user].artplays.values()) > 100:
    # Get recommendations for each nearest neighbor
    recs = {}
    for i in range(k):
      distance = recs06[user][0][i]
      neighbor = recs06[user][1][i]
      userrecs = getRecommendations(neighbor, distance, n)
      for artist in userrecs.iterkeys():
        if recs.has_key(artist):
          recs[artist] += userrecs[artist]
        else:
          recs[artist] = userrecs[artist]
    # Extract top t overall recommendations
    topartists = sorted(recs, key=lambda key: recs[key],
                        reverse=True)[0:t]
    # Evaluate against new data, update weights for that model
    recsuccess = {}
    for artist in topartists:
      recsuccess[artist] = artist in users1k07[user].artplays.keys()
    users1k07[user].recordRecs(recsuccess)

####### COPY PASTE EXTREME, significant refactoring needed...
# Recommend on 2007
recs07 = {}
for user in users1k07.iterkeys():
  if users1k07[user].artplays:  # want users with plays this year
    recs07[user] = tree360k.query(users1k07[user].getMoodDist(),
                                  k=k, p=p)

# Evaluate on 2008
users1k08 = pickle.load(open('../moodrun1K/users08', 'rb'))
for user in recs07.iterkeys():
  # Only want to test if user listened to over 100 tracks
  if sum(users1k08[user].artplays.values()) > 100:
    # Get recommendations for each nearest neighbor
    recs = {}
    for i in range(k):
      distance = recs07[user][0][i]
      neighbor = recs07[user][1][i]
      userrecs = getRecommendations(neighbor, distance, n)
      for artist in userrecs.iterkeys():
        if recs.has_key(artist):
          recs[artist] += userrecs[artist]
        else:
          recs[artist] = userrecs[artist]
    # Extract top t overall recommendations
    topartists = sorted(recs, key=lambda key: recs[key],
                        reverse=True)[0:t]
    # Evaluate against new data, update weights for that model
    recsuccess = {}
    for artist in topartists:
      recsuccess[artist] = artist in users1k08[user].artplays.keys()
    users1k08[user].recordRecs(recsuccess)

####### COPY PASTE EXTREME, significant refactoring needed...
# Recommend on 2008
recs08 = {}
for user in users1k08.iterkeys():
  if users1k08[user].artplays:  # want users with plays this year
    try:
      recs08[user] = tree360k.query(users1k08[user].getMoodDist(),
                                    k=k, p=p)
    except:
      pass  # getting a weird numerical error for 1 user...

# Evaluate on 2009
users1k09 = pickle.load(open('../moodrun1K/users08', 'rb'))
for user in recs08.iterkeys():
  # Only want to test if user listened to over 100 tracks
  if sum(users1k09[user].artplays.values()) > 100:
    # Get recommendations for each nearest neighbor
    recs = {}
    for i in range(k):
      distance = recs08[user][0][i]
      neighbor = recs08[user][1][i]
      userrecs = getRecommendations(neighbor, distance, n)
      for artist in userrecs.iterkeys():
        if recs.has_key(artist):
          recs[artist] += userrecs[artist]
        else:
          recs[artist] = userrecs[artist]
    # Extract top t overall recommendations
    topartists = sorted(recs, key=lambda key: recs[key],
                        reverse=True)[0:t]
    # Evaluate against new data, update weights for that model
    recsuccess = {}
    for artist in topartists:
      recsuccess[artist] = artist in users1k09[user].artplays.keys()
    users1k09[user].recordRecs(recsuccess)











