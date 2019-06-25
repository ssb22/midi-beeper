#!/bin/bash
git pull --no-edit
wget -N http://people.ds.cam.ac.uk/ssb22/mwrhome/midi-beeper.py
git commit -am update && git push
