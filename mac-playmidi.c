// Mac OS X command-line program to play MIDI to
// external MIDI port, or to software synthesis if
// no external device is connected.

// Silas S. Brown 2020 - public domain - no warranty.

// Compile: cc -o /usr/local/bin/playmidi mac-playmidi.c -framework CoreFoundation -framework AudioToolbox -framework CoreMIDI

// Run: playmidi file.mid [speed multiplier [start second [stop second]]]

#include <stdio.h>
#include <stdlib.h>
#include <AudioToolbox/AudioToolbox.h>
#include <CoreFoundation/CoreFoundation.h>

void helpAndExit() {
  fputs("Syntax: playmidi file.mid [speed multiplier [start second [stop second]]]\n",stderr);
  fputs("(set file.mid to - to use /dev/stdin)\n",stderr);
  exit(1);
}

int main (int argc,const char*argv[]) {
  fputs("playmidi 1.0 - Silas S. Brown 2020 - public domain\n",stderr);
  if(argc < 2) helpAndExit();
  const char *filename = argv[1];
  if(!strcmp(filename,"-")) filename="/dev/stdin";
  MusicSequence musicSeq; NewMusicSequence(&musicSeq);
  if(MusicSequenceFileLoad(musicSeq,CFURLCreateFromFileSystemRepresentation(NULL,(const UInt8*)filename,strlen(filename),false),kMusicSequenceFile_MIDIType,0)) {
    fprintf(stderr,"Cannot load MIDI from %s\n",filename);
    helpAndExit();
  }
  fputs("Checking for devices... ",stderr);
  if(MIDIGetNumberOfDestinations()) {
    if(!MusicSequenceSetMIDIEndpoint(musicSeq,MIDIGetDestination(0))) fputs("using CoreMIDI device\n",stderr);
    else fputs("unable to use; using OSX synthesis\n",stderr);
  } else fputs("none; using OSX synthesis\n",stderr);
  MusicPlayer mPlayer; NewMusicPlayer(&mPlayer);
  MusicPlayerSetSequence(mPlayer,musicSeq);
  if(argc>3) {
    double startSecond=atof(argv[3]);
    MusicTimeStamp startPoint;
    if(!MusicSequenceGetBeatsForSeconds(musicSeq,startSecond,&startPoint)) MusicPlayerSetTime(mPlayer,startPoint);
    else {
      fprintf(stderr,"Invalid start time: %s\n",argv[3]);
      helpAndExit();
    }
  }
  MusicTimeStamp stopPoint;
  if(argc>4) {
    double stopSecond=atof(argv[4]);
    if(MusicSequenceGetBeatsForSeconds(musicSeq,stopSecond,&stopPoint)) {
      fprintf(stderr,"Invalid stop time: %s\n",argv[4]);
      helpAndExit();
    }
  } else { // stop at end of index track
    MusicTrack t; MusicSequenceGetIndTrack(musicSeq,0,&t);
    UInt32 n=sizeof(MusicTimeStamp); MusicTrackGetProperty(t,kSequenceTrackProperty_TrackLength,&stopPoint,&n);
  }
  double stopSecs; MusicSequenceGetSecondsForBeats(musicSeq,stopPoint,&stopSecs);
  double playRate = 1.0;
  if(argc>2) {
    playRate=atof(argv[2]);
    if(!playRate) {
      fprintf(stderr,"Not a speed: %s\n",argv[2]);
      helpAndExit();
    } MusicPlayerSetPlayRateScalar(mPlayer,playRate);
  }
  MusicPlayerStart(mPlayer);
  MusicTimeStamp now; double nowSecs;
  do {
    usleep(100000/playRate);
    if(!MusicPlayerGetTime(mPlayer, &now) && !MusicSequenceGetSecondsForBeats(musicSeq,now,&nowSecs))
      fprintf(stderr,"\r%.1lf/%.1lf",nowSecs,stopSecs);
  } while(now<stopPoint);
  MusicPlayerStop(mPlayer); fputs("\n",stderr); return 0;
}
