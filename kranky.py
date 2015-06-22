import numpy as np
import scipy as sp


class PlaybackBuffer(object):
    pass


default_params = {}
default_params['ao_freq'] = 44100
default_params['ai_freq'] = 32000
default_params['n_trials'] = 1000
default_params['stim_order'] = 2



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
            if len(parts)> 0 and parts[1] == 'add':
                stim = {}
                stim['fname'] = parts[2]
                stim['name'] = stim['fname']
                verify_stim(stim)
                stimset['stims'].append(stim)
                stimset['stims'][len(stimset['stims'])-1]['stim_idx'] = len(stimset['stims'])-1
        elif parts[0].lower() == "set":
            if len(parts)>2:
                params[parts[1]] = int(parts[2]) ###### make this parse different formats 
    return params, stimset # for transparency

def verify_stim(stim):
    pass

def generate_playback_plan(params, stimset):
    playback_plan = {}
    playback_plan['trials']=[]

    trial_list = np.array([])
    if params['stim_order'] == 0: # generate trials in given order
        while len(trial_list) < params['n_trials']:
            trial_list = np.append(trial_list, np.arange(0,len(stimset['stims'])))
    elif params['stim_order'] == 1:
        raise(Excpetion('not supported yet'))
    elif params['stim_order'] == 2: # generate randomly shuffeled order 
        while len(trial_list) < params['n_trials']:
            trial_list = np.append(trial_list, np.random.shuffle(np.arange(0,len(stimset['stims']))))
    trial_list = trial_list[0:params['n_trials']]

    # generate trials according to plan
    for ktrial in range(0,params['n_trials']):
        trial = {}
        trial['trial_idx'] = ktrial
        trial['stim_idx'] = int(trial_list[ktrial])
        trial['stim'] = stimset['stims'][trial['stim_idx']]
        playback_plan['trials'].append(trial)

    return playback_plan

def write_playback_audio_file(params, stimset, playback_plan):
    # open new rec file
    # open output wav file
    # begin iterating thru trials of playback plan.
    for ktrial, trial in enumerate(playback_plan['trials']):
        # print ktrial, trial['stim']['name']
        # generate trigger and load stimulus
        # write data to output file
        # write to .rec.paf
        pass
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
    print params
    playback_plan = generate_playback_plan(params,stimset)
    write_playback_audio_file(params, stimset, playback_plan)
    # run_playback(params, stimset, playback_plan)

