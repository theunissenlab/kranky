import sys as _sys
import time as _time

# try:
#     from matplotlib import pyplot as _pyplot
#     from matplotlib.lines import Line2D as _Line2D
#     #from matplotlib.animation import FuncAnimation as _FuncAnimation
# except (ImportError, RuntimeError) as e:
#     _pyplot = None
#     _matplotlib_import_error = e
import numpy as np
import time
# from pycomedi import LOG as _LOG
import pycomedi.constant as _constant
from pycomedi.device import Device as _Device
from pycomedi.subdevice import StreamingSubdevice as _StreamingSubdevice
from pycomedi.channel import AnalogChannel as _AnalogChannel
from pycomedi.channel import DigitalChannel as _DigitalChannel
from pycomedi.chanspec import ChanSpec as _ChanSpec
import pycomedi.utility as _utility


def open_ao_channels(device, subdevice, channels, _range, aref):
    """Subdevice index and list of channel indexes
    to ``Subdevice`` instance and list of ``AnalogChannel`` instances
    """
    if subdevice >= 0:
        subdevice = device.subdevice(subdevice, factory=_StreamingSubdevice)
    else:
        subdevice = device.find_subdevice_by_type(
            _constant.SUBDEVICE_TYPE.ao, factory=_StreamingSubdevice)
    channels = [subdevice.channel(
            index=i, factory=_AnalogChannel, range=_range, aref=aref)
                for i in channels]
    return(subdevice, channels)

def open_do_channels(device, subdevice, channels):
    """Subdevice index and list of channel indexes
    to ``Subdevice`` instance and list of ``AnalogChannel`` instances
    """
    if subdevice >= 0:
        subdevice = device.subdevice(subdevice, factory=_StreamingSubdevice)
    else:
        subdevice = device.find_subdevice_by_type(
            _constant.SUBDEVICE_TYPE.dio, factory=_StreamingSubdevice)
    channels = [subdevice.channel(
            index=i, factory=_DigitalChannel)
                for i in channels]
    return(subdevice, channels)
def prepare_ao_command(subdevice, channels, frequency):
    """Create a periodic sampling command.

    Ask comedilib to create a generic sampling command and then modify
    the parts we want.
    """
    command = subdevice.get_cmd_generic_timed(
        len(channels), scan_period_ns=int(float(1e9)/frequency))
    command.chanlist = channels
    command.stop_src = _constant.TRIG_SRC.none
    command.stop_arg = 0
    return command

def prepare_do_command(subdevice, channels, frequency):
    """Create a periodic sampling command.

    Ask comedilib to create a generic sampling command and then modify
    the parts we want.
    """
    # command = subdevice.get_cmd_src_mask()
    import ipdb; ipdb.set_trace()
    # command.chanlist = channels
    command.stop_src = _constant.TRIG_SRC.none
    command.stop_arg = 0
    return command



class ComediWriter(object):
	def __init__(self,dfname="/dev/comedi0", chunk_size = 4096, n_ao_channels=4, rate = 40000):
		self.device = _Device(filename=dfname)
		self.device.open()
		self.rate = rate
		self.n_ao_channels = n_ao_channels
		self.ao_channel_list = range(n_ao_channels)
		self.chunk_size = chunk_size
		self.is_started = False


		# configure ao subdevice
		ao_subdevice,ao_channels = open_ao_channels(device=self.device, subdevice=None, channels=self.ao_channel_list, _range=0, aref=0)
		self.ao_subdevice=ao_subdevice
		self.ao_channels = ao_channels
		self.ao_subdevice.cmd = prepare_ao_command(subdevice=self.ao_subdevice, channels=self.ao_channels, frequency=self.rate)
		self.ao_dtype = ao_subdevice.get_dtype()
		self.ao_subdevice.command()
		self.ao_converter = self.ao_channels[0].get_converter()
		self.itemsize=np.zeros(1,self.ao_dtype).itemsize
		# # configure do subdevice
		# n_do_channels = len(do_channel_list)
		# do_subdevice,do_channels = open_do_channels(device=device, subdevice=do_subdevice, channels=do_channel_list)
		# import ipdb; ipdb.set_trace()
		# do_subdevice.cmd = prepare_do_command(subdevice=do_subdevice, channels=do_channels, frequency=fs)
		# do_dtype = do_subdevice.get_dtype()
		# import ipdb; ipdb.set_trace()
		# do_subdevice.command()
		self._file = self.ao_subdevice.device.file
		# setup buffers
		ao_preload0 = np.zeros((self.chunk_size*5,self.n_ao_channels))
		ao_preload = np.zeros((ao_preload0.shape), self.ao_dtype)
		for kch in range(n_ao_channels):
			ao_preload[:,kch] = self.ao_converter.from_physical(ao_preload0[:,kch]).astype(self.ao_dtype)
		# import ipdb; ipdb.set_trace()
		# do_buffer = np.zeros(chunk_size*50, do_dtype)
		ao_preload.tofile(self._file)
		# setup writers
		
		# print "%d: bsize %d booffset %d bcontents %d" % (count,do_subdevice.get_buffer_size(), do_subdevice.get_buffer_offset(), do_subdevice.get_buffer_contents())
		# if (do_subdevice.get_buffer_size()-do_subdevice.get_buffer_contents()) > chunk_size * do_buffer.itemsize:
		# 	do_chunk = np.zeros(chunk_size, do_dtype)
		# 	do_chunk.tofile(do_writer._file())
		# import ipdb; ipdb.set_trace()
	def start(self):
		if not self.is_started:
			self.device.do_insn(_utility.inttrig_insn(self.ao_subdevice))
			self.is_started = True
		else:
			raise Exception("playback already started")

	def write_numpy_chunk(self, chunk):
		while not (self.ao_subdevice.get_buffer_size()-self.ao_subdevice.get_buffer_contents()) > np.prod(chunk.shape)*self.itemsize:
			pass
		try:
			chunk.tofile(self._file)
		except Exception as e:
			raise e

	def write_binary_string_chunk(self, chunk):
		while not (self.ao_subdevice.get_buffer_size()-self.ao_subdevice.get_buffer_contents()) > len(chunk):
			pass
		try:
			self._file.write(chunk)
		except Exception as e:
			raise e

	def write(self, chunk):
		if not self.is_started:
			self.start()

		if type(chunk) is np.ndarray:
			self.write_numpy_chunk(chunk)
		elif type(chunk) is str:
			self.write_binary_string_chunk(chunk)
		else:
			raise Exception('Data Type not Recognized')




if __name__=="__main__":
	# import ipdb; ipdb.set_trace()
	writer = ComediWriter(rate=100000)
	count = 0
	amp = 5
	# writer.start()
	ao_chunk_out = np.zeros((writer.chunk_size,writer.n_ao_channels),writer.ao_dtype)
	amp = [5,1,5,1]
	while count < 50000:
		count +=1
		print count
		ao_chunk = np.random.randn(writer.chunk_size,writer.n_ao_channels)
		for kch in range(writer.n_ao_channels):
			ao_chunk_out[:,kch] = writer.ao_converter.from_physical(ao_chunk[:,kch]*amp[kch]).astype(writer.ao_dtype)
			# import ipdb; ipdb.set_trace()
		# ao_chunk_out = np.reshape(ao_chunk_out,(1,np.prod(ao_chunk.shape)),order='F')
		writer.write(ao_chunk_out)
		# writer.write(np.reshape(ao_chunk_out,(1,np.prod(ao_chunk.shape)),order='C').tostring())

