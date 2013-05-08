import shelve

moods1K = shelve.open('moods1K')
moods360K = shelve.open('moods360K')

artistmoods = shelve.open('artistmoods')

for artist in moods360K.iterkeys():
  artistmoods[artist] = moods360K[artist]

for artist in moods1K.iterkeys():
  if not artistmoods.has_key(artist):
    print 'foo'
    artistmoods[artist] = moods1K[artist]

artistmoods.close()
moods1K.close()
moods360K.close()
