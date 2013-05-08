import cPickle as pickle
import numpy as np
import shelve
import sys
from scipy.spatial import cKDTree
csv.field_size_limit(sys.maxsize)
SQRT2 = 1.414214

artistmoods = shelve.open('../artistmoods')
moods = ['aggressive', 'ambient', 'angry', 'bouncy', 'calming', 'carefree', 'cheerful', 'cold', 'dark', 'dramatic', 'dreamy', 'eerie', 'elegant', 'energetic', 'epic', 'funky', 'futuristic', 'gloomy', 'groovy', 'haunting', 'humorous', 'hypnotic', 'industrial', 'intense', 'intimate', 'light', 'lively', 'meditation', 'melancholia', 'mellow', 'mystical', 'party music', 'passionate', 'peaceful', 'poignant', 'quiet', 'reflective', 'relax', 'romantic', 'rowdy', 'sad', 'sentimental', 'sexy', 'smooth', 'soothing', 'sophisticated', 'spacey', 'spiritual', 'strange', 'theater', 'trippy', 'warm', 'whimsical']

# Paste in User class
class User:
  def __init__(self, profile):
    #if profile[1]:
    #  self.gender = 1 if profile[1] == 'm' else 0
    #else:
    #  self.gender = None
    #self.age = int(profile[2]) if profile[2] else None
    self.moodplays = {}
    self.artplays = {}
    self.recweights = {}
    for mood in moods:
      self.moodplays[mood] = 0
      self.recweights[mood] = [1, 1]  # success / overall
  
  def addArtist(self, artmbid, plays=1):
    artistmood = artistmoods[artmbid]
    totalweight = sum([mood['frequency'] * mood['weight']
                      for mood in artistmood])
    for mood in artistmood:
      weight = mood['frequency'] * mood['weight'] / totalweight
      self.moodplays[mood['name']] += 1.0 * weight * plays
    if self.artplays.has_key(artmbid):
      self.artplays[artmbid] += plays  # raw, for rec purposes
    else:
      self.artplays[artmbid] = plays
  
  def recordRecs(self, recs):
    # Recs is a dict of artmbids to bool, whether rec was success
    for artmbid in recs.iterkeys():
      for mood in artistmoods[artmbid]:
        self.recweights[mood['name']][1] += 1  # record overall
        if recs[artmbid]:
          self.recweights[mood['name']][0] += 1  # record success
  
  def getMoodDist(self):
    totalplays = 0
    for mood in moods:
      totalplays += self.moodplays[mood] * (self.recweights[mood][0] / self.recweights[mood][1])
    return [1.0 * self.moodplays[mood] *
            (self.recweights[mood][0] /
             self.recweights[mood][1]) / totalplays
            for mood in moods]


# Build tree for knn model based on each year 1k users
users1k05 = pickle.load(open('../moodrun1K/users05', 'rb'))
users1k06 = pickle.load(open('../moodrun1K/users06', 'rb'))
users1k07 = pickle.load(open('../moodrun1K/users07', 'rb'))
users1k08 = pickle.load(open('../moodrun1K/users08', 'rb'))
users1k09 = pickle.load(open('../moodrun1K/users09', 'rb'))

# Data size
def dataSize(users):
  i = 0
  for user in users.iterkeys():
    if users[user].artplays:
      i += 1
  return i

dataSize(users1k05)
dataSize(users1k06)
dataSize(users1k07)
dataSize(users1k08)
dataSize(users1k09)
len(artistmoods)

def buildKnn(users):
  userlist = []
  moodlist = []
  for user in users.iterkeys():
    if users[user].artplays:
      userlist.append(user)
      moodlist.append(users[user].getMoodDist())
  return userlist, np.array(moodlist)

userlist05, mooddata05 = buildKnn(users1k05)
userlist06, mooddata06 = buildKnn(users1k06)
userlist07, mooddata07 = buildKnn(users1k07)
userlist08, mooddata08 = buildKnn(users1k08)

tree05 = cKDTree(mooddata05)
tree06 = cKDTree(mooddata06)
tree07 = cKDTree(mooddata07)
tree08 = cKDTree(mooddata08)


# Rec methods
def getRecommendations(targetuser, userlist, userdict, usernum,
                       distance, n):
  user = userlist[usernum]
  recs = {}
  if user != targetuser:  # don't recommend based on future self
    weight = 1 - (distance / SQRT2)
    artists = userdict[user].artplays
    topartists = sorted(artists, key=lambda key: artists[key],
                        reverse=True)[0:n]
    for artist in topartists:
      recs[artist] = userdict[user].artplays[artist] * weight
  return recs

def runRecs(users1, users2, tree, userlist):
  # Get recs for year 1
  recs = {}
  for user in users1.iterkeys():
    if users1[user].artplays:  # want users with plays this year
      try:
        recs[user] = tree.query(users1[user].getMoodDist(),
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
        irecs = getRecommendations(user, userlist, users1,
                                   neighbor, distance, n)
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

k = 150  # number of neighbors
p = 2  # default distance metric, Euclidean
n = 1000  # number of artist to recommend per neighbor
t = 10  # number of artists to recommend overall ("top")
# Now predict on user profiles for 1k users in 2005


# Rec runs
users1k05 = pickle.load(open('../moodrun1K/users05', 'rb'))
users1k06 = pickle.load(open('../moodrun1K/users06', 'rb'))
users1k07 = pickle.load(open('../moodrun1K/users07', 'rb'))
users1k08 = pickle.load(open('../moodrun1K/users08', 'rb'))
users1k09 = pickle.load(open('../moodrun1K/users09', 'rb'))

# Method run, with weights
recs05w, users1k06w = runRecs(users1k05, users1k06, tree05, userlist05)
recs06w, users1k07w = runRecs(users1k06w, users1k07, tree06, userlist06)
recs07w, users1k08w = runRecs(users1k07w, users1k08, tree07, userlist07)
recs08w, users1k09w = runRecs(users1k08w, users1k09, tree08, userlist08)

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
recs05nw, users1k06nw = runRecs(users1k05, users1k06, tree05, userlist05)
users1k06 = pickle.load(open('../moodrun1K/users06', 'rb'))
recs06nw, users1k07nw = runRecs(users1k06, users1k07, tree06, userlist06)
users1k07 = pickle.load(open('../moodrun1K/users07', 'rb'))
recs07nw, users1k08nw = runRecs(users1k07, users1k08, tree07, userlist07)
users1k08 = pickle.load(open('../moodrun1K/users08', 'rb'))
recs08nw, users1k09nw = runRecs(users1k08, users1k09, tree08, userlist08)

recAccuracy(recs05nw, users1k06nw)
recAccuracy(recs06nw, users1k07nw)
recAccuracy(recs07nw, users1k08nw)
recAccuracy(recs08nw, users1k09nw)

