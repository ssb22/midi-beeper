#!/usr/bin/env python
# (can be run in either Python 2 or Python 3)

"""MIDI beeper v1.82 (c) 2007-2010,2015-2025 Silas S. Brown
License: Apache 2""" # (see below)

# MIDI beeper is a Python program to play MIDI by beeping
# through the computer's beeper instead of using proper
# sound circuits.  It emulates chords/polyphony.
# It sounds awful, but it might be useful when no sound device
# is attached.  It should work on any machine that has the
# "beep" Linux package, like old NSLU2 network storage devices.
# (On NSLU2 do 'sudo modprobe isp4xx_beeper' before running)

# Can also install a MIDI file into the GNU GRUB bootloader
# (sudo access required; does not work on all machines
# e.g. some laptops have no beeper)
grub = 0 # or run with --grub

# Can also play MIDI files using square-wave synthesis with aplay
# (e.g. on Raspberry Pi) - set aplay below if you want this instead.
# Set it to a volume level, e.g. aplay = 100
aplay = 0 # or set APLAY_VOL environment variable

# Can also convert MIDI files to RISC OS Maestro music files
# for playing (but not typesetting well) on 'vanilla' RISC OS.
# Set riscos_Maestro = 1 below if you want this.
# (Defaults to 1 when script is run on RISC OS, unless one
# of the BBC Micro options is specified instead.)
riscos_Maestro = 0 # or run with --maestro

# Can also convert MIDI files to BBC Micro programs
# (printed to standard output).  Set bbc_micro below:
bbc_micro = 0 # or run with --bbc
acorn_electron = 0 # or run with --electron: Acorn Electron version (more limited)
bbc_binary = 0 # or run with --bbc-binary: make the above use direct memory access instead of DATA (packs more in but harder to save/edit)
bbc_ssd = 0 # or run with --bbc-ssd: writes an SSD image (for an emulator) instead of printing keystrokes to standard output (set environment DFS_TITLE to title the disk; disk will contain one BBC program for each MIDI file on the command line + bootloader)
bbc_sdl = 0 # or run with --bbc-sdl: makes the BBC Micro code compatible with R.T.Russell's BBC BASIC for SDL.  Code still runs on the real BBC too, but is larger.

# HiBasic (Tube) support (~30k for programs) fully works
# Bas128 support (64k for programs) works but (a) bank-switching delays impact the timing of shorter notes and (b) bbc_binary option can cause "Wrap" errors during input.
# However, bbc_binary and bbc_ssd options should pack data into a smaller space so normal BASIC can be used.

# Can also convert a MIDI file to DOS QBASIC code
qbasic = 0 # or run with --qbasic

# Can also get 2 macOS voices to sing text:
# "Organ" 2nd octave Bb to 5th octave D
# "Joelle" (less melodious) 4th C# to 5th C#
# force_monophonic is implied with these, and the "sox" command is also required.
# No melisma; likely works best with patter songs.
mac_voice = "" # or run with --Organ or --Joelle
# put syllables into environment variable SaySyls
# (comma separated; may need to change spelling)
mac_voice_praat_correction = 0 # or run with --praat requires Praat, recommended for Joelle
# - the Apple Software License Agreement says you may use
# these voices "to create your own original content and
# projects for your personal, non-commercial use" so you may
# want to take extra caution you're not getting any revenue.
# (This does not affect your Apache 2 rights to this script)

voice_json = 0 # or run with --json: put environ
# variable SingWords to space-separated words with
# hyphen-separated syllables, preceded by singer
# names in [...], for podcast:transcript on stdout
# - tested on Anytime Player, Anemone DAISY Maker,
# and AntennaPod 3.5
Anytime_Player_bug_workaround = 1

force_monophonic = 0  # set this to 1 to have only the top line (not normally necessary)

maxTime = 0 # set to number of seconds (or set maxTime environment variable) to limit length of playback, 0 = unlimited

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# History is in https://github.com/ssb22/midi-beeper.git
# and https://gitlab.com/ssb22/midi-beeper.git
# and https://bitbucket.org/ssb22/midi-beeper.git
# and https://gitlab.developers.cam.ac.uk/ssb22/midi-beeper
# and in China: https://gitee.com/ssb22/midi-beeper
# but some early versions are missing from these repositories

# ----------------------------------------------------

import os,sys
from struct import pack, unpack
if sys.version_info < (2,2): sys.stderr.write("Warning: Not tested on Python 2.1 and earlier\nYou might need to introduce long() in various places\nto avoid overflow after 35 minutes\n\n") # due to microseconds count (if you really want to listen to beeped MIDI that long)
def delArg(a):
  found = a in sys.argv
  if found: sys.argv.remove(a)
  return found
if delArg('--maestro'): riscos_Maestro = 1
if delArg('--bbc'): bbc_micro = 1
if delArg('--electron'): acorn_electron = 1
if delArg('--bbc-binary'): bbc_binary=bbc_micro=1
if delArg('--bbc-ssd'): bbc_ssd=bbc_micro=1
if delArg('--bbc-sdl'): bbc_sdl=bbc_micro=1
if delArg('--grub'): grub=1
if delArg('--qbasic'): qbasic=1
if delArg('--Organ'): mac_voice="Organ"
if delArg('--Joelle'): mac_voice="Joelle"
if delArg('--praat'): mac_voice_praat_correction=1
if delArg('--json'): voice_json=1
assert not (bbc_sdl and (bbc_binary or bbc_ssd)), "bbc_sdl not compatible with bbc_binary or bbc_ssd"

on_riscos = sys.platform.lower().find("riscos")>=0
if on_riscos and not (bbc_micro or acorn_electron): riscos_Maestro = 1
elif not aplay: aplay=int(os.environ.get("APLAY_VOL",0))
if riscos_Maestro or bbc_micro or acorn_electron or grub or qbasic or mac_voice or voice_json: aplay = 0

# To add a new type of beeper, get the following 'if' block to do any necessary global setup and to define the appropriate version of the per-file init() and of add_midi_note_chord(), then check the 'if' after 'ensure flushed' at end, and quantiseTo logic
if aplay:
  rate = 8000 # can just about manage 3 or 4 channels on a Raspberry Pi if it isn't doing anything else
  o = os.popen("aplay -q -t raw -c 1 -f U8 -r %d" % rate,"w")
  try:
    oWrap,o = o,o.buffer # Python 3
    def bchr(n): return bytes((n,))
  except AttributeError: bchr = chr # Python 2
  def init(): pass
  def chord(freqs,millisecs):
    samples = millisecs * rate / 1000 ; halfPeriods = []
    for f in freqs: halfPeriods.append(rate/2.0/f)
    assert not 0 in halfPeriods
    nextFlips = list(map(int,halfPeriods))
    counts = [1]*len(halfPeriods)
    val = 0
    if nextFlips: next=[aplay/len(halfPeriods)]*len(halfPeriods)
    else: next = []
    t = 0
    while t < samples:
        while t in nextFlips:
            i = nextFlips.index(t)
            val += next[i]
            next[i] = -next[i]
            counts[i] += 1
            nextFlips[i] = int(counts[i]*halfPeriods[i]) # necessary especially at low rates as periods are rarely integers
        o.write(bchr(int(val))) ; t += 1
  def add_midi_note_chord(noteNos,microsecs):
    chord(list(map(to_freq,noteNos)),microsecs / 1000)
elif bbc_micro or acorn_electron:
  # This is a compact BBC Micro program to multiplex up to
  # 9 channels of sound onto the BBC Micro's 3 channels.
  # Basically uses ENVELOPEs to do the pitch multiplexing.
  # BBC Micro's BASIC encouraged the use of @% through Z% by reserving memory for them (heap is typically small), so code can be quite obscure.
  bbc_micro = ["FOR C%=16 TO 19:SO.C%,0,0,0:N.\n" # flush all sound buffers, just in case
               "N%=0:" # N% = next available envelope number (1-16 if not using BPUT#, otherwise 1-4 but we don't want to redefine envelopes that are already associated with notes in the buffer)
               "DIM c%(8)\n" # c% is the current value of each 'channel'; 252 i.e. 4*63 is used for silence.  Data read tells the program what changes to make to this array for the next chord and for how long to sound it (see add_midi_note_chord below).
               "FOR D%=0 TO 8:c%(D%)=252:N.\n" # all channels start with silence
               # The next few lines can be abbreviated thus: "REP.C%=0:REP.READD%:c%(C%)=(D%A.63)*4:I%=(D%DIV64)+1:C%=C%+I%:U.I%=4:READD%:REP.U.AD.-6>3:F.I%=0TO6S.3:S%=0:T%=0:IFc%(I%)=252:V%=0:EL.IFc%(I%+1)=252:V%=1:EL.S%=1:Q%=c%(I%+1)-c%(I%):IFc%(I%+2)=252:V%=2:EL.R%=c%(I%+2)-c%(I%+1):T%=1:V%=3" (234 keystrokes, out of a limit of 238).  But Bas128 is still too slow, even with the read loop all on 1 line like this.
               "REP.C%=0\n" # C% is the write-index for our 'current chord' c%
               "REP.READ D%\n" # lowest 6 bits = semitone no. (which we multiply by 4 to get pitch number); highest 2 bits = array-pointer increment - 1 (so we can increment 1, 2 or 3 places; an "increment" of 4 means end of chord)
               "c%(C%)=(D% AND 63)*4\n" # set pitch
               "I%=(D% DIV 64)+1:C%=C%+I%:U.I%=4\n" # c% array now all set
               "READ D%\n" # This will be the duration of the chord just specified
               "REP.U.ADVAL(-6)>3\n" # BBC Micro quirk: contrary to what the manual says (in at least some printings), the number of notes in each channel's "to be played" buffer before the program waits can be 5 not 4 (on at least some versions of the BBC).  This, together with the current note, means we might need a total of 6*3=18 envelopes, and we have only 16 slots.  Hence the ADVAL loop to avoid filling the buffer completely.
               "FOR I%=0 TO 6 STEP 3\n" # handling our 'channels' as triples, up to 3 being arpeggiated into one BBC Micro channel; I% will be the index-start of each triple
               "S%=0:" # will be set to 1 if the second section of the envelope is used
               "T%=0\n" # will be set to 1 if the third section of the envelope is used
               "IF c%(I%)=252:V%=0:" # no volume if entire channel is silent (see special case below)
               "ELSE IF c%(I%+1)=252:V%=1:" # entire channel has just one note, so play it at "volume 1".  TODO: if c%(I%) is high, consider 'wobbling' the pitch to mask the SN76489's tuning inaccuracy of high notes, e.g. by setting S%=1:Q%=1.  This can be done inline (using the fact that BBC BASIC represents true as -1) using something like "S%=-(c%(I%)>150):Q%=S%:" here.  Would need to check if 150 really is a good threshold, and, if it works, also modify the datBytes string in make_bbcMicro_DFS_image: beware line-length bytes etc; will probably have to stop using the 'abbreviated' version if these extra 2 assignments would make the line too long.  Also check the bbc_sdl .replace of V%=1 below doesn't undo it (and consider turning it off if INKEY(-256) detects SDL-etc, as that environment has better tuning to begin with)
               "ELSE S%=1:Q%=c%(I%+1)-c%(I%):" # channel has at least 2 notes, so set Q% to the first pitch difference, and set S% to enable 2nd section of envelope
               "IF c%(I%+2)=252:V%=2:" # channel has exactly 2 notes, so play it at "volume 2"
               "ELSE R%=c%(I%+2)-c%(I%+1):T%=1:V%=3\n" # channel has 3 notes, so play it at "volume 3", set R% to second pitch difference, and set T% to enable 3rd section of envelope
               # (here ends what can be abbreviated as per the 'abbreviated' comment above)
               "IF V%:" # The following operations are done only if volume is not 0.  We special-case volume 0 so it doesn't use an envelope at all; this (along with the ADVAL loop above) seems to make things a little more robust, as short pauses between notes are frequent.  A special-case of volume 0 is needed anyway in the Electron version below: the Electron uses a ULA with only 1 channel and 1 volume; the last 6 envelope parameters are ignored and setting them to 0 does NOT switch off the sound like it does on the BBC.
               "V%=V%*24+55:" # 79, 103 or 127
               "N%=N%+1:IF N%=17:N%=1" # next available envelope number
               "\nIF V%:" # (still only if volume is not 0)
               "ENV.N%," # setting envelope number N%
               "3," # length of each step in centiseconds
               "0," # first section should sound the 1st note
               "Q%," # second section adds Q% to the pitch for each step
               "R%," # third section adds R% to the pitch for each step
               "1," # first section should have 1 step (for sounding the 1st note)
               "S%," # second section should have either 0 steps (if not used) or 1 step (for sounding note + Q%)
               "T%," # third section should have either 0 steps (if not used) or 1 step (for sounding note + Q% + R%)
               "V%,0,0,-V%," # ADSR (attack, decay, sustain, release) change per step
               "V%," # attack final volume
               "V%" # decay final volume
               ":V%=N%\n" # for the SOUND command below
               "SO.513+(I%DIV3)," # 512 = sync=2 i.e. 3 channels are to receive a note before it is to start; +1 because we're not using channel 0
               "V%," # envelope number or 0
               "c%(I%)," # first pitch of the arpeggio (or plain pitch if no arpeggio)
               "D%\n" # duration
               "N.:U.D%=0:END"]
  if acorn_electron:
    # Cut-down version of the above code for the Electron:
    bbc_micro=["""SO.1,0,0,0
N%=0:DIM c%(2)
FOR D%=0 TO 2:c%(D%)=252:N.
REP.C%=0
REP.READ D%
c%(C%)=(D% AND 63)*4
I%=(D% DIV 64)+1:C%=C%+I%:U.I%=4
READ D%
REP.U.ADVAL(-6)>3
S%=0:T%=0:P%=c%(0)
IF P%=252:V%=0:ELSE V%=1:IF c%(1)<>252:S%=1:Q%=c%(1)-P%:IF c%(2)<>252:R%=c%(2)-c%(1):T%=1
IF V%:N%=N%+1:IF N%=17:N%=1
IF V%:ENV.N%,3,0,Q%,R%,1,S%,T%,126,0,0,-126,126,126:V%=N%
SO.1,V%,P%,D%
U.D%=0:END"""] # the 126,etc is there so that if this program is accidentally run on the BBC Micro instead of the Electron it'll at least sound something
    current_array = [63]*3
  else: current_array = [63]*9
  if bbc_sdl: bbc_micro[0]="COLOUR 128:COLOUR 7:CLS\n"+bbc_micro[0] # BBC SDL defaults to white background: be easier on the eyes by having dark mode like the original BBC
  if bbc_ssd:
    bbc_micro = [] # we'll put tokenised program in later
    bbc_binary = 1
    bbc_files = []
  elif bbc_binary: # don't use AUTO; change to read RAM
    lines = ("E%=TOP:" + bbc_micro[0]).split("\n") ; bbc_micro = []
    for i in range(len(lines)):
      bbc_micro.append("%d%s" % (i+1,lines[i]))
    bbc_micro=[
      "IF(PA. A.&FF00)>&E00:PA.=&E00:*ROM" # reclaim space from Model B DFS if applicable (may or may not be needed depending on which DFS is in use and how much space it takes, which we won't know at code-generation time, so test at runtime if we're above E00 and not in second-processor addresses.  If using Acorn's DFS on Model B, may be able to reduce PAGE from &1900 to &1800 if not using *BUILD, to &1700 if no other ROMs will borrow space from DFS, to &1300 if using OPEN on max 1 file, or to &1100 if not using OPEN or SPOOL/EXEC, but Watford DFS and others will be different so it's safer to just turn it off.)
      "NEW"]+bbc_micro
    # Could see the Mode 0 memory map with: MO.0:V.23;12;0;0;0;0;28,0,12,63,0
    # For larger MIDIs, can see sound queues etc (but not BASIC stack) via: MO.6:V.23;12;0;0;0;0;23;0;0;0;0;0:RUN
    # (can also try MO.4)
    bbc_micro = ["\n".join(bbc_micro).replace("READ D%","D%=?E%:E%=E%+1")]
  keystroke_limit = 238
  if bbc_sdl: keystroke_limit -= 5 # assuming up to 3 keystrokes for the backward-compatibility line number (can be up to 5, but if it gets as high as 4 then we're looking at a 230k+ program which is not going to fit in any version of the BBC Micro anyway so we might as well disregard the BBC Micro's keystroke buffer limit), + 2 keystrokes for "D." to "DATA"
  def add_midi_note_chord(noteNos,microsecs):
    duration = int((microsecs*20+500000)/1000000)
    while duration > 254: # unlikely but we should cover this
      add_midi_note_chord(noteNos,254*1000000/20)
      duration -= 254
    if not duration: return
    def f(n): # convert to SOUND/4 and bound the octaves
      n -= 47 # MIDI note 69 (A4) is pitch 88 i.e. 4*22
      while n<0: n+=12 # TODO: unless we want to make a bass line using SOUND 0,-V,3,D with SOUND 1,E,P+188,D (won't work on acorn_electron; envelope E will have to set its volume params to 0, or stick with single note), or SO.0,-V,2,D for approx. 1 tone below note 0 (which doesn't tie up channel 1).  Would need to know total number of notes there'll be before deciding if can do this.  Anyway such low notes are rather indistinct on BBC hardware.
      while n>=63: n-=12 # we're using 63 for rest
      return n
    if acorn_electron: noteNos = noteNos[-3:]
    noteNos = list(map(f,noteNos[-9:]))
    while len(noteNos)<3: noteNos.append(63)
    if bbc_sdl and (len(noteNos)>6 or (acorn_electron and len(noteNos)>2)) and not '1.13+' in bbc_micro[0]:
      bbc_micro[0]="REM As there are chords with three\nREM notes per channel, you will need\nREM BBC SDL 1.13+ or 'real' BBCBASIC\nREM for the ENVELOPEs to sound right.\nREM\n"+bbc_micro[0] # see bbcsdl bug #3
    if not acorn_electron:
      # Divide the notes evenly among BBC channels,
      # and if need arpeggiation, prefer it in the bass.
      for a,b in [(9,0),(7,0),(9,3),(8,3),(9,6),(9,6)]:
        if len(noteNos)<a: noteNos.insert(len(noteNos)-b,63)
    # Check range of arpeggiation pitch increments, adjust
    # octave as needed (too high shouldn't happen in
    # sensible music, but double-bass too low is possible)
    for i in range(0,len(noteNos),3):
      for j in range(i+1,i+3):
        if noteNos[j]==63: break
        while noteNos[j]>noteNos[j-1]+31: noteNos[j]-=12
        while noteNos[j]<noteNos[j-1]-32: noteNos[j]+=12
    # Now calculate the DATA numbers:
    o = [] ; curSkip = 0
    for i in range(len(current_array)):
      if noteNos[i]==current_array[i] and o and curSkip<2:
        curSkip += 1 ; continue
      if curSkip: o[-1] += curSkip*64
      curSkip = 0 ; current_array[i] = noteNos[i]
      if noteNos[i:] == current_array[i:]:
        o.append(noteNos[i]+3*64) ; break # last change
      else: o.append(noteNos[i])
    o.append(duration)
    if bbc_binary:
      for i in o: bbc_micro.append(int(i))
    else: # self-contained typeable BBC BASIC, assuming AUTO
      o = ",".join(map(lambda x:("%d"%x), o))
      if len(bbc_micro)>1 and len(bbc_micro[-1])+len(o)+1 <= keystroke_limit: bbc_micro[-1] += ','+o
      else: bbc_micro.append("D."+o)
  def init():
    global dedup_microsec_quantise
    dedup_microsec_quantise = 50000 # 1000000/20
elif riscos_Maestro:
  allowed_BPMs = [40, 50, 60, 65, 70, 80, 90, 100, 115, 130, 145, 160, 175, 190, 210]
  default_bpm = max(allowed_BPMs) # theoretically gives the most accuracy
  hemi_microsecs = int(3750000/default_bpm) # for now (ms/hemi = beat/hemi / (b/min * min/microsec) = 1/16 / (bpm / 60000000) = 60000000/16/bpm)
  def add_midi_note_chord(noteNos,microsecs):
    noteNos.reverse()
    global current_time
    for n in current_chord[:]:
      if n.noteNo in noteNos: noteNos.remove(n.noteNo) # just extend the currently-playing note
      else: # stop that note:
        assert n.noteNo not in noteNos # shouldn't have any duplicates in that list
        n.end(current_time)
        n.quantTo(hemi_microsecs)
        foundC = False
        for i in [0,4,6,2,1,3,5,7]: # allocate channels in that order so 2-stave (0-3,4-6/7), 3-stave (0,1-4,5-6/7) and 4-stave (0-1,2-3,4-5,6/7) views work vaguely sensibly
            c = riscos_channels[i]
            if not c or c[-1].endTime <= n.startTime:
                c.append(n) ; foundC = True ; break
        if not foundC: sys.stderr.write("Insufficient RISC OS channels: dropping note %d\n" % n.noteNo)
        current_chord.remove(n)
    for noteNo in noteNos: current_chord.append(MaestroMidiNote(noteNo,current_time)) # newly-started notes
    current_time += microsecs
  def maestroData():
    queues = []
    for c in riscos_channels:
      timeCountFrom = 0 ; chan = []
      barHemisLeft = 64 # assumes 4/4 with no anacrusis
      for n in c:
          nn,barHemisLeft = n.note(hemi_microsecs,timeCountFrom,barHemisLeft)
          chan.append(nn)
          timeCountFrom = n.endTime
      queues.append(''.join(chan))
    staves = 0
    for q in queues:
      if q and staves<4: staves += 1 # helps with more accurate playing if each part has its own stave (pity there's a maximum of 4)
    if not staves: staves = 1
    return Maestro_header+setBPM_block(default_bpm)+setVolumes_block()+musicData_block(queues)+setStaves_block(staves)+setInstruments_block()
  if type("")==type(u""): # Python 3
    maestroData_real = maestroData
    def maestroData(): return maestroData_real().encode('latin1')
  def init():
    global current_chord,current_time,riscos_channels
    current_chord = [] ; current_time = 0 ; riscos_channels = [[],[],[],[],[],[],[],[]]
elif mac_voice:
  force_monophonic = 1
  if mac_voice=="Organ": noteNoToPbas,minNote,maxNote=lambda x:132.96*math.log(x+49.7)-565.5,46,74
  elif mac_voice=="Joelle": noteNoToPbas,minNote,maxNote=lambda x:66.3*math.log(x-14)-210,61,73 # TODO: do these values depend on the exact syllable?
  else: assert 0, "unknown mac_voice "+repr(mac_voice)+" (case sensitive)"
  if mac_voice_praat_correction: minNote,maxNote=0,127 # we can go outside the normal range if praat will fix it
  def init():
    global pcmData,SaySyls
    pcmData = []
    SaySyls = os.environ["SaySyls"].split(",")
    SaySyls.reverse() # so can use pop()
  def add_midi_note_chord(noteNos,microsecs):
    if not microsecs: return
    if noteNos:
      if not SaySyls:
        sys.stderr.write("WARNING: ran out of syllables, check the value of SaySyls\n") ; SaySyls.append("la")
      ThisSyl = SaySyls.pop()
      if not ThisSyl: noteNos = [] # nothing between two commas = omit note (might be useful for small variations between verses)
    if not noteNos: return pcmData.append(b"\0"*int(2*44100*microsecs/1000000)) # rest
    note = noteNos[0]
    while note<minNote: note += 12
    while note>maxNote: note -= 12
    pid = os.getpid() # in case parallelised
    cmd = 'say -v %s -r %d "[[pbas %.1f]]%s" -o %d.aiff' % (mac_voice,(60 if mac_voice=="Joelle" else min(100,int(60000000/microsecs))),noteNoToPbas(note),ThisSyl,pid) # must say at most one syllable per command for pbas to work properly on these voices
    sys.stderr.write(cmd+"\n") ; os.system(cmd)
    lenCheck=os.popen('sox %d.aiff -t raw -r 44100 -c 1 -b 8 -' % pid)
    tempoCorrection = len((lenCheck.buffer if hasattr(lenCheck,'buffer') else lenCheck).read())*1000000/44100.0/microsecs
    b=os.popen('sox %d.aiff -t raw -r 44100 -c 1 -b 16 - tempo %g 10' % (pid,tempoCorrection))
    pcmData.append((b.buffer if hasattr(b,'buffer') else b).read())
    os.remove("%d.aiff" % pid)
    if mac_voice_praat_correction:
      b=os.popen('sox -t raw -r 44100 -c 1 -b 16 -e signed - %d.wav' % pid,'w')
      (b.buffer if hasattr(b,'buffer') else b).write(pcmData[-1]) ; b.close()
      open('%d.praat' % pid, 'w').write('Read from file... %d.wav\nChange gender... 75.0 600.0 1.0 %d 1.0 1.0\nnowarn Write to WAV file... %d-1.wav\nRemove\n' % (pid,to_freq(note),pid)) # misnomer: this is NOT really changing gender with these parameters, it's normalising frequency (it's the same trick I did to get Yali's Mandarin first tone syllables all the same pitch for Gradint in 2008)
      os.system('/Applications/Praat.app/Contents/MacOS/Praat %d.praat' % pid)
      os.remove('%d.wav' % pid)
      os.remove('%d.praat' % pid)
      b=os.popen('sox %d-1.wav -t raw -r 44100 -c 1 -b 16 -' % pid)
      pcmData[-1] = (b.buffer if hasattr(b,'buffer') else b).read()
      os.remove('%d-1.wav' % pid)
elif voice_json:
  force_monophonic = 1
  def init():
    global SingWords,currentSpeaker,microsecsSoFar,sylsLeft
    SingWords = os.environ["SingWords"].split()
    SingWords.reverse() # so can use pop()
    currentSpeaker = "singer"
    microsecsSoFar = int(os.environ.get("SingMicrosecsOffset","0")) # (in case it won't be at the very start of the audio)
    sylsLeft = 0
    print('{"version":"1.0.0","segments":[')
  def setupNextWord():
    isSpeaker = 0
    while True:
      word = SingWords.pop()
      global currentSpeaker
      if word.startswith('[') or isSpeaker:
        if word.startswith('['): currentSpeaker=""
        currentSpeaker += word.replace("[","").replace("]","")
        isSpeaker = not word.endswith(']')
        if isSpeaker: currentSpeaker += " "
      else:
        global currentWord,sylsLeft ; currentWord,sylsLeft = word.replace('-',''),len(word.split('-'))
        if Anytime_Player_bug_workaround: # v1.3.5 drops space before single-letter words
          while SingWords and len(SingWords[-1])==1:
            currentWord += " "+SingWords.pop()
            sylsLeft += 1
        break
  def add_midi_note_chord(noteNos,microsecs):
    global microsecsSoFar, sylsLeft, wordStartMS
    startM,microsecsSoFar = microsecsSoFar,microsecsSoFar+microsecs
    if not noteNos or not microsecs: return
    if not sylsLeft:
      wordStartMS = startM ; setupNextWord()
    sylsLeft -= 1
    if not sylsLeft: print('{"speaker":"%s","startTime":%g,"endTime":%g,"body":"%s"}%s' % (currentSpeaker,wordStartMS/1000000.0,microsecsSoFar/1000000.0,currentWord,(',' if SingWords else ((',{"speaker":"%s","startTime":%g,"endTime":%g,"body":""}' % (currentSpeaker,microsecsSoFar/1000000.0,microsecsSoFar/1000000.0)) if Anytime_Player_bug_workaround else '')))) # (v1.3.5 won't display last word so add a placebo)
elif qbasic:
  def init():
    global basData, dedup_microsec_quantise
    basData = [b'PLAY "T255L64MLMB"']
    dedup_microsec_quantise = 60000000/255/(64/4)
    basData+=[b'ON PLAY(1) GOSUB playTune\nr=0:PLAY ON:GOSUB playTune\nPRINT "Press any key to stop"\nDO: LOOP UNTIL INKEY$ <> ""\nEND\nplayTune:\nIF r<=0 THEN READ p$,r\nIF p$ = "@" THEN END\nPLAY p$\nr = r - 1\nRETURN'] # Won't work in the earlier GW-BASIC: yes you can number the lines (including for the GOSUB), rewrite the loop to WHILE INKEY$="":WEND, and paste into DOSBox to work around gwbasic being unable to load this program from a text file, but the ON PLAY check gets dropped after about 1 chord.
  def add_midi_note_chord(noteNos,microsecs):
    notes = []
    for n in noteNos:
      n -= 23
      while n < 1: n += 12
      while n > 84: n -= 12
      notes.append(b"N%d" % n)
    if not notes: notes=[b"N0"]
    notes = b"%s,%d" % (b"".join(notes),max(1,int(microsecs/dedup_microsec_quantise/len(notes))))
    if basData and basData[-1].startswith(b"DATA ") and len(basData[-1])+len(notes) < 79: basData[-1] += b","+notes # 80th col is scrollbar
    else: basData.append(b"DATA "+notes)
elif grub:
  pulselength_milliseconds = 10
  bpm = int(60000/pulselength_milliseconds)
  assert pulselength_milliseconds == int(60000/bpm), "rounding error with this pulselength"
  if os.path.exists('/boot/grub2'): grub="grub2" # Red Hat etc
  elif os.path.exists('/boot/grub'): grub="grub" # Debian
  else: raise Exception("Can't find GRUB on this system")
  grub_out = os.popen("sudo bash -c '(grep -v ^GRUB_INIT_TUNE < /etc/default/grub;echo GRUB_INIT_TUNE=\\\"/boot/"+grub+"/tune\\\")>/etc/default/grub0;mv /etc/default/grub0 /etc/default/grub;cat > /boot/"+grub+"/tune;if [ -e /boot/efi/EFI/redhat/grub.cfg ]; then grub2-mkconfig -o /boot/efi/EFI/redhat/grub.cfg; else "+grub+"-mkconfig -o /boot/"+grub+"/grub.cfg; fi'","w")
  try: gWrap,grub_out = grub_out,grub_out.buffer # Python 3
  except AttributeError: pass # Python 2
  grub_out.write(pack('<I',bpm))
  def init():
    global dedup_microsec_quantise
    dedup_microsec_quantise = 1000*int(1000/pulselength_milliseconds)
  def add_midi_note_chord(noteNos,microsecs):
    millisecs = microsecs / 1000
    freqs = list(map(to_freq,noteNos))
    if not freqs: freqs = [0]
    if len(freqs)==1: grub_out.write(pack('<HH',int(freqs[0]),int(millisecs/pulselength_milliseconds)))
    else:
      for _ in xrange(max(1,int(millisecs/(len(freqs)*pulselength_milliseconds)))):
        for f in freqs: grub_out.write(pack('<HH',int(f),1))
else: # beep
  # NSLU2 hack:
  try: event=open("/proc/bus/input/devices").read()
  except IOError: event=""
  if "ixp4xx beeper" in event:
    h=event[event.find("Handlers=",event.index("ixp4xx beeper")):]
    event="-e /dev/input/"+(h[:h.find("\n")].split()[-1])
    os.system("sync") # just in case (beep has been known to crash NSLU2 Debian Etch in rare conditions)
  else: event=""

  def init():
    global cumulative_params
    cumulative_params = []
  min_pulseLength, max_pulseLength = 10,20 # milliseconds
  repetitions_to_aim_for = 1 # arpeggiating each chord only once will do if it's brief
  def chord(freqList,millisecs):
    if not millisecs: return ""
    elif not freqList: return " -D %d" % (millisecs,) # rest
    elif len(freqList)==1: return " -n -f %d -l %d" % (freqList[0],millisecs) # one note
    else:
        pulseLength = max(min(millisecs/len(freqList)/repetitions_to_aim_for,max_pulseLength),min_pulseLength)
        return (" -D 0".join([chord([f],pulseLength) for f in freqList]))*max(1,int(millisecs/pulseLength/len(freqList))) # (max with 1 means at least 1 repetition - prefer a slight slow-down to missing a chord out)
    # (the above -D 0 is necessary because Debian 5's beep adds a default delay otherwise)

  command_line_len = 80000 # reduce this if you get "argument list too long" (NB the real limit is slightly more than this value)

  def runBeep(params):
    while " -n" in params: # not entirely silence
        params=params[params.find(" -n")+3:] # discard the initial "-n" and any delay before it
        brkAt = params.find(" -n",command_line_len)
        if brkAt>-1: thisP,params = params[:brkAt],params[brkAt:]
        else: thisP,params = params,""
        os.system("beep "+event+" "+thisP)

  def add_midi_note_chord(noteNos,microsecs):
    millisecs = microsecs / 1000
    if noteNos and cumulative_params and not "-D" in cumulative_params[-1].split()[-2:]: cumulative_params.append("-D 0") # necessary because Debian 5's beep adds a default delay otherwise
    cumulative_params.append(chord(list(map(to_freq,noteNos)),millisecs))

def make_bbcMicro_DFS_image(datFiles):
  opt4 = 3 # exec !BOOT
  disk_title = os.environ.get("DFS_TITLE","")
  disk_title += "\0"*max(0,12-len(disk_title))
  # catalogue is 31 items but we'll do !BOOT separately
  catNames,catInfo,catNo = ["\0"*8]*31,["\0"*8]*31,0
  data = "*BASIC\r"
  assert all(len(f)<=7 and re.match('^[A-Za-z0-9]*$',f) for f,_ in datFiles), "please keep DFS filenames to 7-char alphanumeric "+repr([f for f,_ in datFiles])
  if "BOOT_COPYRIGHT" in os.environ: data += "\rREM "+os.environ["BOOT_COPYRIGHT"]+"\r\r" # TODO: document this?
  if len(datFiles)==1: data += ('LOAD "%s"\rLIST\rRUN\r' % datFiles[0][0])
  else: data += "*CAT\r"+"REP.U.AD.-6=15:".join(('CH."%s"\r' % f) for f,_ in datFiles)
  catNames[0]="!BOOT  $"
  catInfo[0]="".join([
    "\0"*4, # !BOOT lsb-msb Load, lsb-msb Exec
    chr(len(data)&0xFF)+chr(len(data)>>8), # !BOOT len
    "\0", # no >64k options or high start-sector bits
    "\2", # starts on sector 2
    ])
  data += "\0"*((256-(len(data)%256))&0xFF) # pad !BOOT
  for fname,datBytes in datFiles:
    catNo += 1; assert catNo<31,"Catalogue full"
    lomem_set = "\xd2=\xb8P+"+str(len(datBytes)-1)
    assert not acorn_electron, "make_bbcMicro_DFS_image is hard-coded to use the BBC Micro reader, not Electron"
    datBytes="\r\x00\x00"+chr(len(lomem_set)+4)+lomem_set+"\r\x00\n@E%=\xb8P:\xe3C%=16\xb819:\xd4C%,0,0,0:\xed:N%=0:\xdec%(8):\xe3D%=0\xb88:c%(D%)=252:\xed\r\x00\x14\xe5\xf5:C%=0:\xf5:D%=?E%:E%=E%+1:c%(C%)=(D%\x8063)*4:I%=(D%\x8164)+1:C%=C%+I%:\xfdI%=4:D%=?E%:E%=E%+1:\xf5:\xfd\x96-6>3:\xe3I%=0\xb86\x883:S%=0:T%=0:\xe7c%(I%)=252:V%=0:\x8b\xe7c%(I%+1)=252:V%=1:\x8bS%=1:Q%=c%(I%+1)-c%(I%):\xe7c%(I%+2)=252:V%=2:\x8bR%=c%(I%+2)-c%(I%+1):T%=1:V%=3\r\x00\x1e'\xe7V%:V%=V%*24+55:N%=N%+1:\xe7N%=17:N%=1\r\x00(4\xe7V%:\xe2N%,3,0,Q%,R%,1,S%,T%,V%,0,0,-V%,V%,V%:V%=N%\r\x002$\xd4513+(I%\x813),V%,c%(I%),D%:\xed:\xfdD%=0\r\xff"+datBytes # This essentially tokenises the program with the 'abbreviated' version of the loop (and indirection instead of READ).  If changing it, the embedded binary line lengths will also need updating.
    catNames[catNo]=fname+' '*(7-len(fname))+'$'
    catInfo[catNo] = "".join([
      "\0"*4, # lsb-msb Load, lsb-msb Exec (apparently not used for BASIC programs)
      chr(len(datBytes)&0xFF),chr(len(datBytes)>>8),
      chr((2+int(len(data)/256))>>8), # should be max 2 bits (protected by whole-disk-size assert below)
      chr((2+int(len(data)/256))&0xFF), # start sector
    ])
    data += datBytes
    data += "\0"*((256-(len(data)%256))&0xFF) # pad
  sectors = 2+len(data)/256
  if sectors<400: sectors=400 # 40 tracks
  elif sectors<800: sectors=800 # 80 tracks
  else: assert 0, "Disk image too full" # (can in theory go to 1023 sectors, but no real hardware would support it)
  return "".join([
    disk_title[:8],
    "".join(catNames),
    disk_title[8:12],
    "\1", # disk cycle (BCD, incremented each time catalogue is written)
    chr((1+catNo)*8),
    chr((sectors>>8)+16*opt4),
    chr(sectors&0xFF),
    "".join(catInfo),
    data.rstrip("\0")])
if type("")==type(u""): # Python 3
  real_make_bbcMicro_DFS_image = make_bbcMicro_DFS_image
  def make_bbcMicro_DFS_image(datFiles):
    return real_make_bbcMicro_DFS_image(datFiles).encode('latin1')

dedup_microsec_quantise = 0 # for handling 'rolls' etc (currently used by bbc_micro, qbasic, grub; TODO: default 'beep' cmd also? but would need to interact with its variable pulse length)
def dedup_midi_note_chord(noteNos,microsecs):
  if force_monophonic and noteNos: noteNos=[max(noteNos)]
  else: noteNos.sort()
  global dedup_chord,dedup_microsec
  if dedup_microsec_quantise and not microsecs==None:
    global dedup_microsec_error
    microsecs += dedup_microsec_error ; oldM = microsecs
    quantiseTo = dedup_microsec_quantise
    if (qbasic or grub) and noteNos: quantiseTo *= len(noteNos)
    microsecs = int((microsecs+quantiseTo/2)/quantiseTo) * quantiseTo
    dedup_microsec_error = oldM - microsecs
  if noteNos == dedup_chord and microsecs:
    # it's just an extention of the existing one
    dedup_microsec += microsecs
    return
  elif microsecs==0: return # too short, quantise out (and don't have to change dedup_chord because the next one might immediately revert to it if this is a 'roll' effect)
  else: # microsecs==None (flush) or a note change
    add_midi_note_chord(dedup_chord,dedup_microsec)
    dedup_chord,dedup_microsec = noteNos,microsecs

A=440 # you can change this if you want to re-pitch
midi_note_to_freq = []
import math,re
for i in range(128): midi_note_to_freq.append((A/32.0)*math.pow(2,(len(midi_note_to_freq)-9)/12.0))
assert midi_note_to_freq[69] == A # (comment this out if using floating-point tuning because it might fail due to rounding)
def to_freq(n):
  if n==int(n): return midi_note_to_freq[int(n)]
  else: return (A/32.0)*math.pow(2,(n-9)/12.0)

# Begin RISC OS Maestro code

Maestro_header = 'Maestro\x0a\x02'

def BASIC_int(n): return chr(0x40)+chr(n>>24)+chr((n>>16)&0xFF)+chr((n>>8)&0xFF)+chr(n&0xFF)

class MaestroMidiNote:
    def __init__(self,noteNo,startTime):
        self.noteNo,self.startTime = noteNo,startTime
    def end(self,time): self.endTime = time
    def timeLen(self): return self.endTime - self.startTime
    def quantTo(self,resolution):
        self.startTime = int(self.startTime/resolution) * resolution
        self.endTime = int(self.endTime/resolution) * resolution
        if self.endTime == self.startTime: self.endTime += resolution # try to avoid quantising it out completely
    def lenAndDotsList(self,hemiLen,barHemisLeft): # could be several notes tied
        hemisLeft = int(self.timeLen()/hemiLen)
        lTry,lH = 1,64 ; ret = []
        while hemisLeft:
            while hemisLeft >= lH and lH <= barHemisLeft:
                lHT = lH ; dots = 0 ; dotVal = int(lH/2)
                while dotVal and lHT+dotVal <= hemisLeft and dots<3 and lHT+dotVal <= barHemisLeft:
                    dots += 1 ; lHT += dotVal ; dotVal = int(dotVal/2)
                hemisLeft -= lHT ; barHemisLeft -= lHT ; ret.append((lTry,dots))
                if not barHemisLeft:
                    barHemisLeft = 64 # TODO: assumes 4/4
                    lTry,lH =1,64 ; continue
            lTry <<= 1 ; lH >>= 1
            assert not (lH==0 and hemisLeft)
        return ret,barHemisLeft
    def note(self,hemiLen,timeCountFrom,barHemisLeft):
        assert timeCountFrom <= self.startTime
        ret = []
        if timeCountFrom < self.startTime:
            oet,self.endTime,self.startTime = self.endTime,self.startTime,timeCountFrom
            ldl,barHemisLeft = self.lenAndDotsList(hemiLen,barHemisLeft)
            for length,dots in ldl: ret.append(note(None,length,dots))
            self.startTime,self.endTime = self.endTime,oet
        ldl,barHemisLeft = self.lenAndDotsList(hemiLen,barHemisLeft)
        if not ldl: return "".join(ret),barHemisLeft # note must have been completely quantised out
        for length,dots in ldl[:-1]: ret.append(note(self.noteNo,length,dots,tieWithNext=True))
        ret.append(note(self.noteNo,ldl[-1][0],ldl[-1][1]))
        return "".join(ret),barHemisLeft

def note(midiNote,length=4,dots=0,clef="treble",stemDown=None,tieWithNext=False,beamWithNext=False):
    if not midiNote==None: # midiNote=None for a rest
        def f(mn):
            m = mn % 12
            if m >= 5: m += 1
            return int(m/2) + 7*int(mn/12)
        r = f({"treble":71,"bass":50}[clef]) # middle line
        r -= f(midiNote) # -1 = 1 space above the mid-line
        if stemDown==None: stemDown = (r>0)
        r = 16-r
        while r<1: r += 7  # force 8ve ranges
        while r>31: r -= 7 # (assuming we can't change clef)
        sharp = (f(midiNote) == f(midiNote-1))
        r *= 8
        if tieWithNext: r += 4
        if beamWithNext: r += 2
        if stemDown: r += 1
    else: r = sharp = 0
    r2 = 0
    while length:
        length = int(length/2) ; r2 += 1
    assert r2 < 8, "length too short"
    r2 *= 32
    assert 0 <= dots <= 3 ; r2 += dots*8
    if sharp: r2 += 2
    else: r2 += 1 # natural (TODO: figure out if actually needed and omit if not)
    return chr(r) + chr(r2)

def playLen(secondNoterestByte): # for gate-byte sync
    if type(secondNoterestByte)==str:
        secondNoterestByte = ord(secondNoterestByte)
    numDots = (secondNoterestByte >> 3) & 3
    secondNoterestByte = int(secondNoterestByte/32)
    l = 8 # so can *=1.5 3 times and still have an integer
    for i in range(secondNoterestByte,7): l *= 2
    dotVal = int(l/2)
    for i in range(numDots):
      l += dotVal ; dotVal = int(dotVal/2)
    return l

def gatesBytes(notesRestQueues):
    assert len(notesRestQueues) == 8
    lenLeft = [0]*8 ; nrq = notesRestQueues[:] ; r = [] ; barLeft = 64*8
    while any(nrq):
        b = 0 ; toSub = 0
        for i in range(8):
            if nrq[i] and not lenLeft[i]:
                b |= (1 << i)
                lenLeft[i] = playLen(nrq[i][1])
                assert lenLeft[i] > 0, lenLeft[i]
                nrq[i] = nrq[i][2:]
            if lenLeft[i] and (not toSub or lenLeft[i]<toSub): toSub=lenLeft[i]
        if b: r.append(chr(b))
        assert toSub > 0
        for i in range(8):
            if lenLeft[i]: lenLeft[i] -= toSub
        assert 0 in lenLeft
        barLeft -= toSub
        assert barLeft >= 0
        if not barLeft:
            r.append(chr(0)+chr(32)) # barline (needed for reliable playing)
            barLeft = 64*8
    return "".join(r) # (gatesBytes can also include 0 followed by time signature codes etc)

# blocks in any order:

def musicData_block(notesRestQueues): # each queue is a string of 2-byte returns from note() above
    assert len(notesRestQueues) <= 8
    while len(notesRestQueues) < 8: notesRestQueues.append("")
    gb = gatesBytes(notesRestQueues)
    l = [gb]+notesRestQueues
    r = []
    for i in l: r.append(BASIC_int(len(i)))
    return chr(1)+''.join(r)+''.join(l)

def setStaves_block(numStaves=1,numPercStaves=1):
    assert 1 <= numStaves <= 4 and 0 <= numPercStaves <= 1
    return chr(2)+chr(numStaves-1)+chr(numPercStaves-1)

def setInstruments_block(voiceNumberList=[1]*8): # voice 5 is probably the perceptual loudest, might be useful if using unpowered speakers on a RISC OS Raspberry Pi; voice 1 (default) sounds more gentle though (but still better include it or the volume block might not be interpreted)
    assert len(voiceNumberList) == 8
    r = []
    for i in range(8): r.append(chr(i)+chr(voiceNumberList[i]))
    return chr(3)+''.join(r)

def setVolumes_block(volumesList=[7]*8):
    assert len(volumesList)==8
    for x in volumesList: assert 0<=x<=7
    return chr(4)+''.join(map(chr,volumesList))

def setPans_block(stereoPosList):
    assert len(stereoPosList)==8
    for x in stereoPosList: assert -3<=x<=3
    return chr(5)+''.join(map(lambda x:chr(x+3),stereoPosList))

def setBPM_block(bpm): return chr(6)+chr(allowed_BPMs.index(bpm))

# End RISC OS Maestro code

# Some of the code below was taken from an old version of
# Python Midi Package by Max M,
# with much cutting-down and modifying
def toBytes(value):
    return unpack('%sB' % len(value), value)
maxMicrosecs = float(os.environ.get("maxTime",maxTime))*1e6
class MidiToBeep:
    def update_time(self,divisions=0,relative=1):
        oldDivs = self.divisionCount
        if relative: self.divisionCount += divisions
        else: self.divisionCount = divisions
        newMicrosecs = self.microsecs + (self.divisionCount-oldDivs)*self.microsecsPerDivision
        if maxMicrosecs: newMicrosecs = min(newMicrosecs, maxMicrosecs)
        microsecsSeen = newMicrosecs - self.microsecs
        self.microsecs = newMicrosecs
        if microsecsSeen:
            # time was advanced, so output something
            d = {}
            for c,v in self.current_notes_on: d[v+self.semitonesAdd[c]]=1
            if self.need_to_interleave_tracks: self.tracks[-1].append([d.keys(),microsecsSeen])
            else: dedup_midi_note_chord(list(d.keys()),microsecsSeen)
    def reset_time(self):
        self.divisionCount = self.microsecs = 0
    def set_current_track(self, new_track): self._current_track = new_track
    def __init__(self):
        self.divisionCount = self.microsecs = 0
        self._current_track = 0
        self._running_status = None
        self.current_notes_on = []
        self.rpn100 = [0]*16
        self.rpn101 = [0]*16
        self.semitoneRange = [1]*16
        self.semitonesAdd = [0]*16
        self.microsecsPerDivision = 10000
    def note_on(self,channel,note):
        if not channel==9: self.current_notes_on.append((channel,note))
        if mac_voice: dedup_midi_note_chord([],None) # repeated notes must be re-struck on that o/p
    def note_off(self,channel,note):
        try: self.current_notes_on.remove((channel,note))
        except ValueError: pass
    def continuous_controller(self, channel, controller, value):
        # Interpret "pitch bend range":
        if controller==100: self.rpn100[channel] = value
        elif controller==101: self.rpn101[channel] = value
        elif controller==6 and self.rpn100[channel]==self.rpn101[channel]==0:
            self.semitoneRange[channel]=value
    def pitch_bend(self, channel, value):
        # Pitch bend is sometimes used for slurs
        # so we'd better interpret it (only MSB for now; full range is over 8192)
        self.semitonesAdd[channel] = (value-64)*self.semitoneRange[channel]/64.0
    def header(self, format=0, nTracks=1, division=96):
        self.division=division
        self.need_to_interleave_tracks = (format==1)
        self.tracks = [[]][:]
    def eof(self):
        if self.need_to_interleave_tracks:
            while True: # delete empty tracks
                try: self.tracks.remove([])
                except ValueError: break
            while self.tracks:
                minLen = min([t[0][1] for t in self.tracks])
                d = {}
                for t in self.tracks: d.update([(n,1) for n in t[0][0]])
                dedup_midi_note_chord(list(d.keys()),minLen)
                for t in self.tracks:
                    t[0][1] -= minLen
                    if t[0][1]==0: del t[0]
                while True: # delete empty tracks
                    try: self.tracks.remove([])
                    except ValueError: break
    def start_of_track(self, n_track=0):
        self.reset_time()
        self._current_track += 1
        if self.need_to_interleave_tracks: self.tracks.append([])
    def tempo(self, value):
        # TODO if need_to_interleave_tracks, and tempo is not already put in on all tracks, and there's a tempo command that's not at the start and/or not on 1st track, we may need to do something
        self.microsecsPerDivision = value*1.0/self.division

class RawInstreamFile:
    def __init__(self, infile):
        self.data = open(infile, 'rb').read()
        self.cursor = 0
    def getCursor(self):
        return self.cursor
    def moveCursor(self, relative_position=0):
        self.cursor += relative_position
    def nextSlice(self, length, move_cursor=1):
        c = self.cursor
        slc = self.data[c:c+length]
        if move_cursor:
            self.moveCursor(length)
        return slc
    def readBew(self, n_bytes=1, move_cursor=1):
        value = self.nextSlice(n_bytes, move_cursor)
        return unpack('>%s' % {1:'B', 2:'H', 4:'L'}[len(value)], value)[0]
    def readVarLen(self):
        var, value = 0, self.nextSlice(4, 0)
        for byte in unpack('%sB' % len(value), value):
            self.moveCursor(1)
            var = (var << 7) + (byte & 0x7F)
            if not 0x80 & byte: break
        return var
class EventDispatcher:
    def __init__(self, outstream):
        self.outstream = outstream
    def header(self, format, nTracks, division):
        self.outstream.header(format, nTracks, division)
    def start_of_track(self, current_track):
        self.outstream.set_current_track(current_track)
        self.outstream.start_of_track(current_track)
    def eof(self):
        self.outstream.eof()
    def update_time(self, time=0, relative=1):
        self.outstream.update_time(time, relative)
    def reset_time(self):
        self.outstream.reset_time()
    def channel_messages(self, high_nibble, channel, data):
        stream = self.outstream
        data = toBytes(data)
        if high_nibble==0x90: # note on
            note, velocity = data
            if velocity==0: stream.note_off(channel,note)
            else: stream.note_on(channel,note)
        elif high_nibble == 0x80: # note off
            note, velocity = data
            stream.note_off(channel,note)
        elif high_nibble == 0xB0: # continuous controller
            controller, value = data
            stream.continuous_controller(channel, controller, value)
        elif high_nibble == 0xE0: # pitch bend
            stream.pitch_bend(channel, data[1])
    def meta_events(self, meta_type, data):
        stream = self.outstream
        if meta_type == 0x51: # tempo
            b1, b2, b3 = toBytes(data)
            stream.tempo((b1<<16) + (b2<<8) + b3)
class MidiFileParser:
    def __init__(self, raw_in, outstream):
        self.raw_in = raw_in
        self.dispatch = EventDispatcher(outstream)
        self._running_status = None
    def parseMThdChunk(self):
        raw_in = self.raw_in
        header_chunk_type = raw_in.nextSlice(4)
        if type("")==type(u""): header_chunk_type = header_chunk_type.decode('latin1')
        if header_chunk_type != 'MThd': raise TypeError("It is not a valid midi file!")
        header_chunk_zise = raw_in.readBew(4)
        self.format = raw_in.readBew(2)
        self.nTracks = raw_in.readBew(2)
        self.division = raw_in.readBew(2)
        if header_chunk_zise > 6:
            raw_in.moveCursor(header_chunk_zise-6)
        self.dispatch.header(self.format, self.nTracks, self.division)
    def parseMTrkChunk(self):
        self.dispatch.reset_time()
        dispatch = self.dispatch
        raw_in = self.raw_in
        dispatch.start_of_track(self._current_track)
        raw_in.moveCursor(4)
        tracklength = raw_in.readBew(4)
        track_endposition = raw_in.getCursor() + tracklength
        while raw_in.getCursor() < track_endposition:
            time = raw_in.readVarLen()
            dispatch.update_time(time)
            peak_ahead = raw_in.readBew(move_cursor=0)
            if (peak_ahead & 0x80):
                status = self._running_status = raw_in.readBew()
            else:
                status = self._running_status
            high_nibble, low_nibble = status & 0xF0, status & 0x0F
            if status == 0xFF: # meta event
                meta_type = raw_in.readBew()
                meta_length = raw_in.readVarLen()
                meta_data = raw_in.nextSlice(meta_length)
                dispatch.meta_events(meta_type, meta_data)
            elif status == 0xF0: # system exclusive
                raw_in.nextSlice(raw_in.readVarLen()-1)
                if raw_in.readBew(move_cursor=0) == 0xF7:
                    raw_in.readBew()
            elif high_nibble == 0xF0:
                data_size = { 0xF1:1, 0xF2:2, 0xF3:1 }.get(status, 0)
                raw_in.nextSlice(data_size)
            else:
                if high_nibble==0xC0 or high_nibble==0xD0: data_size = 1
                else: data_size = 2
                channel_data = raw_in.nextSlice(data_size)
                event_type, channel = high_nibble, low_nibble
                dispatch.channel_messages(event_type, channel, channel_data)
    def parseMTrkChunks(self):
        for t in range(self.nTracks):
            self._current_track = t
            self.parseMTrkChunk()
        self.dispatch.eof()
class MidiInFile:
    def __init__(self, outStream, infile):
        self.raw_in = RawInstreamFile(infile)
        self.parser = MidiFileParser(self.raw_in, outStream)
    def read(self):
        p = self.parser
        p.parseMThdChunk()
        p.parseMTrkChunks()

try: any
except: # Python 2.3 (e.g. on RISC OS 4)
  def any(x):
    for i in x:
      if i: return True
    return False
  def all(x):
    for i in x:
      if not i: return False
    return True

if delArg('--version'): print(__doc__),sys.exit(0)
helpText = __doc__+"\nSyntax: python midi-beeper.py [options] MIDI-filename ...\nOptions: --bbc | --electron | --bbc-binary | --bbc-ssd | --bbc-sdl | --maestro | --grub | --qbasic | --Organ | --Joelle (--praat --json)\n"
if len(sys.argv)<2: sys.stderr.write(helpText),sys.exit(1)
elif delArg('--help'): print(helpText),sys.exit(0)
if acorn_electron: name = "MIDI to Acorn Electron"
elif (bbc_micro or bbc_micro==[]): name = "MIDI to BBC Micro"
elif riscos_Maestro: name = "MIDI to Maestro"
else: name = "MIDI Beeper"
sys.stderr.write(name+__doc__[__doc__.index(" v"):])
try: xrange
except: xrange = range # Python 3
for midiFile in sys.argv[1:]:
    init() ; dedup_chord,dedup_microsec = [],0
    dedup_microsec_error = 0
    sys.stderr.write("Parsing MIDI file "+midiFile+"\n")
    MidiInFile(MidiToBeep(), midiFile).read()
    dedup_midi_note_chord([],None) # ensure flushed
    if bbc_micro or bbc_micro==[]:
      if bbc_ssd:
        bbcFile = midiFile.replace(os.extsep+"midi","").replace(os.extsep+"mid","")
        if os.sep in bbcFile: bbcFile=bbcFile[bbcFile.rindex(os.sep)+1:]
        if not 0<len(bbcFile)<=7: bbcFile="TUNE%d" % (1+len(bbc_files))
        bbc_files.append((bbcFile,"".join(chr(x) for x in (bbc_micro+[255,0]))))
        # and reset:
        bbc_micro = []
        for i in xrange(len(current_array)): current_array[i]=63
      # else (BBC non-SSD) we'll end below (TODO: per-file?)
    elif riscos_Maestro:
        add_midi_note_chord([],0)
        maestroFile = midiFile.replace(os.extsep+"midi","").replace(os.extsep+"mid","") + ',af1'
        if on_riscos: maestroFile=maestroFile[:-4] # use SetType instead
        assert not maestroFile == midiFile
        sys.stderr.write("Writing Maestro file "+maestroFile+"... ")
        open(maestroFile,'wb').write(maestroData())
        if on_riscos: os.system("SetType "+maestroFile+" af1")
        sys.stderr.write("Finished\n")
    elif qbasic:
        basFile = midiFile.replace(os.extsep+"midi","").replace(os.extsep+"mid","")+os.extsep+"bas"
        open(basFile,'wb').write(b'\n'.join(basData+[b'DATA @,0\n']))
        sys.stderr.write("Wrote "+basFile+"\n")
    elif mac_voice:
        wavFile = midiFile.replace(os.extsep+"midi","").replace(os.extsep+"mid","")+os.extsep+"wav"
        w=os.popen('sox -t raw -r 44100 -c 1 -b 16 -e signed-integer - '+wavFile,'w')
        (w.buffer if hasattr(w,'buffer') else w).write(b''.join(pcmData)) ; w.close() ; sys.stderr.write("Wrote "+wavFile+"\n")
    elif voice_json: print("]}")
    elif not aplay and not grub:
        sys.stderr.write("Playing "+midiFile+"\n")
        runBeep(" ".join(cumulative_params))
if bbc_ssd and bbc_files:
  ssdFile=os.environ.get("DFS_TITLE","tunes")+".ssd"
  sys.stderr.write("Writing output to %s\n" % ssdFile)
  open(ssdFile,"wb").write(make_bbcMicro_DFS_image(bbc_files))
elif bbc_micro:
    if bbc_binary: # need to get it in via indirection
      bbc_micro += [255,0]
# :EQUD&12345678 - 14 keystrokes for 4 bytes
# + 7 for every 60 bytes, total = 14/4+7/60
      if len(bbc_micro) >= 15000: sys.stderr.write("This might exceed BeebEm's 32K keystroke limit. Try pasting 150 lines at a time.\n") # TODO: could check the *exact* limit, but would have to count the code at the start etc
      use_input_loop = ( 8000 < len(bbc_micro) < 15000 ) # saves keystrokes, but might not save actual typing time in a museum etc because EQUD can be copied and the EQUD version is more 'chunked' and easier to track; might be useful to get around max-keystroke limitations on emulators IF we're not exceeding them anyway: typical limit 32k keystrokes which is about 9000 bytes via EQUD method and 16000 via input loop, but allow for program overhead in both cases.  Input loop is slower to paste into an emulator (especially at speed=1) due to the overheads of running a BASIC input/eval loop: if we're way too big then you'll need to chunk it anyway (try 150 lines at a time) so might as well use EQUD in this case. Also, don't use this if data is so big as to leave no room for A$ (although if that's the case then we might have bigger problems re c% + stack); above limits allow for this in default screen modes (6 on Electron and 7 on BBC)
      bbc_micro[0]=bbc_micro[0].replace("NEW","NEW\n0LOMEM=TOP+"+str(len(bbc_micro)-1))
      if use_input_loop: bbc_micro.insert(1,"P%=TOP:LOMEM=P%+"+str(len(bbc_micro)-1)) # need to set now for A$
      else: bbc_micro.insert(1,"P%=TOP")
      bbc_offset = 0 ; i = 2
      if use_input_loop:
        bbc_micro.insert(i,'REP.I.A$:IF LEN(A$):F.A%=1TO193STEP8:!P%=EVAL("&"+MID$(A$,A%,8)):P%=P%+4:N.:U.RIGHT$(A$,1)="*":EL.:U.0') ; i += 1 # horrible mix of if/else and repeat/until on 1 line in immediate mode so it copes with any extra blank lines that buggy emulators might insert
        while i < len(bbc_micro)-100:
          buf = []
          for j in range(i,i+100): buf.append("%02X" % bbc_micro[j])
          for j in range(0,100,4): buf[j],buf[j+1],buf[j+2],buf[j+3] = buf[j+3],buf[j+2],buf[j+1],buf[j] # LSB-MSB
          del bbc_micro[i+1:i+100]
          bbc_micro[i] = "".join(buf) ; i += 1
        bbc_micro[i-1] += '*'
      # Make up the rest (or if not use_input_loop) :
      # TODO: Bas128 gives a "Wrap" error if P% crosses a 16k boundary (even if it's only doing EQUB), so may want a "use plain old indirection" option (low priority because Bas128 has timing issues anyway)
      while i<len(bbc_micro):
       buf = ["[OPT2"]
       while i<len(bbc_micro) and len(buf)<16:
        for fmt,nBytes in [("EQUD&%X",4),("EQUW%d",2),("EQUB%d",1)]:
          if i+nBytes <= len(bbc_micro):
            if nBytes==2 and i+3==len(bbc_micro) and bbc_micro[-1]==0: continue # in this case it might save a couple of keystrokes to end with EQUB *then* EQUW (if bbc_micro[i] is small; worst-case 255,255,0 is the same either way and the BRK optimisation could save 2 keystrokes if doing the EQUB second)
            val = 0
            for j in range(nBytes):
              val += (bbc_micro[i+j]<<(j*8))
            if nBytes==1: buf.append({0:"BRK",10:"ASLA",0x18:"CLC",0x38:"SEC",0x58:"CLI",0x78:"SEI",0xb8:"CLV",0xD8:"CLD",0xF8:"SED",0x4A:"LSRA",0xEA:"NOP",0x40:"RTI",0x60:"RTS"}.get(val,fmt%val)) # occasionally save a couple of keystrokes over the EQUB (usually with a BRK at end)
            else: buf.append(fmt % val)
            del bbc_micro[i:i+nBytes]
            bbc_offset += nBytes
            break
       bbc_micro.insert(i,":".join(buf)+']') ; i += 1
      # TODO: other methods to reduce keystrokes?  (Another thing that could be done is to automatically detect repeats in the MIDI file and get the BBC to do its own repeating instead of writing the data out twice, but this is likely to work only on automatically-generated MIDI files with strict quantised rhythm, otherwise it's likely to be subtly different on the repeat.)
      if not use_input_loop: bbc_micro.append("LOMEM=P%") # because we didn't set it before (and might want to change MODE or something before running; anyway having it here makes it clearer what's going on if you see the screen at the end of the paste)
    elif len(bbc_micro)>1 and len(bbc_micro[-1])<233: bbc_micro[-1] += ",255,0"
    else: bbc_micro.append("D.255,0")
    if not bbc_binary:
      bbc_micro = "\n".join(bbc_micro).split("\n")
      if bbc_sdl:
        # bbc_sdl doesn't recognise keyword abbreviations, so use longhand:
        bbc_micro = "\n".join(bbc_micro).replace("D.","DATA").replace("N.","NEXT").replace("U.","UNTIL").replace("SO.","SOUND").replace("REP.","REPEAT").replace("ENV.","ENVELOPE")
        # Work around bbc_sdl bug #3 (on 1.12 and below) in the case of 2 notes per channel, by using a 0-length 3rd step that negates the 2nd step's change, which should clear up any piece with 6 notes or fewer per chord:
        bbc_micro = bbc_micro.replace("V%=1","V%=1:Q%=0:R%=0")
        if acorn_electron: bbc_micro=bbc_micro.replace("Q%=c%(1)-P%","Q%=c%(1)-P%:R%=-Q%")
        else: bbc_micro=bbc_micro.replace("V%=2","V%=2:R%=-Q%")
        # Add 1 octave if BBC BASIC for SDL (or BBC BASIC for Windows) is detected, because it's pitched an octave lower than the real BBC (well, we could use *VOICE c,5 to emphasize the first harmonic, but we'd have to check which versions support it and it's not quite the same) :
        bbc_micro=bbc_micro.replace("N%=0","A%=-48*((INKEY(-256)AND219)=83):N%=0")
        if acorn_electron: bbc_micro=bbc_micro.replace("P%,","P%+A%,")
        else: bbc_micro=bbc_micro.replace("c%(I%),","c%(I%)+A%,")
        # add line numbers, in case we're on a real BBC (as we can't use AUTO, which cannot be conditioned on INKEY(-256)); already added line numbers to DATA lines (so we know max length on real BBC) but others need adding:
        bbc_micro = bbc_micro.split("\n")
        for i in xrange(len(bbc_micro)):
          bbc_micro[i]=str(i+1)+bbc_micro[i]
      # If not bbc_sdl (and not bbc_binary), use AUTO.
      # AUTO automatically stops once the line number would be >= 32768.  We can use this to avoid having to put an Escape into the keyboard buffer.
      # TODO: If user is pasting this in multiple chunks, and emulator adds a spurious newline at the beginning of each chunk (e.g. BeebEm 3 on Mac), AUTO start number needs decreasing (unless user makes sure not to include the newline at the end of each chunk if the emulator will add its own at the start of the next)
      elif len(bbc_micro) > 3277: bbc_micro.insert(0,"AU."+str(32768-len(bbc_micro))+",1") # (although if this is the case, program is extremely likely to exhaust the memory even in Bas128)
      else: bbc_micro.insert(0,"AU."+str(32770-10*len(bbc_micro)))
    print ("\n".join(bbc_micro))
