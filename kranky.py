import numpy as np
import scipy as sp
import struct
from bitarray import bitarray
import os
import wave
import datetime

stimuli_dir = '/home/jknowles/data/doupe_lab/stimuli/'

class PlaybackBuffer(object):
    pass

default_params = {}
default_params['ao_freq'] = 44100
default_params['ai_freq'] = 32000
default_params['n_trials'] = 1000
default_params['stim_order'] = 2
default_params['trigger_length'] = 100


def load_rc_file(fname):
    params = dict(default_params)
    stimset = {}
    stimset['stims'] = []
    with open(fname) as rcfid:
        for line in rcfid:
            params, stimset = parse_rc_line(line, params, stimset) # returned for transparency
    return params, stimset

def parse_rc_line(line, params, stimset):
    if len(line.strip('\n'))>0:
        parts = line.strip('\n').split(' ')
        if parts[0].lower() == 'stim':
            if len(parts) > 1 and parts[1] == 'add':
                if len(parts) == 3:
                    stim = {}
                    stim['fname'] = parts[2]
                    stim['name'] = os.path.basename(stim['fname'])
                    head,tail = os.path.split(os.path.dirname(stim['fname']))
                    stim['stimset'] = tail
                    if not os.path.exists(stim['fname']):
                        stim['fname'] = os.path.join(stimuli_dir, stim['stimset'], stim['name'])
                    verify_stim(stim)
                    stimset['stims'].append(stim)
                    stimset['stims'][len(stimset['stims'])-1]['stim_idx'] = len(stimset['stims'])-1
                elif len(parts) == 4:
                    stim = {}
                    stim['stimset'] = parts[2]
                    stim['name'] = parts[3]
                    stim['fname'] = os.path.join(stimuli_dir, stim['stimset'], stim['name'])
                    verify_stim(stim)

        elif parts[0].lower() == "set":
            if len(parts)>2:
                params[parts[1]] = int(parts[2]) ###### make this parse different formats 
    return params, stimset # for transparency

def verify_stim(stim):
    load_stim(stim)
    pass

def load_stim(stim):
    if stim['fname'][-4:] == '.raw':
        fid = open(stim['fname'],'r')
        wf = np.fromfile(fid, dtype = '>i16')
        fid.close()

    elif stim['fname'][-4:] == '.wav':
        wfid = wave.open(stim['fname'],'r')
        wlen = wave.getnframes()
        wf = np.array(wfid.readframes(wlen))
        wfid.close()
    else: 
        raise(Exception('Unknown file type'))
    return wf


def generate_playback_plan(params, stimset):
    playback_plan = {}
    playback_plan['trials']=[]

    trial_list = np.array([])
    if params['stim_order'] == 0: # generate trials in given order
        while len(trial_list) < params['n_trials']:
            sl = np.arange(0,len(stimset['stims']))
            trial_list = np.append(trial_list, sl)
    elif params['stim_order'] == 1:
        raise(Excpetion('not supported yet'))
    elif params['stim_order'] == 2: # generate randomly shuffeled order 

        while len(trial_list) < params['n_trials']:
            sl = np.arange(0,len(stimset['stims']))
            np.random.shuffle(sl)
            trial_list = np.append(trial_list, sl)
    trial_list = trial_list[0:params['n_trials']]

    # generate trials according to plan
    for ktrial in range(0,params['n_trials']):
        trial = {}
        trial['trial_idx'] = ktrial
        trial['stim_idx'] = int(trial_list[ktrial])
        trial['stim'] = stimset['stims'][trial['stim_idx']]
        playback_plan['trials'].append(trial)

    return playback_plan

def generate_trigger(params, n_samples, trial_idx = None):

    baudrate = 1000
    code = np.array([1, 0, 1, 0, 1, 0],dtype=np.bool)
    if trial_idx is not None:
        tbytes = struct.pack('>H', trial_idx)
        tbits = bitarray(endian = 'big')
        tbits.frombytes(tbytes)
        # code.extend(tbits.tolist)
        code = np.append(code, tbits.tolist())
    else:
        code = np.append(code,[0]*16)

    wf = np.zeros((n_samples))
    high_onsets = []
    low_onsets = []
    for k,value in enumerate(code):
        onset_idx = np.floor(params['ao_freq']*float(k)/baudrate)
        offset_idx = np.floor(params['ao_freq']*float(k+1)/baudrate)-1
        # print 'bite %d onset %d offset %d' % (k,onset_idx, offset_idx)
        wf[onset_idx:offset_idx] = value
        if value is True:
            high_onsets.append(onset_idx)
        else:
            low_onsets.append(onset_idx)
    # from matplotlib import pyplot as plt; plt.plot(wf); plt.show()
    return wf, high_onsets, low_onsets

def write_playback_audio_file(params, stimset, playback_plan, output_filename):
    # open new .rec.paf file
    # open output wav files
    # begin iterating thru trials of playback plan.

    # open new .rec.paf file and write params
    recfid = open(output_filename + 'rec.paf','w')
    recfid.write('format: "kranky 20150622"\n')
    recfid.write('date: "%s"\n' % str(datetime.datetime.now()))
    for key in params.keys():
        recfid.write('%s: %d\n' % (key, params[key]))
    for stim in stimset['stims']:
        recfid.write('stim[%d]: file="%s";\n' % (stim['stim_idx'], stim['fname']))
    owfid=wave.open(output_filename,'wb')
    owfid.setnchannels(2)
    owfid.setframerate(params['ao_freq'])
    owfid.setsampwidth(2)
    lastnsamp = 0
    for ktrial, trial in enumerate(playback_plan['trials']):
        # load stimulus wf
        stimwf = load_stim(trial['stim'])
        # generate trigger
        trigwf, hio, lowo = generate_trigger(params, len(stimwf), trial_idx = ktrial,)
        # concatinate and save to output .wav
        data = np.vstack((stimwf.astype(np.int16), np.multiply(trigwf,2**15-1).astype(np.int16)))
        owfid.writeframes(data.tostring(order='F'))# write data to output file
        nsamp= owfid.getnframes()
        # write to .rec.paf
        recfid.write('trial[%d]: stim_index=%d; ao_range=[%d, %d]\n' % (ktrial, trial['stim']['stim_idx'], lastnsamp, nsamp))
        lastnsamp = nsamp
    owfid.close()
    recfid.close()
    pass

def run_playback(params, stimset, playback_plan):
    # open new .rec file
    # write static part of .rec
    # setup connection to daq
    # setup trial buffer
    # begin iterating thru trials of playback plan.
    ktrial = 0
    Playing = True
    pb = PlaybackBuffer()
    try: 
        while Playing:
            if pb.tb_ready:
                # generate trigger and load stimulus
                # add trial to tb
                pass
            if pb.rbuffer():
                # read messages from buffer
                # write messages to .rec file
                pass
            pass
        # write exit note to .rec file

            
    except Exception as e:
        # empty .rec buffer 
        # close rec file with error note
        raise(e) 
    pass


if __name__=="__main__":
    rc_fname = "./test.rc"
    params, stimset = load_rc_file(rc_fname)
    playback_plan = generate_playback_plan(params,stimset)
    write_playback_audio_file(params, stimset, playback_plan, 'test.wav')
    # run_playback(params, stimset, playback_plan)

