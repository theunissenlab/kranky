## Kranky

Kranky is a stimulus presentation system rolled in python to control the playback of auditory stimuli in neuroscience experiments. It is easy to control and modify, and integrates with open-ephys.  

kranky is compatible with instructions for krank, a stimulus presenter and data acquisition program developed in the doupe lab. 


## usage: 
see ./kranky -h

## .rc file
The .rc file describes the stimuli and trial parameters.  Parameters can also be entered as arguments to in the call to kranky, which override the .rc file specifications (see ./kranky -h). Stimuli are added with 
```
stim add stim1 stim2...  
```
By default, stimuli are assumed analog out channels unless they are specified as ttl:
```
stim add aostim0.wav ttl-ttlstim0.wav
stim add ao-aostim0.wav ttl-ttlstim0.wav
```
these two entries are equivalent.  

```
### example rc file

# add the stimuli
stim add ao:/tazo/jknowles/stimuli/probe_songs2/probe_songs2_song1.raw 
stim add /tazo/jknowles/stimuli/probe_songs2/probe_songs2_song2.raw
stim add /tazo/jknowles/stimuli/probe_songs2/probe_songs2_song1flipped.raw

# set the parameters
set ao_freq 40000
set n_trials 10
set stim_order 2
```


## stimulus files
Kranky accepts .wav files and raw binary (.raw) are 16 bit integers. All stimuli in a presentation should have the same sampling rate, but this is enforced for .wav files.  
## .rec files
.rec files save a record of the playback and capture for future analysis. kranky.py saves .pbrec files which contain all the information about the stimulus presentation as it happens. It similtaniously looks at the data coming in to write .rec from the .pbrec files.  .rec is .pbrec plus ai clock samples when the stimuli happened.

## trigger system
(will write up soon). 

## open ephys
kranky is built to run along with a special version of open ephys.  You can download my fork here:
https://github.com/Jeffknowles/GUI

## analog output
Kranky is built to write output using alsa or comedi.  However, the program is constructed in such a way that makes it easy build a ao thread to play out in other systems.

## digital output
(will write up soon)

## output to .wav file
Kranky can also write to a wav file:  

	python kranky.py test.rc --wav




```
#!bash
kranky -h
usage: kranky [-h] [-c CARDIDX] [-n N_TRIALS] [-r REQUIRE_DATA] [-d DATA_DIR]
              [-s STIM_DIR] [-o STIM_ORDER] [--ao-freq AO_FREQ] [--wav WAV]
              rc_fname

positional arguments:
  rc_fname

optional arguments:
  -h, --help            show this help message and exit
  -c CARDIDX, --cardidx CARDIDX
                        alsa card number
  -n N_TRIALS, --n-trials N_TRIALS
                        trials help
  -r REQUIRE_DATA, --require-data REQUIRE_DATA
                        require that new data be found in data dur to continue
  -d DATA_DIR, --data-dir DATA_DIR
                        directory to look for data dir from data capture
                        software
  -s STIM_DIR, --stim-dir STIM_DIR
                        directory containing stim-sets. If the exact directory
                        passed in the rc file isnt found, kranky looks for the
                        stimset here.
  -o STIM_ORDER, --stim-order STIM_ORDER
                        How to order the stimuli. 0=in the order provided
                        2=randomly interleaved
  --ao-freq AO_FREQ
  --wav WAV             write a .wav file instead of doing playback


```