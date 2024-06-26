#!/usr/bin/env python
#   (works on both Python 2 and Python 3)

# MIDI ringtone generator (c) Silas S. Brown
# See http://ssb22.user.srcf.net/compos/noise.html#ringtone

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

# Some code was taken from an old version of
# Python Midi Package by Max M.

# History is in https://github.com/ssb22/midi-beeper.git
# and https://gitlab.com/ssb22/midi-beeper.git
# and https://bitbucket.org/ssb22/midi-beeper.git
# and https://gitlab.developers.cam.ac.uk/ssb22/midi-beeper
# and in China: https://gitee.com/ssb22/midi-beeper

try: from cStringIO import StringIO # Python 2
except: from io import BytesIO as StringIO # Python 3
from struct import pack, unpack
def writeBew(value, length):
    return pack('>%s' % {1:'B', 2:'H', 4:'L'}[length], value)
def varLen(value):
    if value <= 127: return 1
    elif value <= 16383: return 2
    elif value <= 2097151: return 3
    else: return 4
def writeVar(value):
    sevens = to_n_bits(value, varLen(value))
    for i in range(len(sevens)-1):
        sevens[i] = sevens[i] | 0x80
    return fromBytes(sevens)
def to_n_bits(value, length=1, nbits=7):
    bytes = [(value >> (i*nbits)) & 0x7F for i in range(length)]
    bytes.reverse()
    return bytes
def B(s):
    if type("")==type(u""): return s.encode("utf-8") # Python 3
    else: return s # Python 2
def fromBytes(value):
    if not value:
        return B('')
    return pack('%sB' % len(value), *value)
class RawOutstreamFile:
    def __init__(self, outfile=None):
        if not outfile: outfile = B('')
        self.buffer = StringIO()
        self.outfile = outfile
    def writeSlice(self, str_slice):
        self.buffer.write(str_slice)
    def writeBew(self, value, length=1):
        self.writeSlice(writeBew(value, length))
    def writeVarLen(self, value):
        var = self.writeSlice(writeVar(value))
    def write(self):
        if self.outfile:
            if type(self.outfile)==str:
                outfile = open(self.outfile, 'wb')
                outfile.write(self.getvalue())
                outfile.close()
            else:
                self.outfile.write(self.getvalue())
    def getvalue(self):
        return self.buffer.getvalue()
class MidiOutFile:
    def update_time(self, new_time=0):
        self._relative_time += int(new_time)
    def reset_time(self):
        self._relative_time = 0
    def rel_time(self):
        return self._relative_time
    def __init__(self, raw_out=None):
        if not raw_out: raw_out = B('')
        self.raw_out = RawOutstreamFile(raw_out)
        self._relative_time = 0
        self._current_track = 0
        self._running_status = None
    def write(self):
        self.raw_out.write()
    def event_slice(self, slc):
        trk = self._current_track_buffer
        trk.writeVarLen(self.rel_time())
        trk.writeSlice(slc)
    def note_on(self, channel=0, note=0x40, velocity=0x40):
        slc = fromBytes([0x90 + channel, note, velocity])
        self.event_slice(slc)
    def note_off(self, channel=0, note=0x40, velocity=0x40):
        slc = fromBytes([0x80 + channel, note, velocity])
        self.event_slice(slc)
    def patch_change(self, channel, patch):
        slc = fromBytes([0xC0 + channel, patch])
        self.event_slice(slc)
    def header(self, format=0, nTracks=1, division=96):
        raw = self.raw_out
        raw.writeSlice(B('MThd'))
        bew = raw.writeBew
        bew(6, 4) 
        bew(format, 2)
        bew(nTracks, 2)
        bew(division, 2)
    def start_of_track(self, n_track=0):
        self._current_track_buffer = RawOutstreamFile()
        self.reset_time()
        self._current_track += 1
    def end_of_track(self):
        raw = self.raw_out
        raw.writeSlice(B('MTrk'))
        track_data = self._current_track_buffer.getvalue()
        eot_slice = writeVar(self.rel_time()) + fromBytes([0xFF, 0x2F, 0])
        raw.writeBew(len(track_data)+len(eot_slice), 4)
        raw.writeSlice(track_data)
        raw.writeSlice(eot_slice)
    def tempo(self, value):
        data_slice = fromBytes([
            (value>>16 & 0xff),
            (value>>8 & 0xff), (value & 0xff)])
        self.event_slice(
            fromBytes([0xFF, 0x51]) +
            writeVar(len(data_slice)) +
            data_slice)

mof = MidiOutFile('ringtone.mid')
mof.header()
mof.start_of_track()
mof.patch_change(0,73) # flute
mof.tempo(1000000)
import random
pitches = [0x40+random.randint(-10,20)]
for i in range(random.randint(1,3)): pitches.append(pitches[-1]+random.randint(1,10))
softPitches = [(c,pitches[c]) for c in range(len(pitches))]
pitches *= 16 ; loudPitches = [(c,pitches[c]) for c in range(16) if not c==9] # duplicate on all channels except percussive-10 (9 when 0-based); helps some synths make it not too soft
burstsPerRing = random.randint(7,14)
totalCycleLen = 150
half_burstTime = int(totalCycleLen*0.4/burstsPerRing/2)
for velocity in [0x40,0x40,0x50,0x60,0,0x60,0x70,0x7f,0x7f,0,0x30,0x20,0x10,0x10,0]+[0x10,0x10,0x10,0x10,0]*10: # *4 is probably more than enough for the network to give up
    for ring in [1,2]: # UK double-ring
        for i in range(burstsPerRing):
            if velocity > 0x40: pitches = loudPitches
            elif velocity: pitches = softPitches
            else: pitches = []
            for c,p in pitches: mof.note_on(c,p,velocity),mof.reset_time()
            mof.update_time(half_burstTime)
            for c,p in pitches: mof.note_off(c,p,velocity),mof.reset_time()
            mof.update_time(half_burstTime)
        mof.update_time(totalCycleLen/10)
    mof.update_time(totalCycleLen/2)
mof.end_of_track() ; mof.write()
print ("Generated a ringtone.mid (run again for another)")
