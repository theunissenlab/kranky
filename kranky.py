# load rc file
# load and verify stimuli
# generate stimuli, triggers, and write rec file
# que trigger (and recording in future)



def load_rc file(fname):
    params = {}
    stimset = {}
    return params, stimset

def generate_playback_plan(params, stimset):
    playback_plan = {}
    return playback_plan

def write_playback_audio_file(params, stimset, playback_plan):
    # open new rec file
    # open output wav file
    # begin iterating thru trials of playback plan.
    for trial in playback_plan['trials']:
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
        # write exit note to .rec.pb file

            
    except Exception as e:
        # empty .rec buffer then close rec file with error note
        raise(e) 

    pass


if __name__=="__main__":
    rc_fname = "./test.rc"
