import numpy as np
import scipy as sp



def load_rc_file(fname):
    params = {}
    stimset = {}
    with open(fname) as rcfid:
        for line in rcfid:
            print line
    params['ntrials']= 10
    return params, stimset

def generate_playback_plan(params, stimset):
    playback_plan = {}
    playback_plan['trials']=[]
    for ktrial in range(0,params['ntrials']):
        trial = {}
        playback_plan['trials'].append(trial)
    return playback_plan

def write_playback_audio_file(params, stimset, playback_plan):
    # open new rec file
    # open output wav file
    # begin iterating thru trials of playback plan.
    for trial in playback_plan['trials']:
        print trial
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
    try: 
        while Playing:
            if tb.ready:
                # generate trigger and load stimulus
                # add trial to tb
                pass
            if rb.buffer():
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
    write_playback_audio_file(params, stimset, playback_plan)
    # run_playback(params, stimset, playback_plan)

