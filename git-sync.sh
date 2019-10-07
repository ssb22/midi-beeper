#!/bin/bash
git pull --no-edit
wget -N http://ssb22.user.srcf.net/mwrhome/midi-beeper.py
git commit -am update && git push
