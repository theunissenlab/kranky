import numpy as np
import scipy as sp
import struct
from bitarray import bitarray
import os
import wave
import datetime
import time
import Queue
import threading
import alsaaudio as aa


from lib import zmq_tools as zt
from lib.fifo import FifoFileBuffer
stimuli_dir = '/home/jknowles/data/doupe_lab/stimuli/'
trial_queue_size = 2 # FifoFileBuffernumber of trials to load into queue
data_queue_size = 10
dtype_out = np.int32;
scale_factor = 2**31-1
channel_def = {'ao0': 0, 
            'trigger': 1}
                
default_params = {}
default_params['ao_freq'] = 48000
default_params['ai_freq'] = 32000
default_params['n_trials'] = 5
default_params['stim_order'] = 2
default_params['trigger_length'] = 1 # ms
        
runflag = False
playflag = False



class PlaybackController(object):
    def __init__(self, params):
        self.params = params
        self.pcm = None
        self.periodsize = 2**11
        self.nchannels = 4
        self.channel_def = {'ao0': 0, 
                            'ao1': 1, 
                            'trigger0': 2, 
                            'trigger1': 3}

        self.trial_queue = Queue.Queue(maxsize=trial_queue_size)
        self.data_queue = Queue.Queue(maxsize=data_queue_size)
        self.message_queue = Queue.Queue()
        pass


    def connect_to_pcm(self, cardidx):
        if self.pcm is not None:
            pass

        self.pcm = aa.PCM(type=aa.PCM_PLAYBACK, mode=aa.PCM_NORMAL, card='plughw:%d,0'%cardidx)
        self.pcm.setchannels(self.nchannels)
        self.pcm.setrate(self.params['ao_freq'])
        self.pcm.setperiodsize(self.periodsize)
        self.pcm.setformat(aa.PCM_FORMAT_S32_LE)
        

        
          
        mixer = aa.Mixer(control='DAC', cardindex = cardidx)
        try:
            mixer.setvolume(100)
        except:
            pass
        try:
            mixer.setmute(0)
        except:
            pass
        try:
            mixer.close()
        except:
            pass
            

        pass



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
        code = np.append(code,[True]*16)
    code = np.append(code,[True])
    wf = np.zeros((n_samples))
    high_onsets = []
    high_offsets = []
    low_onsets = []
    low_offsets = []
    for k,value in enumerate(code):
        onset_idx = np.floor(params['ao_freq']*float(k)/baudrate)
        offset_idx = np.floor(params['ao_freq']*float(k+1)/baudrate)
        # print 'bite %d onset %d offset %d' % (k,onset_idx, offset_idx)
        wf[onset_idx:offset_idx] = value
        if value==1:
            high_onsets.append(onset_idx)
            high_offsets.append(offset_idx)
        else:
            low_onsets.append(onset_idx)
            low_offsets.append(offset_idx)
    # from matplotlib import pyplot as plt; plt.plot(wf); plt.show()
    # from matplotlib import pyplot as plt;
    # plt.plot(wf[0:1000]); plt.show()
    # import ipdb; ipdb.set_trace()

    return wf, high_onsets, low_onsets


def load_trial_data(pbc,trial,ktrial):
    stim0_wf = load_stim(trial['stim']).astype(dtype_out)
    stim1_wf = np.zeros(len(stim0_wf)).astype(dtype_out)
    stim2_wf = np.zeros(len(stim0_wf)).astype(dtype_out)
    trigger0_wf, hio, lowo = generate_trigger(pbc.params, len(stim0_wf), trial_idx = ktrial)
    trigger0_wf = np.multiply(trigger0_wf,1*scale_factor).astype(dtype_out)
    data = np.vstack((stim0_wf, stim1_wf, stim2_wf, trigger0_wf))
    return data

def load_intro_data(pbc, intro_length=1, intro_pulse_length=5e-3):
    data = np.zeros((4,pbc.params['ao_freq']*intro_length)).astype(dtype_out)
    idx0 = 1;
    idx1 = round(float(intro_pulse_length)*pbc.params['ao_freq'])+idx0
    data[2,idx0:idx1]=1*scale_factor
    return data
def load_end_data(pbc, end_length=1,end_pulse_length=5e-3):
    data = np.zeros((4,pbc.params['ao_freq']*end_length)).astype(dtype_out)
    # data[3,:] =-1*scale_factor
    idx0 = data.shape[1]-float(end_pulse_length)*pbc.params['ao_freq']
    data[2,idx0:-2]=1*scale_factor
    return data


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
    owfid.setnchannels(4)
    owfid.setframerate(params['ao_freq'])
    owfid.setsampwidth(4)
    lastnsamp = 0
    for ktrial, trial in enumerate(playback_plan['trials']):
        # load stimulus wf
        stimwf = load_stim(trial['stim'])
        # generate trigger
        trigwf, hio, lowo = generate_trigger(params, len(stimwf), trial_idx = ktrial,)
        # concatinate and save to output .wav
        data = np.vstack((stimwf.astype(dtype_out), np.multiply(trigwf,2**15-1).astype(dtype_out)))
        owfid.writeframes(data.tostring(order='F'))# write data to output file
        nsamp= owfid.getnframes()
        # write to .rec.paf
        recfid.write('trial[%d]: stim_index=%d; ao_range=[%d, %d]\n' % (ktrial, trial['stim']['stim_idx'], lastnsamp, nsamp))
        lastnsamp = nsamp
    owfid.close()
    recfid.close()
    pass


def trial_loader(pbc, playback_plan):
    global runflag, playflag
    # add intro
    sample_count = 0
    trial_data = load_intro_data(pbc)
    # trial_data[0,: ]= np.random.normal(0,2**20,trial_data[0,:].shape); trial_data[0,1]=2**29
    pbc.trial_queue.put(trial_data)
    sample_count += trial_data.shape[1]
    playflag = True
    # loop thru trials, adding to que
    for ktrial, trial in enumerate(playback_plan['trials']):
        if not runflag:
            return
        print "generating trial: %d" % ktrial
        trial_data = load_trial_data(pbc, trial, ktrial)
        # trial_data[0,: ]= np.random.normal(0,2**20,trial_data[0,:].shape); trial_data[0,1]=2**29
        pbc.trial_queue.put(trial_data)
        pbc.message_queue.put('trial[%d]: stim_index=%d; ao_range=[%d, %d]\n' % (ktrial, trial['stim']['stim_idx'], sample_count, sample_count+trial_data.shape[1]))
        sample_count += trial_data.shape[1]
    # add ending
    pbc.trial_queue.put(load_end_data(pbc))
    # add stop sig
    pbc.trial_queue.put("STOP")
    pass

def data_loader(pbc):
    chunk_length = pbc.periodsize#*pbc.nchannels
    chunk_length_bytes = chunk_length*4  #*pbc.nchannels
    buff = FifoFileBuffer()
    nsafeframes = int(float(pbc.params['ao_freq'])/chunk_length)
    global runflag, playflag
    while not playflag:
        pass

    # add some chunks to start
    for k in range(0,nsafeframes):
        pbc.data_queue.put(np.zeros((1,chunk_length),dtype=dtype_out).tostring())


    trial_count = 0
    chunk_count = 0
    while runflag:
        if buff.available < chunk_length_bytes:
            if pbc.trial_queue.qsize() > 0:
                trial_data = pbc.trial_queue.get()
                if trial_data is not "STOP":
                    trial_count += 1
                    trial_data[0,1]=2**30
                    trial_data = np.reshape(trial_data,(1,np.prod(trial_data.shape)),order='F')
                    buff.write(trial_data.tostring())
                    print "loading trial %d size (%d, %d)" % (trial_count, trial_data.shape[0], trial_data.shape[1])
                else: # exit:  dump rest of data and pass along stop message
                    pbc.data_queue.put(buff.read())
                    # add some chunks to end
                    for k in range(0,nsafeframes):
                        pbc.data_queue.put(np.zeros((1,chunk_length),dtype=dtype_out).tostring())
                    pbc.data_queue.put("STOP")
                    break

                # import ipdb; ipdb.set_trace()
        if buff.available >= chunk_length_bytes:
            # import ipdb; ipdb.set_trace()
            pbc.data_queue.put(buff.read(size=chunk_length_bytes))
            chunk_count += 1
            # print "loading chunk %d" % chunk_count
    pass

def ao_thread(pbc):
    global runflag, playflag
    while not playflag:
        pass
    count = 0
    while runflag:
        chunk = pbc.data_queue.get()
        if chunk is not "STOP":
            pbc.pcm.write(chunk)
            count += 1
        else:
            break
    runflag=False
    pass


def write_rec_header(recfid, params, stimset):
    recfid.write('format: "kranky 20150622"\n')
    recfid.write('date: "%s"\n' % str(datetime.datetime.now()))
    for key in params.keys():
        recfid.write('%s: %d\n' % (key, params[key]))
    for stim in stimset['stims']:
        recfid.write('stim[%d]: file="%s";\n' % (stim['stim_idx'], stim['fname']))

def find_data_location(data_path_root, DIR_PRE):
    DIR_NOW = os.listdir(data_path_root)
    unique = list(set(DIR_NOW)-set(DIR_PRE))
    if len(unique) > 0:
         return data_path_root + os.pathsep + unique[0]
    else:
        return None


def empty_que(que):
    while que.qsize() > 0:
        try:
            que.get(False)
        except:
            pass
    pass

def run_playback(cardidx, params, stimset, playback_plan, data_path_root="/home/jknowles/science_code/GUI/Builds/Linux/build/"):
    global runflag, playflag
    # open new .rec file
    # write static part of .rec
    # setup connection to daq

    pbc = PlaybackController(params)
    pbc.connect_to_pcm(cardidx)
    # import ipdb; ipdb.set_trace()



    # get dir list
    DIR_PRE = os.listdir(data_path_root)

    # start threads going
    runflag = True
    playflag = False
    t_tl = threading.Thread(target=trial_loader, args=(pbc, playback_plan))
    t_tl.start()
    t_dl = threading.Thread(target=data_loader, args=(pbc,))
    t_dl.start()
    t_ao = threading.Thread(target=ao_thread, args=(pbc,))
    t_ao.start()


    try:
        while runflag: # initially look for data directory
            data_path=find_data_location(data_path_root, DIR_PRE)
            if data_path is not None:
                # now we have the dir, open new .rec.paf file and write params
                rec_file_name = data_path + os.pathsep + "presentation.pbrec"
                print "Found Corresponding data: %s" % data_path
                print "Saving Rec File to: %s" % rec_file_name
                recfid = open(rec_file_name,'w')
                write_rec_header(recfid, pbc.params, stimset)
                break
        while runflag:
            # write messages to recfile as they exist
            if pbc.message_queue.qsize() > 0:
                message = pbc.message_queue.get()
                recfid.write(message)

            pass
    except Exception as e:
        raise e
    finally:
        runflag = False
        playflag = False
        try:
            empty_que(pbc.data_queue)
            pbc.data_queue.put("STOP", block = False)
        except:
            pass
        try:
            empty_que(pbc.trial_queue)
            pbc.trial_queue.put("STOP", block = False)
        except:
            pass




if __name__=="__main__":
    rc_fname = "./test.rc"
    cardidx = 1

    params, stimset = load_rc_file(rc_fname)
    params = default_params
    playback_plan=generate_playback_plan(params,stimset)
    # write_playback_audio_file(params, stimset, playback_plan, 'test.wav')
    run_playback(cardidx, params, stimset, playback_plan)
