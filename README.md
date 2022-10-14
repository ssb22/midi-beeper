# midi-beeper
MIDI Beeper from http://ssb22.user.srcf.net/mwrhome/midi-beeper.html
(also mirrored at http://ssb22.gitlab.io/mwrhome/midi-beeper.html just in case)

MIDI beeper is a program to play MIDI files on Linux/BSD by beeping through the computer’s beeper instead of using proper sound circuits. If you try to play chords or polyphony, it will rapidly switch between alternate notes like an old office telephone. It sounds awful, but it might be useful when you really have to play a MIDI file but have no sound device attached. It should work on any machine that has the “beep” command (install “beep” package from your Linux/Unix package manager). It has been tested on a PC speaker and on an NSLU2’s internal speaker.

On the NSLU2, playing music with beep works in Debian 4 (Etch, 2007) but not so well in Debian 5 (Lenny, 2012); you can try compiling this [modified beep.c](http://ssb22.user.srcf.net/mwrhome/beep.c) instead (remember the chmod 4755 mentioned in the man page). I haven’t tried it on more recent distros because my NSLU2 power supply failed and I upgraded to a Raspberry Pi.

RISC OS etc
-----------

If you need to know what a MIDI file sounds like while using a “vanilla” RISC OS machine, edit midi-beeper and set riscos_Maestro to turn it into a converter from MIDI files to Acorn Maestro files. Rather than rapidly switching between notes, this uses true polyphony of up to 8 channels, although Maestro can struggle with rhythm when playing more than 4 channels. The music may not look good in Maestro (which is not a good program for typesetting anyway), but at least it plays.

Alternatively you can use a BBC Micro emulator (or a real BBC Micro if you still have one from the 1980s) and set MIDI beeper to generate BBC Micro code. This uses 3-channel polyphony and can multiplex up to 9 via envelope arpeggiation (3 on the Electron). The tuning can be a bit ‘wobbly’. Here’s an [example SSD of short compositions](http://ssb22.user.srcf.net/mwrhome/bbcmicro.zip) (~60k for ~33½mins).

MIDI beeper can also generate polyphonic square waves itself and feed them to aplay, which might be useful if you need a small MIDI player on a Raspberry Pi running Linux, although too many sound channels can slow this down as it’s only a Python script.

Copyright and Trademarks
------------------------

© Silas S. Brown, Licensed under Apache 2.

* Apache is a registered trademark of The Apache Software Foundation.

* Debian is a trademark owned by Software in the Public Interest, Inc.

* Linux is the registered trademark of Linus Torvalds in the U.S. and other countries.

* Python is a trademark of the Python Software Foundation.

* Raspberry Pi is a trademark of the Raspberry Pi Foundation.

* RISC OS is a trademark of Pace Micro Technology Plc.

* Any other trademarks I mentioned without realising are trademarks of their respective holders.
