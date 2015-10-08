import os
import wave
from multiprocessing import Process, Value
import subprocess
import numpy as np
if os.uname()[0]=='Linux': # this allows for development on non-linux systems 
	import alsaaudio as aa
else:
	pass

# find mixer name
for control_name in ['PCM', 'Speaker','Master']:
	try:
		mixer = aa.Mixer(control=control_name, cardindex = cardidx)
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
	

#functions
def playwf(stopsig, pcm, trial_data):
	# try:
 #   		mixer.setvolume(100)
	# except:
	# 	pass
	# try:
	# 	mixer.setmute(0)
	# except:
	# 	pass



	data=song.readframes(frame_size)
	while data and stopsig.value==0:
			if pulse:
				# x = np.fromstring(data, np.int16)
				# x = np.expand_bebbdims(x,axis=1)
				# x = np.concatenate((x, 0*np.ones(x.shape)), axis = 1)
				# data = x.flatten().tostring()
				pcm.write(data)
				
				# data = np.concatinate(np.array(data), np.one
			else:
				pcm.write(data)
			data=song.readframes(frame_size)
	elif filetype == '.sng':
		fid= open(filename, 'r')
		nchannels=1
		pcm.setformat(aa.PCM_FORMAT_S32_LE)
		pcm.setchannels(nchannels)
		pcm.setrate(rate)
		pcm.setperiodsize(frame_size)
		data = np.fromfile(fid, dtype = np.dtype('d'), count = frame_size)
		while len(data) > 0 and stopsig.value==0:
			if len(data) < frame_size:
				data = np.append(data, np.zeros((frame_size-len(data), 1)))
			data = np.array(data*2**15, dtype = np.dtype('i4'))
			pcm.write(data.tostring())
			data = np.fromfile(fid, dtype = np.dtype('d'), count = frame_size)
	pcm.close()
	stopsig.value = 1
	pass

def sendwf(cardidx, wavefile, filetype, rate, pulse = False, pulse_type = "high"):
	stopsig = Value('i', 0)
	kwargs = {'pulse': pulse, 'pulse_type': pulse_type}
	p=Process(target = playwf, args = (stopsig, cardidx, wavefile, filetype, rate), kwargs = kwargs)
	p.start()
	return (p, stopsig)

def beep(a=.05, b=500):
	command = 'play --no-show-progress --null --channels 1 synth %s sine %f' % ( a, b)
	# print command
	subprocess.Popen([command], stdout=subprocess.PIPE, shell = True)
	#os.popen('play --no-show-progress --null --channels 1 synth %s sine %f' % ( a, b))
	# sendwf(0, '/sounds/beep.wav', '.wav, 44100)
	pass

def list_sound_cards():
	if os.uname()[0]=='Linux':
		return aa.cards()
	else:
		return ['iLuv_1']

if __name__=="__main__":
    import sys
    if len(sys.argv) <= 1:
        raise(Exception('no args passed'))
    else:
    	cardidx = int(sys.argv[1])
        spath = sys.argv[2]
    sendwf(cardidx, spath, '.wav',44100,pulse = False)
	# # song1 = wave.open('/home/jknowles/test.wav')
	# # song2 = wave.open('/home/jknowles/test1ch.wav')
	# # import ipdb; ipdb.set_trace()

	# sendwf(1, '/home/jknowles/data/doupe_lab/stimuli/boc_syl_discrim_v1_stimset_a/song_a_1.wav','.wav',44100, pulse = False)
	# # playwf(1, '/home/jknowles/test.wav','.wav',44100, pulse = True)
	# # playwf(1, '/home/jknowles/test1ch.wav','.wav',44100, pulse = True)
	

