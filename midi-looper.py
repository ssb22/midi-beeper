#!/usr/bin/env python3
"""MIDI looper for Raspberry Pi + USB MIDI keyboard
(c) Silas S. Brown 2026.  License: Apache 2

Records until silence, then loops with overdubbing.
Ctrl+C to stop and save."""
# (I did say "public domain no warranty" but apparently
# some corporate offices don't trust that.  Apache 2 lets
# them know I don't have a silly patent up my sleeve that
# I'd try to enforce, so their policy might accept it more
# easily if you need to use this at work.)

import sys,time,datetime,queue
def loop(silenceSecs=2):
    print("Loading mido...") # Pi 1 B+: 4 to 15 seconds
    import mido # apt install python3-mido python3-rtmidi, or pip install mido rtmidi
    q,loop,active_notes,waiting,playing = queue.Queue(),[],set(),True,False
    ins,outs = mido.get_input_names(),mido.get_output_names()
    def preferred(n): return 'USB' in n.upper() or 'CASIO' in n.upper()
    inN,outN = next((n for n in ins if preferred(n)),ins[0]),next((n for n in outs if preferred(n)),outs[0])
    port_in,port_out=mido.open_input(inN,callback=lambda msg:q.put((time.monotonic(),msg.copy()))),mido.open_output(outN)
    print(f"MIDI connected: {inN} -> {outN}")
    i,N,t0=0,0,0
    print("Ready. Play a note to start recording...")
    try:
      while True:
        while not q.empty():
          t,msg=q.get()
          if (msg.type=='note_on' and msg.velocity==0 or msg.type=='note_off') and (waiting or (msg.channel, msg.note) not in active_notes): continue # ignore spurious note-off from previous loop etc
          if waiting:
            t0=t
            if msg.type=='note_on': waiting=False
          loop.append((t-t0,msg))
          if msg.type=='note_on' and msg.velocity: active_notes.add((msg.channel,msg.note))
          elif msg.type=='note_off' or (msg.type=='note_on' and msg.velocity==0): active_notes.discard((msg.channel,msg.note))
          latest_event=t
        while i<N and time.monotonic()>=t0+loop[i][0]:
          port_out.send(loop[i][1])
          i += 1
        if not waiting and not playing and not active_notes and time.monotonic()-latest_event >= silenceSecs:
          print(f"Silence detected ({silenceSecs}s)")
          playing=True
        if playing and i>=N: # play it again
          loop.sort(key=lambda x:x[0])
          for c,n in active_notes: loop.append((loop[-1][0],mido.Message('note_off',channel=c,note=n)))
          i,N,active_notes,t0 = 0,len(loop),set(),time.monotonic()
        time.sleep(0.01)
    except KeyboardInterrupt: print("\nStopping...")
    finally:
      t = time.monotonic()
      if playing:
        print("\nSending All Notes Off...")
        for ch in range(16): port_out.send(mido.Message('control_change',channel=ch,control=120,value=0)),port_out.send(mido.Message('control_change',channel=ch,control=123,value=0))
      port_in.close(),port_out.close()
      if loop:
        mf = mido.MidiFile(ticks_per_beat=480)
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('set_tempo',tempo=500000))
        mf.tracks.append(track)
        for c,n in active_notes: loop.append((t-t0,mido.Message('note_off',channel=c,note=n)))
        loop.sort(key=lambda x:x[0]); t0 = 0
        for t,msg in loop:
            track.append(msg.copy(time=mido.second2tick(t-t0,mf.ticks_per_beat,500000)))
            t0 = t
        filename=datetime.datetime.now().strftime("loop%Y%m%d_%H%M%S.mid")
        mf.save(filename),print(f"Saved to {filename}")

if __name__ == "__main__": loop()
