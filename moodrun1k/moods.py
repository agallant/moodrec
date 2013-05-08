import csv
import shelve
import sys
csv.field_size_limit(sys.maxsize)

artistmoods = shelve.open('../artistmoods')
moods = set()

for artist in artistmoods.iterkeys():
  artistmood = artistmoods[artist]
  for mood in artistmood:
    moods.add(mood['name'])

moods = list(moods)
moods.sort()


# Extended from the User class run on 360K data
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

playsfile = open('../lastfm-dataset-1K/userid-timestamp-artid-artname-traid-traname.tsv', 'rb')
playsreader = csv.reader(playsfile, delimiter='\t')
usersfile = open('../lastfm-dataset-1K/userid-profile.tsv', 'rb')
usersreader = csv.reader(usersfile, delimiter='\t')
usersreader.next()  # skip a row for header

users05 = {}
users06 = {}
users07 = {}
users08 = {}
users09 = {}
for row in usersreader:
  users05[row[0]] = User(row)
  users06[row[0]] = User(row)
  users07[row[0]] = User(row)
  users08[row[0]] = User(row)
  users09[row[0]] = User(row)

usersfile.close()

i = 0
for row in playsreader:
  print i
  i += 1
  if artistmoods.has_key(row[2]) and users05.has_key(row[0]):
    year = row[1][0:4]
    if year == '2005':
      users05[row[0]].addArtist(row[2])
    elif year == '2006':
      users06[row[0]].addArtist(row[2])
    elif year == '2007':
      users07[row[0]].addArtist(row[2])
    elif year == '2008':
      users08[row[0]].addArtist(row[2])
    elif year == '2009':
      users09[row[0]].addArtist(row[2])

playsfile.close()

from scipy.spatial import cKDTree
import numpy as np
import cPickle as pickle

pickle.dump(users05, open('users05', 'wb'))
pickle.dump(users06, open('users06', 'wb'))
pickle.dump(users07, open('users07', 'wb'))
pickle.dump(users08, open('users08', 'wb'))
pickle.dump(users09, open('users09', 'wb'))


#users = pickle.load(open('users', 'rb'))
userlist = []
moodlist = []
for user in users.iterkeys():
  if users[user].artplays:  # only consider users with plays
    userlist.append(user)
    moodlist.append(users[user].getMoodDist())

pickle.dump(users, open('users', 'wb'))
#del users
pickle.dump(userlist, open('userlist', 'wb'))
pickle.dump(moodlist, open('moodlist', 'wb'))
mooddata = np.array(moodlist)
#del userlist
#del moodlist
tree = cKDTree(mooddata)
