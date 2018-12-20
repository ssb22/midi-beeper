#!/usr/bin/env python2

# MIDI beeper (plays MIDI without sound hardware)
# Version 1.65, (c) 2007-2010,2015-2018 Silas S. Brown.  License: GPL

# MIDI beeper is a Python program to play MIDI by beeping
# through the computer's beeper instead of using proper
# sound circuits.  It emulates chords/polyphony.
# It sounds awful, but it might be useful when no sound device
# is attached.  It should work on any machine that has the
# "beep" Linux package, including NSLU2 network storage devices.
# (On NSLU2 do 'sudo modprobe isp4xx_beeper' before running)

# Can also play MIDI files using square-wave synthesis with aplay
# (e.g. on Raspberry Pi) - set aplay below if you want this instead.
# Set it to a volume level, e.g. aplay = 100
aplay = 0

# Can also convert MIDI files to RISC OS Maestro music files
# for playing (but not typesetting well) on 'vanilla' RISC OS.
# Set riscos_Maestro = 1 below if you want this.
riscos_Maestro = 0
# If running this *on* RISC OS (Python 2.3) you might find it useful to set:
# import sys ; sys.argv.append("$.!Boot.Loader.test/mid") # (or whatever)

# Can also convert MIDI files to BBC Micro programs
# (printed to standard output).  Set bbc_micro below:
bbc_micro = 0 # or run with --bbc
acorn_electron = 0 # or run with --electron: Acorn Electron version (more limited)
bbc_binary = 0 # or run with --bbc-binary: make the above use direct memory access instead of DATA (packs more in but harder to save/edit)
bbc_ssd = 0 # or run with --bbc-ssd: writes an SSD image (for an emulator) instead of printing keystrokes to standard output (set environment DFS_TITLE to title the disk; disk will contain one BBC program for each MIDI file on the command line + bootloader)

# HiBasic (Tube) support (~30k for programs) fully works
# Bas128 support (64k for programs) works but (a) bank-switching delays impact the timing of shorter notes and (b) bbc_binary option can cause "Wrap" errors during input.  However bbc_binary and bbc_ssd options should pack data into a smaller space so normal BASIC can be used.

force_monophonic = 0  # set this to 1 to have only the top line (not normally necessary)

# ----------------------------------------------------

import os,sys
def delArg(a):
  found = a in sys.argv
  if found: sys.argv.remove(a)
  return found
if delArg('--bbc'): bbc_micro = 1
if delArg('--electron'): acorn_electron = 1
if delArg('--bbc-binary'): bbc_binary=bbc_micro=1
if delArg('--bbc-ssd'): bbc_ssd=bbc_micro=1

if aplay:
  rate = 8000 # can just about manage 3 or 4 channels on a Raspberry Pi if it isn't doing anything else
  o = os.popen("aplay -q -t raw -c 1 -f U8 -r %d" % rate,"w")
  def init(): pass
  def chord(freqs,millisecs):
    samples = millisecs * rate / 1000 ; halfPeriods = []
    for f in freqs: halfPeriods.append(rate/2.0/f)
    assert not 0 in halfPeriods
    nextFlips = map(int,halfPeriods) ; counts = [1]*len(halfPeriods)
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
        o.write(chr(val)) ; t += 1
  def add_midi_note_chord(noteNos,microsecs):
    chord(map(to_freq,noteNos),microsecs / 1000)
elif bbc_micro or acorn_electron:
  # This is a compact BBC Micro program to multiplex up to
  # 9 channels of sound onto the BBC Micro's 3 channels.
  # Basically uses ENVELOPEs to do the pitch multiplexing.
  # BBC Micro's BASIC encouraged the use of @% through Z% by reserving memory for them (heap is typically small), so code can be quite obscure.
  # N% = next available envelope number (1-16 if not using BPUT#, otherwise 1-4 but we don't want to redefine envelopes that are already associated with notes in the buffer).
  # BBC Micro quirk: contrary to what the manual says (in at least some printings), the number of notes in each channel's "to be played" buffer before the program waits can be 5 not 4 (on at least some versions of the BBC).  This, together with the current note, means we might need a total of 6*3=18 envelopes, and we have only 16 slots.  Hence the ADVAL loop to avoid filling the buffer completely.  (Also making sure to special-case volume 0 so it doesn't use an envelope seems to make things a little more robust.  This is needed anyway in the Electron version below: the Electron uses a ULA with only 1 channel and 1 volume; last 6 envelope parameters are ignored and setting them to 0 does NOT switch off the sound like it does on the BBC)
  # c% is the current value of each 'channel' (252 i.e. 4*63 is used for silence); data read tells the program what changes to make to this array for the next chord & how long to sound it for (see add_midi_note_chord below).
  # Lines 4 through 12 of this can be abbreviated thus: REP.:C%=0:REP.:READD%:c%(C%)=(D%A.63)*4:I%=(D%DIV64)+1:C%=C%+I%:U.I%=4:READD%:REP.:U.AD.-6>3:F.I%=0TO6S.3:S%=0:T%=0:IFc%(I%)=252:V%=0:EL.IFc%(I%+1)=252:V%=1:EL.S%=1:Q%=c%(I%+1)-c%(I%):IFc%(I%+2)=252:V%=2:EL.R%=c%(I%+2)-c%(I%+1):T%=1:V%=3
  # but Bas128 is still too slow (I'm not convinced it copies whole lines into low memory or anything like that)
  bbc_micro = ["""FOR C%=16 TO 19:SO.C%,0,0,0:N.
N%=0:DIM c%(8)
FOR D%=0 TO 8:c%(D%)=252:N.
REP.:C%=0
REP.:READ D%
c%(C%)=(D% AND 63)*4
I%=(D% DIV 64)+1:C%=C%+I%:U.I%=4
READ D%
REP.:U.ADVAL(-6)>3
FOR I%=0 TO 6 STEP 3
S%=0:T%=0
IF c%(I%)=252:V%=0:ELSE IF c%(I%+1)=252:V%=1:ELSE S%=1:Q%=c%(I%+1)-c%(I%):IF c%(I%+2)=252:V%=2:ELSE R%=c%(I%+2)-c%(I%+1):T%=1:V%=3
IF V%:V%=V%*24+55:N%=N%+1:IF N%=17:N%=1
IF V%:ENV.N%,3,0,Q%,R%,1,S%,T%,V%,0,0,-V%,V%,V%:V%=N%
SO.513+(I%DIV3),V%,c%(I%),D%
N.:U.D%=0:END"""]
  if acorn_electron:
    # Cut-down version of the above code for the Electron:
    bbc_micro=["""SO.1,0,0,0
N%=0:DIM c%(2)
FOR D%=0 TO 2:c%(D%)=252:N.
REP.:C%=0
REP.:READ D%
c%(C%)=(D% AND 63)*4
I%=(D% DIV 64)+1:C%=C%+I%:U.I%=4
READ D%
REP.:U.ADVAL(-6)>3
S%=0:T%=0:P%=c%(0)
IF P%=252:V%=0:ELSE V%=1:IF c%(1)<>252:S%=1:Q%=c%(1)-P%:IF c%(2)<>252:R%=c%(2)-c%(1):T%=1
IF V%:N%=N%+1:IF N%=17:N%=1
IF V%:ENV.N%,3,0,Q%,R%,1,S%,T%,126,0,0,-126,126,126:V%=N%
SO.1,V%,P%,D%
U.D%=0:END"""] # the 126,etc is there so that if this program is accidentally run on the BBC Micro instead of the Electron it'll at least sound something
    current_array = [63]*3
  else: current_array = [63]*9
  if bbc_ssd:
    bbc_micro = [] # we'll put tokenised program in later
    bbc_binary = 1
    bbc_files = []
  elif bbc_binary: # don't use AUTO; change to read RAM
    lines = ("E%=TOP:" + bbc_micro[0]).split("\n") ; bbc_micro = []
    for i in range(len(lines)):
      bbc_micro.append("%d%s" % (i+1,lines[i]))
    bbc_micro=[
      "IF(PA. A.&FF00)>&E00:PA.=&E00:*ROM" # reclaim space from Model B DFS if applicable (may or may not be needed depending on which DFS is in use and how much space it takes, which we won't know at code-generation time)
      "NEW"]+bbc_micro
    # Could see the Mode 0 memory map with: MO.0:V.23;12;0;0;0;0;28,0,12,63,0
    # For larger MIDIs, can see sound queues etc (but not BASIC stack) via: MO.6:V.23;12;0;0;0;0;23;0;0;0;0;0:RUN
    # (can also try MO.4)
    bbc_micro = ["\n".join(bbc_micro).replace("READ D%","D%=?E%:E%=E%+1")]
  def add_midi_note_chord(noteNos,microsecs):
    duration = int((microsecs*20+500000)/1000000)
    while duration > 254: # unlikely but we should cover this
      add_midi_note_chord(noteNos,254*1000000/20)
      duration -= 254
    if not duration: return
    def f(n): # convert to SOUND/4 and bound the octaves
      n -= 47 # MIDI note 69 is pitch 88 i.e. 4*22
      while n<0: n+=12
      while n>=63: n-=12 # we're using 63 for rest
      return n
    if acorn_electron: noteNos = noteNos[-3:]
    noteNos = map(f,noteNos[-9:])
    while len(noteNos)<3: noteNos.append(63)
    if not acorn_electron: # divide evenly among BBC channels
      # (and if need arpeggiation, prefer it in the bass)
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
    else: # self-contained typeable BBC BASIC
      o = ",".join(map(lambda x:("%d"%x), o))
      if len(bbc_micro)>1 and len(bbc_micro[-1])+len(o)+1 <= 238: bbc_micro[-1] += ','+o
      else: bbc_micro.append("D."+o)
  def init():
    global dedup_microsec_quantise
    dedup_microsec_quantise = 50000 # 1000000/20
elif riscos_Maestro:
  allowed_BPMs = [40, 50, 60, 65, 70, 80, 90, 100, 115, 130, 145, 160, 175, 190, 210]
  default_bpm = max(allowed_BPMs) # theoretically gives the most accuracy
  hemi_microsecs = 3750000/default_bpm # for now (ms/hemi = beat/hemi / (b/min * min/microsec) = 1/16 / (bpm / 60000000) = 60000000/16/bpm)
  def add_midi_note_chord(noteNos,microsecs):
    noteNos.reverse()
    global current_time
    for n in current_chord[:]:
      if n.noteNo in noteNos: noteNos.remove(n.noteNo) # just extend the currently-playing note
      else: # stop that note:
        assert n.noteNo not in noteNos # shouldn't have any duplicates in that list
        n.end(current_time)
        n.quantiseTo(hemi_microsecs)
        foundC = False
        for i in [0,4,6,2,1,3,5,7]: # allocate channels in that order so 2-stave (0-3,4-6/7), 3-stave (0,1-4,5-6/7) and 4-stave (0-1,2-3,4-5,6/7) views work vaguely sensibly
            c = riscos_channels[i]
            if not c or c[-1].endTime <= n.startTime:
                c.append(n) ; foundC = True ; break
        if not foundC: sys.stderr.write("Insufficient RISC OS channels: dropping note %d\n" % n.noteNo)
        current_chord.remove(n)
    for noteNo in noteNos: current_chord.append(MidiNote(noteNo,current_time)) # newly-started notes
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
  def init():
    global current_chord,current_time,riscos_channels
    current_chord = [] ; current_time = 0 ; riscos_channels = [[],[],[],[],[],[],[],[]]
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
    if not freqList: return " -D %d" % (millisecs,) # rest
    elif len(freqList)==1: return " -n -f %d -l %d" % (freqList[0],millisecs) # one note
    else:
        pulseLength = max(min(millisecs/len(freqList)/repetitions_to_aim_for,max_pulseLength),min_pulseLength)
        return (" -D 0".join([chord([f],pulseLength) for f in freqList]))*max(1,millisecs/pulseLength/len(freqList)) # (max with 1 means at least 1 repetition - prefer a slight slow-down to missing a chord out)
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
    cumulative_params.append(chord(map(to_freq,noteNos),millisecs))

def make_bbcMicro_DFS_image(datFiles):
  opt4 = 3 # exec !BOOT
  disk_title = os.environ.get("DFS_TITLE","")
  disk_title += "\0"*max(0,12-len(disk_title))
  # catalogue is 31 items but we'll do !BOOT separately
  catNames,catInfo,catNo = ["\0"*8]*31,["\0"*8]*31,0
  data = "*BASIC\r"
  assert all(len(f)<=7 and re.match('^[A-Za-z0-9]*$',f) for f,_ in datFiles), "please keep DFS filenames to 7-char alphanumeric "+repr([f for f,_ in datFiles])
  if "BOOT_COPYRIGHT" in os.environ: data += "\rREM "+os.environ["BOOT_COPYRIGHT"]+"\r\r" # TODO: document this?
  if len(datFiles)==1: data += ('*LOAD "%s"\rLIST\rRUN\r' % datFiles[0][0])
  else: data += "*CAT\r"+"REP.:U.AD.-6=15:".join(('CH."%s"\r' % f) for f,_ in datFiles)
  nextSector = 2+int((len(data)+255)/256)
  catNames[0]="!BOOT  $"
  catInfo[0]="".join([
    "\0"*4, # !BOOT lsb-msb Load, lsb-msb Exec
    chr(len(data)&0xFF)+chr(len(data)>>8),
    "\0", # no >64k options or high start-sector bits
    "\2", # starts on sector 2
    ])
  data += "\0"*((256-(len(data)%256))&0xFF) # pad
  for fname,datBytes in datFiles:
    catNo += 1; assert catNo<31
    lomem_set = "\xd2=\xb8P+"+str(len(datBytes)-1)
    assert not acorn_electron, "make_bbcMicro_DFS_image is hard-coded to use the BBC Micro reader, not Electron"
    datBytes="\r\x00\x00"+chr(len(lomem_set)+4)+lomem_set+"\r\x00\n@E%=\xb8P:\xe3C%=16\xb819:\xd4C%,0,0,0:\xed:N%=0:\xdec%(8):\xe3D%=0\xb88:c%(D%)=252:\xed\r\x00\x14\xe5\xf5:C%=0:\xf5:D%=?E%:E%=E%+1:c%(C%)=(D%\x8063)*4:I%=(D%\x8164)+1:C%=C%+I%:\xfdI%=4:D%=?E%:E%=E%+1:\xf5:\xfd\x96-6>3:\xe3I%=0\xb86\x883:S%=0:T%=0:\xe7c%(I%)=252:V%=0:\x8b\xe7c%(I%+1)=252:V%=1:\x8bS%=1:Q%=c%(I%+1)-c%(I%):\xe7c%(I%+2)=252:V%=2:\x8bR%=c%(I%+2)-c%(I%+1):T%=1:V%=3\r\x00\x1e'\xe7V%:V%=V%*24+55:N%=N%+1:\xe7N%=17:N%=1\r\x00(4\xe7V%:\xe2N%,3,0,Q%,R%,1,S%,T%,V%,0,0,-V%,V%,V%:V%=N%\r\x002$\xd4513+(I%\x813),V%,c%(I%),D%:\xed:\xfdD%=0\r\xff"+datBytes
    catNames[catNo]=fname+' '*(7-len(fname))+'$'
    catInfo[catNo] = "".join([
      "\0"*4, # lsb-msb Load, lsb-msb Exec (TODO: should these be &1900 for BASIC programs?)
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
  while data[-1]=="\0": data=data[:-1] # TODO: inefficient
  return "".join([
    disk_title[:8],
    "".join(catNames),
    disk_title[8:12],
    "\1", # disk cycle (BCD, incremented each time catalogue is written)
    chr((1+catNo)*8),
    chr((sectors>>8)+16*opt4),
    chr(sectors&0xFF),
    "".join(catInfo),
    data])

dedup_microsec_quantise = 0 # for handling 'rolls' etc (currently used by bbc_micro; TODO: default 'beep' cmd also?)
def dedup_midi_note_chord(noteNos,microsecs):
  if force_monophonic and noteNos: noteNos=[max(noteNos)]
  else: noteNos.sort()
  global dedup_chord,dedup_microsec
  if dedup_microsec_quantise and not microsecs==None:
    global dedup_microsec_error
    microsecs += dedup_microsec_error ; oldM = microsecs
    microsecs = int((microsecs+dedup_microsec_quantise/2)/dedup_microsec_quantise) * dedup_microsec_quantise
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

class MidiNote:
    def __init__(self,noteNo,startTime):
        self.noteNo,self.startTime = noteNo,startTime
    def end(self,time): self.endTime = time
    def timeLen(self): return self.endTime - self.startTime
    def quantiseTo(self,resolution):
        origLen = self.endTime - self.startTime
        self.startTime = int(self.startTime/resolution) * resolution
        self.endTime = int(self.endTime/resolution) * resolution
        if self.endTime == self.startTime: self.endTime += resolution # try to avoid quantising it out completely
    def lenAndDotsList(self,hemiLen,barHemisLeft): # could be several notes tied
        hemisLeft = int(self.timeLen()/hemiLen)
        lTry,lH = 1,64 ; ret = []
        while hemisLeft:
            while hemisLeft >= lH and lH <= barHemisLeft:
                lHT = lH ; dots = 0 ; dotVal = lH/2
                while dotVal and lHT+dotVal <= hemisLeft and dots<3 and lHT+dotVal <= barHemisLeft:
                    dots += 1 ; lHT += dotVal ; dotVal /=2
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
    dotVal = l*0.5
    for i in range(numDots):
      l += dotVal ; dotVal /= 2
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

# Some of the code below is taken from Python Midi Package by Max M,
# http://www.mxm.dk/products/public/pythonmidi
# with much cutting-down and modifying
from types import StringType
from cStringIO import StringIO
from struct import pack, unpack
def getNibbles(byte): return (byte >> 4 & 0xF, byte & 0xF)
def setNibbles(hiNibble, loNibble):
    return (hiNibble << 4) + loNibble
def readBew(value):
    return unpack('>%s' % {1:'B', 2:'H', 4:'L'}[len(value)], value)[0]
def readVar(value):
    sum = 0
    for byte in unpack('%sB' % len(value), value):
        sum = (sum << 7) + (byte & 0x7F)
        if not 0x80 & byte: break
    return sum
def varLen(value):
    if value <= 127:
        return 1
    elif value <= 16383:
        return 2
    elif value <= 2097151:
        return 3
    else:
        return 4
def to_n_bits(value, length=1, nbits=7):
    bytes = [(value >> (i*nbits)) & 0x7F for i in range(length)]
    bytes.reverse()
    return bytes
def toBytes(value):
    return unpack('%sB' % len(value), value)
def fromBytes(value):
    if not value:
        return ''
    return pack('%sB' % len(value), *value)
NOTE_OFF = 0x80
NOTE_ON = 0x90
AFTERTOUCH = 0xA0
CONTINUOUS_CONTROLLER = 0xB0
PATCH_CHANGE = 0xC0
CHANNEL_PRESSURE = 0xD0
PITCH_BEND = 0xE0
BANK_SELECT = 0x00
MODULATION_WHEEL = 0x01
BREATH_CONTROLLER = 0x02
FOOT_CONTROLLER = 0x04
PORTAMENTO_TIME = 0x05
DATA_ENTRY = 0x06
CHANNEL_VOLUME = 0x07
BALANCE = 0x08
PAN = 0x0A
EXPRESSION_CONTROLLER = 0x0B
EFFECT_CONTROL_1 = 0x0C
EFFECT_CONTROL_2 = 0x0D
GEN_PURPOSE_CONTROLLER_1 = 0x10
GEN_PURPOSE_CONTROLLER_2 = 0x11
GEN_PURPOSE_CONTROLLER_3 = 0x12
GEN_PURPOSE_CONTROLLER_4 = 0x13
BANK_SELECT = 0x20
MODULATION_WHEEL = 0x21
BREATH_CONTROLLER = 0x22
FOOT_CONTROLLER = 0x24
PORTAMENTO_TIME = 0x25
DATA_ENTRY = 0x26
CHANNEL_VOLUME = 0x27
BALANCE = 0x28
PAN = 0x2A
EXPRESSION_CONTROLLER = 0x2B
EFFECT_CONTROL_1 = 0x2C
EFFECT_CONTROL_2 = 0x2D
GENERAL_PURPOSE_CONTROLLER_1 = 0x30
GENERAL_PURPOSE_CONTROLLER_2 = 0x31
GENERAL_PURPOSE_CONTROLLER_3 = 0x32
GENERAL_PURPOSE_CONTROLLER_4 = 0x33
SUSTAIN_ONOFF = 0x40
PORTAMENTO_ONOFF = 0x41
SOSTENUTO_ONOFF = 0x42
SOFT_PEDAL_ONOFF = 0x43
LEGATO_ONOFF = 0x44
HOLD_2_ONOFF = 0x45
SOUND_CONTROLLER_1 = 0x46
SOUND_CONTROLLER_2 = 0x47
SOUND_CONTROLLER_3 = 0x48
SOUND_CONTROLLER_4 = 0x49
SOUND_CONTROLLER_5 = 0x4A
SOUND_CONTROLLER_7 = 0x4C
SOUND_CONTROLLER_8 = 0x4D
SOUND_CONTROLLER_9 = 0x4E
SOUND_CONTROLLER_10 = 0x4F
GENERAL_PURPOSE_CONTROLLER_5 = 0x50
GENERAL_PURPOSE_CONTROLLER_6 = 0x51
GENERAL_PURPOSE_CONTROLLER_7 = 0x52
GENERAL_PURPOSE_CONTROLLER_8 = 0x53
PORTAMENTO_CONTROL = 0x54
EFFECTS_1 = 0x5B
EFFECTS_2 = 0x5C
EFFECTS_3 = 0x5D
EFFECTS_4 = 0x5E
EFFECTS_5 = 0x5F
DATA_INCREMENT = 0x60
DATA_DECREMENT = 0x61
NON_REGISTERED_PARAMETER_NUMBER = 0x62
NON_REGISTERED_PARAMETER_NUMBER = 0x63
REGISTERED_PARAMETER_NUMBER = 0x64
REGISTERED_PARAMETER_NUMBER = 0x65
ALL_SOUND_OFF = 0x78
RESET_ALL_CONTROLLERS = 0x79
LOCAL_CONTROL_ONOFF = 0x7A
ALL_NOTES_OFF = 0x7B
OMNI_MODE_OFF = 0x7C
OMNI_MODE_ON = 0x7D
MONO_MODE_ON = 0x7E
POLY_MODE_ON = 0x7F
SYSTEM_EXCLUSIVE = 0xF0
MTC = 0xF1
SONG_POSITION_POINTER = 0xF2
SONG_SELECT = 0xF3
TUNING_REQUEST = 0xF6
END_OFF_EXCLUSIVE = 0xF7
SEQUENCE_NUMBER = 0x00
TEXT            = 0x01
COPYRIGHT       = 0x02
SEQUENCE_NAME   = 0x03
INSTRUMENT_NAME = 0x04
LYRIC           = 0x05
MARKER          = 0x06
CUEPOINT        = 0x07
PROGRAM_NAME    = 0x08
DEVICE_NAME     = 0x09
MIDI_CH_PREFIX  = 0x20
MIDI_PORT       = 0x21
END_OF_TRACK    = 0x2F
TEMPO           = 0x51
SMTP_OFFSET     = 0x54
TIME_SIGNATURE  = 0x58
KEY_SIGNATURE   = 0x59
SPECIFIC        = 0x7F
FILE_HEADER     = 'MThd'
TRACK_HEADER    = 'MTrk'
TIMING_CLOCK   = 0xF8
SONG_START     = 0xFA
SONG_CONTINUE  = 0xFB
SONG_STOP      = 0xFC
ACTIVE_SENSING = 0xFE
SYSTEM_RESET   = 0xFF
META_EVENT     = 0xFF
def is_status(byte):
    return (byte & 0x80) == 0x80
class MidiToBeep:
    def update_time(self, new_time=0, relative=1):
        if relative:
            self._relative_time = new_time
            self._absolute_time += new_time
        else:
            self._relative_time = new_time - self._absolute_time
            self._absolute_time = new_time
        if self._relative_time:
            # time was advanced, so output something
            d = {}
            for c,v in self.current_notes_on: d[v+self.semitonesAdd[c]]=1
            if self.need_to_interleave_tracks: self.tracks[-1].append([d.keys(),self._relative_time*self.microsecsPerDivision])
            else: dedup_midi_note_chord(d.keys(),self._relative_time*self.microsecsPerDivision)
    def reset_time(self):
        self._relative_time = 0
        self._absolute_time = 0
    def rel_time(self): return self._relative_time
    def abs_time(self): return self._absolute_time
    def reset_run_stat(self): self._running_status = None
    def set_run_stat(self, new_status): self._running_status = new_status
    def get_run_stat(self): return self._running_status
    def set_current_track(self, new_track): self._current_track = new_track
    def get_current_track(self): return self._current_track
    def __init__(self):
        self._absolute_time = 0
        self._relative_time = 0
        self._current_track = 0
        self._running_status = None
        self.current_notes_on = []
        self.rpnLsb = [0]*16
        self.rpnMsb = [0]*16
        self.semitoneRange = [1]*16
        self.semitonesAdd = [0]*16
        self.microsecsPerDivision = 10000
    def note_on(self, channel=0, note=0x40, velocity=0x40):
        if velocity and not channel==9: self.current_notes_on.append((channel,note))
    def note_off(self, channel=0, note=0x40, velocity=0x40):
        try: self.current_notes_on.remove((channel,note))
        except ValueError: pass
    def aftertouch(self, channel=0, note=0x40, velocity=0x40): pass
    def continuous_controller(self, channel, controller, value):
        # Interpret "pitch bend range":
        if controller==64: self.rpnLsb[channel] = value
        elif controller==65: self.rpnMsb[channel] = value
        elif controller==6 and self.rpnLsb[channel]==self.rpnMsb[channel]==0:
            self.semitoneRange[channel]=value
    def patch_change(self, channel, patch): pass
    def channel_pressure(self, channel, pressure): pass
    def pitch_bend(self, channel, value):
        # Pitch bend is sometimes used for slurs
        # so we'd better interpret it (only MSB for now; full range is over 8192)
        self.semitonesAdd[channel] = (value-64)*self.semitoneRange[channel]/64.0
    def sysex_event(self, data): pass
    def midi_time_code(self, msg_type, values): pass
    def song_position_pointer(self, value): pass
    def song_select(self, songNumber): pass
    def tuning_request(self): pass
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
                dedup_midi_note_chord(d.keys(),minLen)
                for t in self.tracks:
                    t[0][1] -= minLen
                    if t[0][1]==0: del t[0]
                while True: # delete empty tracks
                    try: self.tracks.remove([])
                    except ValueError: break
    def meta_event(self, meta_type, data): pass
    def start_of_track(self, n_track=0):
        self.reset_time()
        self._current_track += 1
        if self.need_to_interleave_tracks: self.tracks.append([])
    def end_of_track(self): pass
    def sequence_number(self, value): pass
    def text(self, text): pass
    def copyright(self, text): pass
    def sequence_name(self, text): pass
    def instrument_name(self, text): pass
    def lyric(self, text): pass
    def marker(self, text): pass
    def cuepoint(self, text): pass
    def program_name(self,progname): pass
    def device_name(self,devicename): pass
    def midi_ch_prefix(self, channel): pass
    def midi_port(self, value): pass
    def tempo(self, value):
        # TODO if need_to_interleave_tracks, and tempo is not already put in on all tracks, and there's a tempo command that's not at the start and/or not on 1st track, we may need to do something
        self.microsecsPerDivision = value/self.division
    def smtp_offset(self, hour, minute, second, frame, framePart): pass
    def time_signature(self, nn, dd, cc, bb): pass
    def key_signature(self, sf, mi): pass
    def sequencer_specific(self, data): pass

class RawInstreamFile:
    def __init__(self, infile=''):
        if infile:
            if isinstance(infile, StringType):
                infile = open(infile, 'rb')
                self.data = infile.read()
                infile.close()
            else:
                self.data = infile.read()
        else:
            self.data = ''
        self.cursor = 0
    def setData(self, data=''):
        self.data = data
    def setCursor(self, position=0):
        self.cursor = position
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
        return readBew(self.nextSlice(n_bytes, move_cursor))
    def readVarLen(self):
        MAX_VARLEN = 4
        var = readVar(self.nextSlice(MAX_VARLEN, 0))
        self.moveCursor(varLen(var))
        return var
class EventDispatcher:
    def __init__(self, outstream):
        self.outstream = outstream
        self.convert_zero_velocity = 1
        self.dispatch_continuos_controllers = 1
        self.dispatch_meta_events = 1
    def header(self, format, nTracks, division):
        self.outstream.header(format, nTracks, division)
    def start_of_track(self, current_track):
        self.outstream.set_current_track(current_track)
        self.outstream.start_of_track(current_track)
    def sysex_event(self, data):
        self.outstream.sysex_event(data)
    def eof(self):
        self.outstream.eof()
    def update_time(self, new_time=0, relative=1):
        self.outstream.update_time(new_time, relative)
    def reset_time(self):
        self.outstream.reset_time()
    def channel_messages(self, hi_nible, channel, data):
        stream = self.outstream
        data = toBytes(data)
        if (NOTE_ON & 0xF0) == hi_nible:
            note, velocity = data
            if velocity==0 and self.convert_zero_velocity:
                stream.note_off(channel, note, 0x40)
            else:
                stream.note_on(channel, note, velocity)
        elif (NOTE_OFF & 0xF0) == hi_nible:
            note, velocity = data
            stream.note_off(channel, note, velocity)
        elif (AFTERTOUCH & 0xF0) == hi_nible:
            note, velocity = data
            stream.aftertouch(channel, note, velocity)
        elif (CONTINUOUS_CONTROLLER & 0xF0) == hi_nible:
            controller, value = data
            if self.dispatch_continuos_controllers:
                self.continuous_controllers(channel, controller, value)
            else:
                stream.continuous_controller(channel, controller, value)
        elif (PATCH_CHANGE & 0xF0) == hi_nible:
            program = data[0]
            stream.patch_change(channel, program)
        elif (CHANNEL_PRESSURE & 0xF0) == hi_nible:
            pressure = data[0]
            stream.channel_pressure(channel, pressure)
        elif (PITCH_BEND & 0xF0) == hi_nible:
            hibyte, lobyte = data
            value = (hibyte<<7) + lobyte
            stream.pitch_bend(channel, value)
        else:
            raise ValueError, 'Illegal channel message!'
    def continuous_controllers(self, channel, controller, value):
        stream = self.outstream
        stream.continuous_controller(channel, controller, value)
    def system_commons(self, common_type, common_data):
        stream = self.outstream
        if common_type == MTC:
            data = readBew(common_data)
            msg_type = (data & 0x07) >> 4
            values = (data & 0x0F)
            stream.midi_time_code(msg_type, values)
        elif common_type == SONG_POSITION_POINTER:
            hibyte, lobyte = toBytes(common_data)
            value = (hibyte<<7) + lobyte
            stream.song_position_pointer(value)
        elif common_type == SONG_SELECT:
            data = readBew(common_data)
            stream.song_select(data)
        elif common_type == TUNING_REQUEST:
            stream.tuning_request(time=None)
    def meta_events(self, meta_type, data):
        stream = self.outstream
        if meta_type == SEQUENCE_NUMBER:
            number = readBew(data)
            stream.sequence_number(number)
        elif meta_type == TEXT:
            stream.text(data)
        elif meta_type == COPYRIGHT:
            stream.copyright(data)
        elif meta_type == SEQUENCE_NAME:
            stream.sequence_name(data)
        elif meta_type == INSTRUMENT_NAME:
            stream.instrument_name(data)
        elif meta_type == LYRIC:
            stream.lyric(data)
        elif meta_type == MARKER:
            stream.marker(data)
        elif meta_type == CUEPOINT:
            stream.cuepoint(data)
        elif meta_type == PROGRAM_NAME:
            stream.program_name(data)
        elif meta_type == DEVICE_NAME:
            stream.device_name(data)
        elif meta_type == MIDI_CH_PREFIX:
            channel = readBew(data)
            stream.midi_ch_prefix(channel)
        elif meta_type == MIDI_PORT:
            port = readBew(data)
            stream.midi_port(port)
        elif meta_type == END_OF_TRACK:
            stream.end_of_track()
        elif meta_type == TEMPO:
            b1, b2, b3 = toBytes(data)
            stream.tempo((b1<<16) + (b2<<8) + b3)
        elif meta_type == SMTP_OFFSET:
            hour, minute, second, frame, framePart = toBytes(data)
            stream.smtp_offset(
                    hour, minute, second, frame, framePart)
        elif meta_type == TIME_SIGNATURE:
            nn, dd, cc, bb = toBytes(data)
            stream.time_signature(nn, dd, cc, bb)
        elif meta_type == KEY_SIGNATURE:
            sf, mi = toBytes(data)
            stream.key_signature(sf, mi)
        elif meta_type == SPECIFIC:
            meta_data = toBytes(data)
            stream.sequencer_specific(meta_data)
        else:
            meta_data = toBytes(data)
            stream.meta_event(meta_type, meta_data)
class MidiFileParser:
    def __init__(self, raw_in, outstream):
        self.raw_in = raw_in
        self.dispatch = EventDispatcher(outstream)
        self._running_status = None
    def parseMThdChunk(self):
        raw_in = self.raw_in
        header_chunk_type = raw_in.nextSlice(4)
        header_chunk_zise = raw_in.readBew(4)
        if header_chunk_type != 'MThd': raise TypeError, "It is not a valid midi file!"
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
            hi_nible, lo_nible = status & 0xF0, status & 0x0F
            if status == META_EVENT:
                meta_type = raw_in.readBew()
                meta_length = raw_in.readVarLen()
                meta_data = raw_in.nextSlice(meta_length)
                dispatch.meta_events(meta_type, meta_data)
            elif status == SYSTEM_EXCLUSIVE:
                sysex_length = raw_in.readVarLen()
                sysex_data = raw_in.nextSlice(sysex_length-1)
                if raw_in.readBew(move_cursor=0) == END_OFF_EXCLUSIVE:
                    eo_sysex = raw_in.readBew()
                dispatch.sysex_event(sysex_data)
            elif hi_nible == 0xF0:
                data_sizes = {
                    MTC:1,
                    SONG_POSITION_POINTER:2,
                    SONG_SELECT:1,
                }
                data_size = data_sizes.get(hi_nible, 0)
                common_data = raw_in.nextSlice(data_size)
                common_type = lo_nible
                dispatch.system_common(common_type, common_data)
            else:
                data_sizes = {
                    PATCH_CHANGE:1,
                    CHANNEL_PRESSURE:1,
                    NOTE_OFF:2,
                    NOTE_ON:2,
                    AFTERTOUCH:2,
                    CONTINUOUS_CONTROLLER:2,
                    PITCH_BEND:2,
                }
                data_size = data_sizes.get(hi_nible, 0)
                channel_data = raw_in.nextSlice(data_size)
                event_type, channel = hi_nible, lo_nible
                dispatch.channel_messages(event_type, channel, channel_data)
    def parseMTrkChunks(self):
        for t in range(self.nTracks):
            self._current_track = t
            self.parseMTrkChunk()
        self.dispatch.eof()
class MidiInFile:
    def __init__(self, outStream, infile=''):
        self.raw_in = RawInstreamFile(infile)
        self.parser = MidiFileParser(self.raw_in, outStream)
    def read(self):
        p = self.parser
        p.parseMThdChunk()
        p.parseMTrkChunks()
    def setData(self, data=''):
        self.raw_in.setData(data)

try: any
except: # Python 2.3 (RISC OS?)
  def any(x):
    for i in x:
      if i: return True
    return False
  def all(x):
    for i in x:
      if not i: return False
    return True

if acorn_electron: name = "MIDI to Acorn Electron"
elif (bbc_micro or bbc_micro==[]): name = "MIDI to BBC Micro"
elif riscos_Maestro: name = "MIDI to Maestro"
else: name = "MIDI Beeper"
sys.stderr.write(name+" (c) 2007-2010, 2015-2018 Silas S. Brown.  License: GPL\n")
if len(sys.argv)<2:
    sys.stderr.write("Syntax: python midi-beeper.py MIDI-filename ...\n")
    sys.exit(1)
for midiFile in sys.argv[1:]:
    init() ; dedup_chord,dedup_microsec = [],0
    dedup_microsec_error = 0
    sys.stderr.write("Parsing MIDI file "+midiFile+"\n")
    MidiInFile(MidiToBeep(), open(midiFile,"rb")).read()
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
        assert not maestroFile == midiFile
        sys.stderr.write("Writing Maestro file "+maestroFile+"... ")
        open(maestroFile,'wb').write(maestroData())
        sys.stderr.write("Finished\n")
    elif not aplay:
        sys.stderr.write("Playing "+midiFile+"\n")
        runBeep(" ".join(cumulative_params))
if bbc_files:
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
        bbc_micro.insert(i,'REP.:I.A$:IF LEN(A$):F.A%=1TO193STEP8:!P%=EVAL("&"+MID$(A$,A%,8)):P%=P%+4:N.:U.RIGHT$(A$,1)="*":EL.:U.0') ; i += 1 # horrible mix of if/else and repeat/until on 1 line in immediate mode so it copes with any extra blank lines that buggy emulators might insert
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
      # AUTO automatically stops once the line number would be >= 32768.  We can use this to avoid having to put an Escape into the keyboard buffer.
      # TODO: If user is pasting this in multiple chunks, and emulator adds a spurious newline at the beginning of each chunk (e.g. BeebEm 3 on Mac), AUTO start number needs decreasing (unless user makes sure not to include the newline at the end of each chunk if the emulator will add its own at the start of the next)
      bbc_micro = "\n".join(bbc_micro).split("\n")
      if len(bbc_micro) > 3277: bbc_micro.insert(0,"AU."+str(32768-len(bbc_micro))+",1") # (although if this is the case, program is extremely likely to exhaust the memory even in Bas128)
      else: bbc_micro.insert(0,"AU."+str(32770-10*len(bbc_micro)))
    print "\n".join(bbc_micro)
