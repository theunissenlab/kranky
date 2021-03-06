## Kranky

Kranky is a stimulus presentation system rolled in python to control the playback of auditory stimuli in neuroscience experiments. It is easy to control and modify, and integrates with open-ephys. It is implemented with multi-layered threaded buffers that should stream to basically any devices without issue.    

kranky is compatible with instructions for krank, a stimulus presenter and data acquisition program developed in the doupe lab by [David Schleef ](http://schleef.org/). 

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

Here is an example rc file:    

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
Kranky accepts .wav files and raw binary (.raw) are 16 bit integers. All stimuli in a presentation should have the same sampling rate, but this is (can be) only checked for .wav files.  

If kranky can't find the file with the path in the rc file, it will look for the inside 'stim_dir', under the assumption that the stimulus file resides in a subdirectory of 'stim_dir'.  


## .pbrec and .rec files
.rec files are a record of the playback and capture for future analysis. kranky saves .pbrec files which contain all the information about the stimulus presentation as it happens in 'data_dir', or inside the directory containing open-ephys data if it finds that directory in 'data-dir'. After an aquisition, the matlab function write_kranky_recfile.m  will parse the digital trigger data from open-ephys and write a '.rec' file, which is .pbrec plus ai clock samples when the stimuli happened.

## trigger system
kranky automatically generates ttl trigger signals at the start of each trial to input into open-ephys/intan digital inputs. The trigger is basically like a serial pulse that contains three square waves (for timing allignment) followed by a le digital packet encoding the trial number. These triggers are parsed by [write_kranky_recfile.m](https://bitbucket.org/spikeCoder/kranky/src/master/analysis_tools/write_kranky_recfile.m), using [parse_kranky_triggers.m](https://bitbucket.org/spikeCoder/kranky/src/master/analysis_tools/parse_kranky_triggers.m). These functions assume the trigger has been routed into open-ephys di2. The baud rate is 1000Hz.  

## open ephys and record control
kranky is built to run along with a special version of open ephys.  You can download my fork here:
https://github.com/Jeffknowles/GUI.  This fork has minor changes from the main version of open ephys to play nicely with kranky.  
1) Record control interprets pulses and is more robust to possible bounces on the incoming ttl signal. 
2) everytime recording is triggered, open-ephys makes a new data directory rather than appending on the data in the same directory. 

You can use either open-ephys format or kwik format (selected in open ephys). The kranky/analysis_tools are written for the open-ephys format.  Apparently there are some issues with the (otherwise superior) kwik format getting corrupted.  See discussion [here](https://groups.google.com/forum/#!topic/klustaviewas/LmeDzuQLxgM)

The open-ephys folks did a great job making an adaptable data aquisition GUI for neural data.  An example open-ephys configuration file for use with kranky is provided with my fork.  

## analog output
Kranky is built to write output using alsa or comedi.  However, the program is constructed in such a way that makes it easy build a ao thread to play out in other systems.

## digital output
Kranky provides several options for time locked digital outputs depending on your requirements and hardware. In general, most (inexpensive) devices don't do a great job of streaming out digital outputs time locked with analog outputs. 
### analog output as ttl
If only a few digital outputs are required (ie record control, time/trial trigger, you can use analog channels as de-facto ttl channels. Kranky makes this easy and takes care of controlling the range of an analog signal to 
### "analogO->analogI-> Digital" (aad) 
Another option I came up with is to use an analog output to encode several ttl outputs. The most significant bits of the analog output encode the state of several (I have used up to 4) digital outputs. The decoding of this signal can be implemented with lots cheap hardware options, but kranky includes code to run on an arduino to read in analog signal and write out a digital signal (kranky/lib/arduino_aad). A basic arduino uno will do this with a 15us period, which is equivilent to ~66KhZ which is overkill or anything but the most Jim Simmonsesque applications. Faster processes would even make Jim happy!

To use AAD with an arduino: 

1.  deploy [kranky/lib/arduino_aad](https://bitbucket.org/spikeCoder/kranky/src/master/lib/arduino_aad/arduino_aad.ino) to an arduino and connect aad channel to Ai0.  
1.  turn on AAD in kranky (--do-aad 1) 
1.  turn set AAD Channel
1.  now any digital channels will be encoded as aad
1.  to send record control and or trigger over aad, use negative channel numbers
 

### Streaming Digital Outputs 
A third option if your hardware supports simultaneous streaming of analog and digital signals is to just stream out the digital.  Let me know if you find a cheap option that does this well!  I have thought about hacking apart a single analog output on a sound card as this would provide DO's implemented as AAD without the need to send it through a decoder.  

 
## output to .wav file
Kranky can also write to a wav file from kranky:  

	python kranky.py test.rc --wav


## Arguments / Parameters:  
The parameters are as follows: 
```
data_dir  [defaults to current directory]
n_trials [defaults to 100]
trigger_channel [defaults to 3]
record_control_channel [defaults to 2]
stim_order [defaults to 2]
cardidx: [defaults to 'comedi' if comedi is installed, otherwise to card 0]
aad_channel: [defaults to None]
stim_dir [defaults to jeff's folder /home/jknowles/data/doupe_lab/stimuli sorry!]
n_ao_channels: [defaults to 4]
ao_freq [defaults to 40000]
wav: [defaults to false]
do_aad [defaults to false]
require_data [defaults to true]
```
see ./kranky -h (print out below) for information about each parameter
```
#!bash
./kranky -h
usage: kranky [-h] [-c CARDIDX] [-n N_TRIALS] [-r REQUIRE_DATA] [-d DATA_DIR]
              [-s STIM_DIR] [-o STIM_ORDER]
              [--trigger-channel TRIGGER_CHANNEL]
              [--record-control-channel RECORD_CONTROL_CHANNEL]
              [--do-aad DO_AAD] [--aad-channel AAD_CHANNEL]
              [--ao-freq AO_FREQ] [--n-ao-channels N_AO_CHANNELS] [--wav WAV]
              rc_fname

Stimuluis Presenter for Neuroscience Experiments. Jeff Knowles, 2015;
jeff.knowles@gmail.com

positional arguments:
  rc_fname

optional arguments:
  -h, --help            show this help message and exit
  -c CARDIDX, --cardidx CARDIDX
                        alsa card number
  -n N_TRIALS, --n-trials N_TRIALS
                        number of trials to run
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
  --trigger-channel TRIGGER_CHANNEL
                        Channel for timing trigger signal. If ch > 0, the
                        signal is routed through analog output on the channel
                        provided. If ch < 0, the trigger is produced on an
                        aad-ch, encoded on the aad output channel
  --record-control-channel RECORD_CONTROL_CHANNEL
                        Channel for recording control signal. If ch > 0, the
                        signal is routed through analog output on the channel
                        provided. If ch < 0, the record control is produced on
                        an aad-ch, encoded on the aad output channel.
  --do-aad DO_AAD       Specify whether to route channels through aad
                        (analog->analog->digital. If do_aad is false, then all
                        negative channel numbers are ignored
  --aad-channel AAD_CHANNEL
                        Channel for aad (analog->analog->digital) output. Four
                        ttl channels are encoded in one analog channel. If ch
                        > 0, the signal is routed through analog output on the
                        channel provided. If trigger_channel < 0, the trigger
                        is produced on an aad-ch, encoded on the aad output
                        channel
  --ao-freq AO_FREQ
  --n-ao-channels N_AO_CHANNELS
  --wav WAV             write a .wav file instead of doing playback

Note: All optional arguments may also be entered into the rc file, by ommiting
-- and replacing - with _ (eg data_dir, n_ao_channels, require_data replace
--data-dir, --n-ao-channels, --require-data, ext.) Command line args override
rc file args, which override default params.
```