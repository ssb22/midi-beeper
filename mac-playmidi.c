// Mac OS X command-line program to play MIDI to
// external MIDI port, or to software synthesis if
// no external device is connected.

// v1.2 - Silas S. Brown 2020,2024 - public domain, no warranty

// Compile: cc -o /usr/local/bin/playmidi mac-playmidi.c -framework CoreFoundation -framework AudioToolbox -framework CoreMIDI

// Run: playmidi [deviceNo] file.mid [speed multiplier [start second [stop second]]]

// deviceNo, if specified, is
// -1 for internal synth (fallback default)
// 0 for 1st attached synth (default)
// 1 for 2nd attached synth, etc

// Where to find history:
// https://github.com/ssb22/midi-beeper.git
// and https://gitlab.com/ssb22/midi-beeper.git
// and https://bitbucket.org/ssb22/midi-beeper.git
// and https://gitlab.developers.cam.ac.uk/ssb22/midi-beeper
// and in China: https://gitee.com/ssb22/midi-beeper

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <AudioToolbox/AudioToolbox.h>
#include <CoreFoundation/CoreFoundation.h>

void helpAndExit() {
  fputs("Syntax: playmidi [deviceNo] file.mid [speed multiplier [start second [stop second]]]\n",stderr);
  exit(1);
}

volatile int gotInterrupt = 0;
void stopMusic(int sig) {
  gotInterrupt = 1;
}

int main(int argc,const char*argv[]) {
  fputs("playmidi 1.2 - Silas S. Brown 2020,2024 - public domain\n",stderr);
  if(argc < 2) helpAndExit();
  int offset = 0, deviceNo = 0; // auto
  if(atoi(argv[1]) || !strcmp(argv[1],"0")) {
    offset=1; deviceNo=atoi(argv[1]);
  }
  if(argc < 2+offset) helpAndExit();
  const char *filename = argv[1+offset];
  MusicSequence musicSeq; NewMusicSequence(&musicSeq);
  if(MusicSequenceFileLoad(musicSeq,CFURLCreateFromFileSystemRepresentation(NULL,(const UInt8*)filename,strlen(filename),false),kMusicSequenceFile_MIDIType,0)) {
    fprintf(stderr,"Cannot load MIDI from %s\n",filename);
    helpAndExit();
  }
  if(deviceNo>=0) {
  fputs("Checking for devices... ",stderr);
  if(MIDIGetNumberOfDestinations()) {
    if(!MusicSequenceSetMIDIEndpoint(musicSeq,MIDIGetDestination(deviceNo))) fputs("using CoreMIDI device\n",stderr);
    else fputs("unable to use; using OSX synthesis\n",stderr);
  } else fputs("none; using OSX synthesis\n",stderr);
  }
  MusicPlayer mPlayer; NewMusicPlayer(&mPlayer);
  MusicPlayerSetSequence(mPlayer,musicSeq);
  if(argc>3+offset) {
    double startSecond=atof(argv[3+offset]);
    MusicTimeStamp startPoint;
    if(!MusicSequenceGetBeatsForSeconds(musicSeq,startSecond,&startPoint)) MusicPlayerSetTime(mPlayer,startPoint);
    else {
      fprintf(stderr,"Invalid start time: %s\n",argv[3+offset]);
      helpAndExit();
    }
  }
  MusicTimeStamp stopPoint;
  if(argc>4+offset) {
    double stopSecond=atof(argv[4+offset]);
    if(MusicSequenceGetBeatsForSeconds(musicSeq,stopSecond,&stopPoint)) {
      fprintf(stderr,"Invalid stop time: %s\n",argv[4+offset]);
      helpAndExit();
    }
  } else { // stop at end of longest track
    UInt32 nTracks; if(MusicSequenceGetTrackCount(musicSeq, &nTracks)) nTracks=1;
    MusicTimeStamp maxStopPoint;
    for(int trackNo=0; trackNo<nTracks; trackNo++) {
      MusicTrack t; MusicSequenceGetIndTrack(musicSeq,trackNo,&t);
      UInt32 n=sizeof(MusicTimeStamp); MusicTrackGetProperty(t,kSequenceTrackProperty_TrackLength,&stopPoint,&n);
      if(!trackNo || stopPoint>maxStopPoint) maxStopPoint = stopPoint;
      else stopPoint=maxStopPoint;
    }
  }
  double stopSecs; MusicSequenceGetSecondsForBeats(musicSeq,stopPoint,&stopSecs);
  double playRate = 1.0;
  if(argc>2+offset) {
    playRate=atof(argv[2+offset]);
    if(playRate<=0) {
      fprintf(stderr,"Not a speed: %s\n",argv[2+offset]);
      helpAndExit();
    } MusicPlayerSetPlayRateScalar(mPlayer,playRate);
  }
  MusicPlayerStart(mPlayer);
  signal(SIGINT,stopMusic);
  MusicTimeStamp now; double nowSecs;
  do {
    usleep(100000/playRate);
    if(!MusicPlayerGetTime(mPlayer, &now) && !MusicSequenceGetSecondsForBeats(musicSeq,now,&nowSecs))
      fprintf(stderr,"\r%.1lf/%.1lf",nowSecs,stopSecs);
  } while(now<stopPoint && !gotInterrupt);
  MusicPlayerStop(mPlayer); fputs("\n",stderr); return 0;
}
