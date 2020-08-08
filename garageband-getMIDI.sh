#!/bin/bash

# Read MIDI data out of saved GarageBand loops.
# Silas S. Brown 2020 - public domain - no warranty.
# Tested on GarageBand '11 6.0.5 on MacOS 10.7.5.

if [ "$(python --version 2>&1|sed -e 's/.* //' -e 's/[.].*//')" == 2 ]; then
  export Python2=python # bundled with Mac OS X 10.14 and below
elif which -s python2; then export Python2=python2 # usually there on 10.14 and below (unless someone removed it?)
elif which -s python2.7; then export Python2=python2.7
elif which -s python2.6; then export Python2=python2.6
elif which -s python2.5; then export Python2=python2.5
else echo "Cannot find Python 2 on this system" 1>&2; exit 1; fi

cd ~/Library/Audio/"Apple Loops/User Loops/"SingleFiles || exit 1
for N in *.aif; do
    if test -e "$N"; then
        mv -iv "$N" /tmp &&
        export M=/tmp/"$(echo "$N"|sed -e s/aif$/mid/)" &&
        "$Python2" -c 'import sys;d=sys.stdin.read();m=d[d.index("MThd"):];sys.stdout.write(m[:m.index("CHS")])' < /tmp/"$N" > "$M" &&
        du -h "$M"
    fi
done
