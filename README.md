moodrec
=======

A Mood-based Music Recommendation System

This repository contains code that generates artist-level music recommendations based on data from [Oscar Celma's Last.fm Dataset](http://ocelma.net/MusicRecommendationDataset/index.html) and [The Echo Nest API](http://the.echonest.com/). It depends on SciPy, NumPy, and other odds and ends that you may or may not have to "sudo pip install" (see the import statements throughout the code).

The code is currently in severe need of refactoring (it was mostly written ad hoc/interactively and under time pressure), but it does run and in fact was used for an initial pull so I am uploading it as is. I will update this repository as I have time to clean and generalize the system.

What the code in each folder does, in a nutshell:
- echorun1k and echorun360k pull artist moods for the 1K and 360K datasets from The Echo Nest (moodjoin.py simply combines the resulting dicts into one comprehensive artist-mood lookup table)
- moodrun1k and moodrun360k build user mood profiles based on 1K/360K playback data and the moods pulled from The Echo Nest
- recun1k and recun360k run actual recommendations for the 1K users based on both 1K and 360K data, and report precision/recall
