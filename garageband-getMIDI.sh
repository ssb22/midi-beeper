#!/bin/bash

# Read MIDI data out of saved GarageBand loops.
# Silas S. Brown 2020,2022 - public domain - no warranty.

# Tested on GarageBand '11 6.0.5 on MacOS 10.7.5:
# New track (Cmd-Shift-N or bottom-left "+" icon),
# Record (if all red and doesn't go green, may hv to reset the MIDI connection, especially if going via a hub)
# (if you want to multi-track, you can join the tracks via Edit / Select All (cmd-A), Edit / Join (cmd-J))
# Edit / Add to loop library, then run this script.

# Ground-bass loops (playback via the Mac):
# GarageBand / Preferences / General,
# "Cycle Recording (Automatically merge Software Instrument recordings when using the cycle region)",
# then record,
# then add a loop but switch OFF Control / Snap to Grid (Cmd-G),
# then record again to add layers to the loop.

# Where to find history:
# https://github.com/ssb22/midi-beeper.git
# and https://gitlab.com/ssb22/midi-beeper.git
# and https://bitbucket.org/ssb22/midi-beeper.git
# and https://gitlab.developers.cam.ac.uk/ssb22/midi-beeper
# and in China: git clone https://gitee.com/ssb22/midi-beeper

if [ "$(python --version 2>&1|sed -e 's/.* //' -e 's/[.].*//')" == 2 ]; then
  Python2=python # bundled with Mac OS X 12.1 and below
elif which -s python2; then Python2=python2 # usually there on 10.14 and below (unless someone removed it?)
elif which -s python2.7; then Python2=python2.7
elif which -s python2.6; then Python2=python2.6
elif which -s python2.5; then Python2=python2.5
else echo "Cannot find Python 2 on this system" 1>&2; exit 1; fi

cd ~/Library/Audio/"Apple Loops/User Loops/"SingleFiles || exit 1
for N in *.aif; do
    if test -e "$N"; then
        mv -iv "$N" /tmp &&
        M=/tmp/"$(echo "$N"|sed -e s/aif$/mid/)" &&
        "$Python2" -c 'import sys;d=sys.stdin.read();m=d[d.index("MThd"):];sys.stdout.write(m[:m.index("CHS")])' < /tmp/"$N" > "$M" &&
        du -h "$M"
    fi
done
