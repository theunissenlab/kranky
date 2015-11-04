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
import traceback
import argparse

# from lib import zmq_tools as zt
from lib.fifo import FifoFileBuffer
try:
    from lib.pycomedi_tools import ComediWriter, run_aad_thread, aad_factor, aad_offset
except ImportError as e:
    ComediWriter = None

trial_queue_size = 5 # FifoFileBuffernumber of trials to load into queue
data_queue_size = 5


# dtype_out = np.dtype(np.int16)
# nbytes = dtype_out.itemsize
# scale_factor = 2**(8*nbytes-1)-1

                 
runflag = False
playflag = False
class PlaybackController(object):
    def __init__(self, params):
        self.params = params
        self.pcm = None
        self.pcm_type = None
        self.dtype_out = None 
        self.periodsize = 1024#2**12sa
        self.trial_queue = Queue.Queue(maxsize=trial_queue_size)
        self.data_queue = Queue.Queue(maxsize=data_queue_size)
        self.message_queue = Queue.Queue()
        pass


    def connect_to_pcm(self, cardidx):
        if self.pcm is not None:
            pass
        self.pcm = aa.PCM(type=aa.PCM_PLAYBACK, mode=aa.PCM_NORMAL, card='plughw:%d,0'%cardidx)
        # self.pcm = aa.PCM(type=aa.PCM_PLAYBACK, mode=aa.PCM_NORMAL, card='plughw:%d,0'%cardidx)
        self.pcm.setchannels(self.params['n_ao_channels'])
        self.pcm.setrate(self.params['ao_freq'])
        self.pcm.setperiodsize(self.periodsize)
        self.pcm.setformat(aa.PCM_FORMAT_S16_LE)
        self.dtype_out = np.dtype(np.int16)
        self.ttl_height_rel = 1
        try:
            mixer = aa.Mixer(control='DAC', cardindex = cardidx)
        except:
            pass
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
        self.pcm_type = 'alsa'
        pass
    def connect_to_comedi(self,cardidx=None):
        if self.pcm is not None:
            pass
        self.pcm = ComediWriter(dfname = '/dev/comedi0',n_ao_channels = self.params['n_ao_channels'],rate=self.params['ao_freq'],chunk_size=self.periodsize)
        self.pcm_type = 'comedi'
        self.dtype_out = np.dtype(self.pcm.ao_dtype)
        self.ttl_height_rel = 0.5
        pass

    def ao_write_complete(self):
        if self.pcm_type=='comedi':
            chunk_size_bytes = self.periodsize*self.params['n_ao_channels']*self.dtype_out.itemsize
            if self.pcm.ao_subdevice.get_buffer_contents() > chunk_size_bytes:
                return False
            else:
                return True
        else: 
            return True


def load_rc_file(fname, stimuli_dir=None):
    params = dict(default_params)
    stimset = {}
    stimset['stims'] = []
    with open(fname) as rcfid:
        for line in rcfid:
            params, stimset = parse_rc_line(line, params, stimset,stimuli_dir=stimuli_dir) # returned for transparency
    return params, stimset

def parse_rc_line(line, params, stimset,stimuli_dir=None):
    if len(line.strip('\n'))>0:
        parts = line.strip('\n').split(' ')
        parts = [part for part in parts if len(parts)>0]
        if parts[0].lower() == 'stim':
            if len(parts) > 2 and parts[1] == 'add':
                    stim = parse_stim(params, parts[2:])
                    verify_stim(params,stim)
                    stimset['stims'].append(stim)
                    stimset['stims'][len(stimset['stims'])-1]['stim_idx'] = len(stimset['stims'])-1
        elif parts[0].lower() == "set":
            if len(parts)>2:
                params[parts[1]] = int(parts[2]) ###### make this parse different formats 
    return params, stimset # for transparency

def parse_stim(params,parts):
    stim = {}
    stim['n_ttlchs'] = 0
    stim['n_aochs'] = 0
    stim['aochs'] = []
    stim['ttlchs']= []
    stim_name_parts=[]
    for k,part in enumerate(parts):
        if 'ttl-' in part:
            ch={}
            fname = part.part.strip('ttl-')
            name = os.path.basename(fname)
            head,tail = os.path.split(os.path.dirname(fname))
            stimset = tail
            if check_if_fname_exists(fname) is not False:
                ch['fname']=check_if_fname_exists(fname)
                ch['type']='file-ttl'
                ch['command']=None
                ch['fname']=fname
                ch['stimset']=stimset
                ch['name']=name

            else: # see if kranky should generate this
                if 'kranky:' in fname:
                    ch['type']='kranky-ttl'
                    ch['command']=fname.strip('kranky')
                    ch['fname']=None
                    ch['stimset']='kranky'
                    ch['name']=name
                else:
                    raise Exception('Error in ''stim add'' command format for part:\n %s' % (part))
            stim['ttlchs'].append(ch)
            stim['n_ttlchs']+=1
            stim_name_parts.append('ttl:%s/%s' % (ch['stimset'], ch['name']))
        else: # otherwise its an analog channel. always double chcek your channels before she blows
            ch={}
            ch['type']='ao'
            fname = part.strip('ao-')
            name = os.path.basename(fname)
            head,tail = os.path.split(os.path.dirname(fname))
            stimset = tail
            if check_if_fname_exists(fname,stimset,name,stimuli_dir) is not False:
                ch['fname']=check_if_fname_exists(fname,stimset,name,stimuli_dir)
                ch['command']=None
                ch['stimset']=stimset
                ch['name']=name
                ch['type']='file-ao'
            else:
                raise Exception('Error in ''stim add'' command format for part:\n %s' % (part))
            stim['aochs'].append(ch)
            stim['n_aochs']+=1
            stim_name_parts.append('ao:%s/%s' % (ch['stimset'], ch['name']))
            pass
    stim['name'] = '-'.join(stim_name_parts)
    verify_stim(params,stim)
    return stim

def check_if_fname_exists(fname,stimset,name,stimuli_dir):
    # if can't find the file, try looking in the "stim" directory
    if not os.path.exists(fname) and stimuli_dir is not None:
        working_one = os.path.join(stimuli_dir, stimset, name)
    else:
        working_one = fname
    return working_one

def verify_stim(params, stim):
    stim=stim.copy()
    load_stim(params, stim)
    pass

def load_stim(params, stim):
    nsamples_max = 0

    for k,ttlch in enumerate(stim['ttlchs']):
        if ttlch['type']=='file-ttl':
            wf=load_wf(params,ttlch['fname'])
        elif ttlch['type']=='kranky-ttl':
            raise Exception('kranky generation not yet supported.  check back soon says the duck')
        else:
            raise Exception('Bad ch type ttl %d: %s' % (k,ttlch['type']))

        nsamples_max = np.max((nsamples_max,len(wf)))
        stim['ttlchs'][k]['wf'] = wf
        stim['ttlchs'][k]['nsamples']=len(wf)
    for k,aoch in enumerate(stim['aochs']):
        if aoch['type']=='file-ao':
            wf=load_wf(params,aoch['fname'])
        else:
            raise Exception('Bad ch type ao %d: %s' % (k,aoch['type']))
        nsamples_max = np.max((nsamples_max,len(wf)))
        stim['aochs'][k]['wf'] = wf
        stim['aochs'][k]['nsamples']=len(wf)
    stim['nsamples_max']=nsamples_max
    return stim

def load_wf(params, fname):

    if fname[-4:] == '.raw':
        fid = open(fname,'r')
        dt = np.dtype('int16').newbyteorder('>')
        wf = np.fromfile(fid, dtype = dt)
        fid.close()

    elif fname[-4:] == '.wav':
        wfid = wave.open(fname,'r')
        # wlen = wave.getnframes()
        wf = np.array(wfid.readframes(-1))
        if wfid.getsampwidth() == 2:
            # import ipdb; ipdb.set_trace()
            wf = np.fromstring(str(wf), dtype=np.int16)
        elif wfid.getsampwidth() == 4:
            wf = np.fromstring(str(wf), dtype=np.int32)
        else:
            error('bytesize not supported')
        if wfid.getframerate() != params['ao_freq']:
            raise(Exception('Frame rate of file %s does not match ao_rate\n ao_rate=%d\n file rate=%d' % (fname, params['ao_freq'],wfid.getframerate())))
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

    return wf, high_onsets, low_onsets


def type_info(dtype):
    if dtype in [np.int, np.int0, np.int8, np.int16, np.int32, np.int64]:
        issigned = True
        maxvalue = 2**(8*dtype.itemsize-1)-1
        zerovalue = 0
    else:
        issigned = False
        maxvalue = 2**(8*dtype.itemsize)-1
        zerovalue = 2**(8*dtype.itemsize) / 2
    return issigned, zerovalue, maxvalue


def condition_wf(wf, dtype_out):
    issigned, zerovalue, maxvalue = type_info(dtype_out)
    if issigned:
        wf_out = wf.astype(dtype_out)
    else:
        wf_out = wf.astype(np.int64)
        wf_out = (wf_out + zerovalue).astype(dtype_out)
    return wf_out

def condition_ttl(wf, dtype_out, ttl_height_rel):
    issigned, zerovalue, maxvalue = type_info(dtype_out)
    ttl_value = zerovalue+(maxvalue-zerovalue)*ttl_height_rel
    if issigned:
        wf_out=np.zeros(wf.shape,dtype_out)
        wf_out[wf!=0]=ttl_value
    else:
        wf_out=(np.ones(wf.shape)*zerovalue).astype(dtype_out)
        wf_out[wf!=0]=ttl_value
    return wf_out

def load_trial_data(pbc,trial,ktrial, record_control_trial = False, record_control_trial_length = 1, record_control_pulse_length=10e-3):
    if trial is None:
        trial = {}
    else:
        trial=trial.copy()
    if ktrial is None:
        ktrial = -1
    if 'stim' in trial.keys():
        stim=trial['stim']
        stim = load_stim(pbc.params, stim)
        # load the ao and ttl channel wfs into nump mats
        aowfs = np.zeros((stim['n_aochs'],stim['nsamples_max']))
        ttlwfs = np.zeros((stim['n_ttlchs'],stim['nsamples_max']))
        for k,ttlch in enumerate(stim['ttlchs']):
            ttlwfs[k,0:ttlch['nsamples']] = ttlch['wf']
        for k,aoch in enumerate(stim['aochs']):
            aowfs[k,0:aoch['nsamples']]=condition_wf(aoch['wf'], pbc.dtype_out)
        nsamples = stim['nsamples_max']
        trigger0_wf, hio, lowo = generate_trigger(pbc.params, nsamples, trial_idx = ktrial)
        record_control_wf = np.zeros((1,nsamples))
    elif record_control_trial: # generate record control wf
        nsamples = record_control_trial_length * pbc.params['ao_freq']
        idx0 = 0
        idx1 = int(round(float(record_control_pulse_length)*pbc.params['ao_freq'])+idx0)
        record_control_wf = np.zeros((nsamples))
        record_control_wf[idx0:idx1]=1
    else:
        raise Exception('No Trial info given')


    # generate output data
    data=condition_wf(np.zeros((pbc.params['n_ao_channels'],nsamples),pbc.dtype_out), pbc.dtype_out)
    ao_is_used=np.zeros(pbc.params['n_ao_channels'], np.bool)
    
    # add record control as analog-ttl
    if pbc.params['record_control_channel']>=0: # if record control is an ao channel, saet it
        if ao_is_used[pbc.params['record_control_channel']]:
            raise Exception('Error: Record channel set to %d but it has already been assigned' % (pbc.params['record_control_channel']))
        data[pbc.params['record_control_channel'],:] = condition_ttl(record_control_wf, pbc.dtype_out, pbc.ttl_height_rel)

    # add trigger channel as analog-ttl
    if not record_control_trial and pbc.params['trigger_channel']>=0: # if trigger channel is an ao channel
        if ao_is_used[pbc.params['trigger_channel']]:
            raise Exception('Error: Trigger channel set to %d but it has already been assigned' % (pbc.params['trigger_channel']))
        data[pbc.params['trigger_channel'],:]= condition_ttl(trigger0_wf, pbc.dtype_out, pbc.ttl_height_rel)
        ao_is_used[pbc.params['trigger_channel']]=True
    
    ## now add analog wfs
    if not record_control_trial:
        if any(ao_is_used[0:len(stim['aochs'])]):
            raise Exception('Error trial %d: ao channel(s) have already been assigned' % (ktrial))
        else:
            data[0:len(stim['aochs']),:]=aowfs
            ao_is_used[0:len(stim['aochs'])]= True

    ## now if do_aad then calculate the aad_wf from the do_channels
    if pbc.params['do_aad']: 
        aad_dos = np.zeros((4,nsamples), np.bool)
        aad_is_used = np.zeros(4, np.bool)

        # if record control is aad then add it to aad_dos
        if pbc.params['record_control_channel']<0: # if record control is an ao channel, saet it
            if aad_is_used[-pbc.params['record_control_channel']]:
                raise Exception('Error: Record channel set to aad ch %d but it has already been assigned' % (pbc.params['trigger_channel']))
            aad_dos[-pbc.params['record_control_channel'],:] = record_control_wf.astype(np.bool)
            aad_is_used[-pbc.params['record_control_channel']]=True
        # add trigger channel as analog-ttl
        if not record_control_trial and pbc.params['trigger_channel']<0: # if trigger channel is an ao channel
            if aad_is_used[-pbc.params['trigger_channel']]:
                raise Exception('Error: Trigger channel set to aad ch %d but it has already been assigned' % (pbc.params['trigger_channel']))
            aad_dos[-pbc.params['trigger_channel'],:]= trigger0_wf.astype(np.bool)
            aad_is_used[pbc.params['trigger_channel']]=True
        # add all stimulus ttlwfs to aad_dos
        if not record_control_trial:
            aad_dos[0:stim['n_ttlchs']]=ttlwfs.astype(np.bool)
        # generate aad wf from aad_dos
        aad_dos = np.vstack((aad_dos, np.zeros((4,nsamples),np.bool)))
        aad_ba = bitarray(np.reshape(aad_dos, (np.prod(aad_dos.shape)), order='F').tolist(), endian='little')
        aad_wf = np.fromstring(aad_ba.tostring(),np.uint8).astype(pbc.dtype_out)
        # add aad wf to analog out data
        if ao_is_used[pbc.params['aad_channel']]:
            raise Exception('Error: Add channel set to %d but it has already been assigned' % (pbc.params['aad_channel']))
        # import ipdb; ipdb.set_trace()
        data[pbc.params['aad_channel'],:]=aad_wf*aad_factor + aad_offset
        # import ipdb; ipdb.set_trace()
        ao_is_used[pbc.params['aad_channel']]=True
        pass
    else: ## otherwise add the digital channels as analog_digital channels
        if not record_control_trial:
            ao_ttl_ch_idxs = range(stim['n_aochs'], stim['n_ttlchs'])
            if any(ao_is_used[ao_ttl_ch_idxs]):
                raise Exception('Error trial %d: ttl channel(s) have already been assigned' % (ktrial))
            data[ao_ttl_ch_idxs,:]=condition_ttl(ttlwfs, pbc.dtype_out, pbc.ttl_height_rel)
    trial['data']=data
    trial['ktrial']=ktrial
    return trial

# def load_intro_data(pbc, intro_length=1, intro_pulse_length=10e-3):
#     data = np.zeros((pbc.pbc['n_ao_channels'],pbc.params['ao_freq']*intro_length))
#     idx0 = 1;
#     idx1 = round(float(intro_pulse_length)*pbc.params['ao_freq'])+idx0
#     data[2,idx0:idx1]=1
#     data = condition_ttl(data,pbc.dtype_out, pbc.ttl_height_rel)
#     return data
# def load_end_data(pbc, end_length=1,end_pulse_length=10e-3):
#     data = np.zeros((4,pbc.params['ao_freq']*end_length))
#     # data[3,:] =-1*scale_factor
#     idx0=1
#     idx1 = data.shape[1]-float(end_pulse_length)*pbc.params['ao_freq']
#     data[2,idx0:idx1]=1
#     data=condition_ttl(data,pbc.dtype_out,pbc.ttl_height_rel)
#     # import ipdb; ipdb.set_trace()
#     return data


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
    owfid.setnchannels(params['n_ao_channels'])
    owfid.setframerate(params['ao_freq'])
    owfid.setsampwidth(nbytes)
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
    trial = load_trial_data(pbc, {},-1,record_control_trial=True)
    pbc.trial_queue.put(trial)
    playflag = True
    # loop thru trials, adding to que
    for ktrial, trial in enumerate(playback_plan['trials']):
        if not runflag:
            return
        # print "generating trial: %d" % ktrial
        trial = load_trial_data(pbc, trial, ktrial)
        pbc.trial_queue.put(trial)
    # add ending
    trial = load_trial_data(pbc, {}, -1,record_control_trial=True)
    pbc.trial_queue.put(trial)
    # add stop sig
    pbc.trial_queue.put("STOP")
    pass

def data_loader(pbc):
    chunk_length = pbc.periodsize*pbc.params['n_ao_channels']
    chunk_length_bytes = chunk_length*pbc.dtype_out.itemsize
    buff = FifoFileBuffer()
    nsafeframes = int(float(pbc.params['ao_freq'])/pbc.periodsize)
    global runflag, playflag
    while not playflag:
        pass

    # add some chunks to start
    buff.write(condition_ttl(np.zeros((1,chunk_length*nsafeframes)),pbc.dtype_out,pbc.ttl_height_rel).tostring())

    trial_count = 0
    chunk_count = 0
    sample_count = 0
    trials_done = False
    while runflag:
        if buff.available <= chunk_length_bytes:
            if pbc.trial_queue.qsize() > 0:
                trial = pbc.trial_queue.get()
                if trial is not "STOP":
                    trial_count += 1
                    trial_data = np.reshape(trial['data'],(1,np.prod(trial['data'].shape)),order='F')
                    buff.write(trial_data.tostring())
                    if trial['ktrial']>=0 and 'stim' in trial.keys():
                        print "Trial %d:  %s" % (trial['ktrial'], trial['stim']['name'])
                        pbc.message_queue.put('trial[%d]: stim_index=%d; ao_range=[%d, %d]\n' % (trial['ktrial'], trial['stim']['stim_idx'], sample_count, sample_count+trial['data'].shape[1]))
                    elif trial['ktrial']==-1:
                        print "Sending Record Control Signal"
                    sample_count += trial['data'].shape[1]

                    
                else: # exit:  dump rest of data and pass along stop message
                    trials_done = True
                    buff.write(condition_ttl(np.zeros((1,chunk_length*nsafeframes)),pbc.dtype_out,pbc.ttl_height_rel).tostring())
                    # buff.write(condition_wf(1000*np.random.randn(1,chunk_length*nsafeframes*1),pbc.dtype_out).tostring())
                # import ipdb; ipdb.set_trace()
        if buff.available >= chunk_length_bytes:
            # import ipdb; ipdb.set_trace()
            pbc.data_queue.put(buff.read(size=chunk_length_bytes))
            chunk_count += 1
        elif trials_done and (buff.available < chunk_length_bytes):
            pbc.data_queue.put(buff.read())
            break
            # print "loading chunk %d" % chunk_count
    pbc.data_queue.put("STOP")
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
            while not pbc.ao_write_complete():
                pass    
            print 'ao complete after %d chunks' % count
            runflag=False
    pass


def write_rec_header(recfid, params, stimset):
    recfid.write('format: "kranky 20150622"\n')
    recfid.write('date: "%s"\n' % str(datetime.datetime.now()))
    for key in params.keys():
        recfid.write('%s: %s\n' % (key, str(params[key])))
    for stim in stimset['stims']:
        recfid.write('stim[%d]: file="%s";\n' % (stim['stim_idx'], stim['name']))

def find_data_location(data_path_root, DIR_PRE):
    DIR_NOW = os.listdir(data_path_root)
    unique = list(set(DIR_NOW)-set(DIR_PRE))
    if len(unique) > 0:
         return data_path_root + unique[0]
    else:
        return None


def empty_que(que):
    while que.qsize() > 0:
        try:
            que.get(False)
        except:
            pass
    pass

def run_playback(cardidx, params, stimset, playback_plan, data_path_root="/home/jknowles/science_code/GUI/Builds/Linux/build/", require_data = True):
    global runflag, playflag

    pbc = PlaybackController(params)
    if len(cardidx)<2:
        cardidx=int(cardidx)
        pbc.connect_to_pcm(cardidx)
    else:
        pbc.connect_to_comedi()
    # import ipdb; ipdb.set_trace()

    # get dir list
    if require_data:
        DIR_PRE = os.listdir(data_path_root)

    #start threads going
    runflag = True
    playflag = False
    t_tl = threading.Thread(target=trial_loader, args=(pbc, playback_plan))
    t_tl.start()
    t_dl = threading.Thread(target=data_loader, args=(pbc,))
    t_dl.start()
    t_ao = threading.Thread(target=ao_thread, args=(pbc,))
    t_ao.start()
    threads = [t_tl, t_dl, t_ao]
    curtime = datetime.datetime.now()
    try:
        # save recording
        if require_data: # if ephys data are required, look for new data in data_path_root/
            data_path = None
            while runflag: # initially look for data directory
                data_path=find_data_location(data_path_root, DIR_PRE)
                if data_path is not None:
                    # now we have the dir, open new .rec.paf file and write params
                    rec_file_name = data_path + os.path.sep + "presentation_%d-%d-%d_%d-%d-%d.pbrec" % (curtime.year, curtime.month, curtime.day, curtime.hour,curtime.minute,curtime.second)
                    print "Found Corresponding data: %s" % data_path
                    break
                if pbc.message_queue.qsize() > 4 and require_data:
                    raise Exception("AI Data Not Found! Is Ephys Running?")
        else: 
            rec_file_name = data_path_root + os.path.sep + "presentation_%d-%d-%d_%d-%d-%d.pbrec" % (curtime.year, curtime.month, curtime.day, curtime.hour,curtime.minute,curtime.second)
        print "Saving Rec File to: %s" % rec_file_name
        recfid = open(rec_file_name,'w')
        write_rec_header(recfid, pbc.params, stimset)
        # Now if data recfile is g2g start main loop
        while runflag:
            # write messages to recfile as they exist
            if pbc.message_queue.qsize() > 0:
                message = pbc.message_queue.get(False)
                recfid.write(message)
                recfid.flush()
            pass
    except KeyboardInterrupt as e:
        print "You stopped me with a KeyboardInterrupt. Don't forget to stop the recording if it's going!"
    except Exception as e:
        traceback.print_exc()
        raise e
    finally:
        runflag = False
        playflag = False
        try:
            empty_que(pbc.trial_queue)
            pbc.trial_queue.put("STOP", block = False)
            pbc.trial_queue.mutex.release_lock()
        except:
            pass
        try:
            empty_que(pbc.data_queue)
            pbc.data_queue.put("STOP", block = False)
            pbc.data_queue.mutex.release_lock()
        except:
            pass
        try:
            pbc.message_queue.mutex.release_lock()
            pass
        except:
            pass
        for thread in threads:
            try:
                thread.join()
            except:
                pass

    pass



if __name__=="__main__":
    # set overall default commands
    default_params = {}
    default_params['ao_freq'] = 40000
    default_params['n_trials'] = 100
    default_params['stim_order'] = 2
    default_params['wav']=False
    default_params['require_data']=True
    default_params['cardidx']='comedi'
    default_params['do_aad']=False
    default_params['aad_channel']=None
    default_params['record_control_channel']= 2
    default_params['trigger_channel']=3
    default_params['n_ao_channels'] = 4
    default_params['data_dir'] = os.getcwd()
    default_params['stim_dir'] = '/home/jknowles/data/doupe_lab/stimuli/'
    parser=argparse.ArgumentParser(prog='kranky')
    parser.description = 'Stimuluis Presenter for Neuroscience Experiments. Jeff Knowles, 2015; jeff.knowles@gmail.com'
    parser.epilog =  'Note: All optional arguments may also be entered into the rc file, with _ replacing - (eg data_dir instead of --data-dir)'
    ## arguments
    parser.add_argument('rc_fname')
    parser.add_argument('-c', '--cardidx',help='alsa card number', type = str)
    parser.add_argument('-n','--n-trials',help='number of trials to run', type=int)
    parser.add_argument('-r','--require-data', type=int,help='require that new data be found in data dur to continue')
    parser.add_argument('-d','--data-dir',type=str,help='directory to look for data dir from data capture software')
    parser.add_argument('-s','--stim-dir',type=str,help='directory containing stim-sets.  If the exact directory passed in the rc file isnt found, kranky looks for the stimset here.')
    parser.add_argument('-o','--stim-order',type=int,help='How to order the stimuli. 0=in the order provided 2=randomly interleaved')
    parser.add_argument('--trigger-channel',type=int, help='Channel for timing trigger signal. If ch > 0, the signal is routed through analog output on the channel provided.  If trigger_channel < 0, the trigger is produced on an aad-ch, encoded on the aad output channel')
    parser.add_argument('--record-control-channel',type=int,help='Channel for recording control signal. If ch > 0, the signal is routed through analog output on the channel provided.')
    parser.add_argument('--do-aad', type = int,help='Specify whether to route channels through aad (analog->analog->digital.  If do_aad is false, then all negative channel numbers are ignored')
    parser.add_argument('--aad-channel',type=int, help='Channel for aad (analog->analog->digital) output. Four ttl channels are encoded in one analog channel. If ch > 0, the signal is routed through analog output on the channel provided.  If trigger_channel < 0, the trigger is produced on an aad-ch, encoded on the aad output channel')
    parser.add_argument('--ao-freq',type=int)
    parser.add_argument('--n-ao-channels',type=int)
    parser.add_argument('--wav',help='write a .wav file instead of doing playback')


    args = vars(parser.parse_args())
    rc_fname = args['rc_fname']
    if args['stim_dir'] is not None:
        stimuli_dir = args['stim_dir']
    else:
        stimuli_dir = default_params['stim_dir']
    # get params and stimset from rc
    params, stimset = load_rc_file(rc_fname, stimuli_dir=stimuli_dir)
    # override defaults with params
    paramsout = default_params
    for param in params.keys():
        paramsout[param]=params[param]
    params=paramsout
    # override  params with args
    for arg in args.keys():
        if args[arg] is not None:
            params[arg]=args[arg]
    if 'ai_freq' in params.keys():
        params.pop('ai_freq')
    for stim in stimset['stims']:
        verify_stim(params, stim)

    # print params
    for key in params.keys():
        print '%s: %s' % (key, str(params[key]))
    if False:
        for stim in stimset['stims']:
            print 'stim[%d]: file="%s";' % (stim['stim_idx'], stim['fname'])
    playback_plan=generate_playback_plan(params,stimset)
    if params['wav']:
        write_playback_audio_file(params, stimset, playback_plan, 'test.wav')
    else:
        run_playback(params['cardidx'], params, stimset, playback_plan, require_data = params['require_data'], data_path_root=params['data_dir'])
