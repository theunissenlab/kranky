## Kranky

Kranky is a stimulus presentation system rolled in python to control the playback of auditory stimuli in neuroscience experiments. It's originally designed to be compatiple with instructions for krank, developed in the doupe lab. 

usage: 
(see python kranky -h)


## .rc file
The .rc file describes the stimuli and trial parameteres.  Arguments can also be entered in the call to kranky, which override the .rc file specifications


```
### example rc file
stim add /tazo/jknowles/stimuli/probe_songs2/probe_songs2_song1.raw
stim add /tazo/jknowles/stimuli/probe_songs2/probe_songs2_song2.raw
stim add /tazo/jknowles/stimuli/probe_songs2/probe_songs2_song1flipped.raw

# stim list
set ao_freq 40000
set ai_freq 32000
set n_trials 10
set stim_order 2
set ramp_time 0
set attenuation 15
set attenuation2 0
#!


```


## stimulus files
Kranky accepts .wav files and raw binary (.raw) are 16 bit integers. All stimuli in a presentation should have the same sampling rate, but this is enforced for .wav files.  

## .rec files

## open ephys

## output to .wav file
Kranky can also write to a wav file:  

	python kranky.py test.rc --wav



Kranky is built to run on alsa (and soon NI) but is constructed in such a way that makes it easy build a ao thread to play out in other systems.


	

usage: kranky.py [-h] [-n N_TRIALS] [-r REQUIRE_DATA] [-d DATA_DIR]
                 [-s STIM_DIR] [-o STIM_ORDER] [--wav WAV]
                 rc_fname

positional arguments:
  rc_fname

optional arguments:
  -h, --help            show this help message and exit
  -n N_TRIALS, --n-trials N_TRIALS
                        trials help
  -r REQUIRE_DATA, --require-data REQUIRE_DATA
                        force data help
  -d DATA_DIR, --data-dir DATA_DIR
                        data directory help
  -s STIM_DIR, --stim-dir STIM_DIR
                        stimulus directory help
  -o STIM_ORDER, --stim_order STIM_ORDER
                        stimulus directory help
  --wav WAV             wav help