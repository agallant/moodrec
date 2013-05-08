import csv
import shelve
import sys
csv.field_size_limit(sys.maxsize)

moods = shelve.open('../echorun360K/moods')

emotions = set()

for artist in moods.iterkeys():
  artistmoods = moods[artist]
  for mood in artistmoods:
    emotions.add(mood['name'])

emotions = list(emotions)
emotions.sort()


class User:
  def __init__(self, profile):
    if profile[1]:
      self.gender = 1 if profile[1] == 'm' else 0
    else:
      self.gender = None
    self.age = int(profile[2]) if profile[2] else None
    self.moodplays = {}
    for emotion in emotions:
      self.moodplays[emotion] = 0
    self.totalplays = 0
  
  def addArtist(self, artmbid, plays=1):
    artistmoods = moods[artmbid]
    totalweight = sum([mood['frequency'] * mood['weight']
                      for mood in artistmoods])
    for mood in artistmoods:
      weight = mood['frequency'] * mood['weight'] / totalweight
      self.moodplays[mood['name']] += 1.0 * weight * plays
    self.totalplays += plays
  
  def getMoodDist(self):
    return [1.0 * self.moodplays[emotion] / self.totalplays
            for emotion in emotions]

playsfile = open('../lastfm-dataset-360K/usersha1-artmbid-artname-plays.tsv', 'rb')
playsreader = csv.reader(playsfile, delimiter='\t')
usersfile = open('../lastfm-dataset-360K/usersha1-profile.tsv', 'rb')
usersreader = csv.reader(usersfile, delimiter='\t')

users = {}#shelve.open('users')
for row in usersreader:
  users[row[0]] = User(row)

usersfile.close()

for row in playsreader:
  if moods.has_key(row[1]) and users.has_key(row[0]):
    users[row[0]].addArtist(row[1], int(row[3]))

playsfile.close()

from scipy.spatial import cKDTree
import numpy as np
import cPickle as pickle

#users = pickle.load(open('users', 'rb'))
userlist = []
moodlist = []
for user in users.iterkeys():
  if users[user].totalplays:  # only consider users with plays
    userlist.append(user)
    moodlist.append(users[user].getMoodDist())

pickle.dump(users, open('users', 'wb'))
del users
#users.clear()
mooddata = np.array(moodlist)
pickle.dump(userlist, open('userlist', 'wb'))
pickle.dump(moodlist, open('moodlist', 'wb'))
pickle.dump(mooddata, open('mooddata', 'wb'))
#del userlist
#del moodlist
tree = cKDTree(mooddata)

#pickle.dump(tree, open('tree', 'wb'))