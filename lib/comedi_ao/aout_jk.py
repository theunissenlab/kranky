#!/usr/bin/env python
#
# Copyright (C) 2012 W. Trevor King <wking@tremily.us>
#
# This file is part of pycomedi.
#
# pycomedi is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 2 of the License, or (at your option) any later
# version.
#
# pycomedi is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# pycomedi.  If not, see <http://www.gnu.org/licenses/>.

"""Output a series of data files using an analog output Comedi subdevice.
"""

import os.path as _os_path

import numpy as _numpy
# from scipy.io import wavfile as _wavfile
try:
    import pycomedi.constant
except:
    pass
from pycomedi.device import Device as _Device
from pycomedi.subdevice import StreamingSubdevice as _StreamingSubdevice
from pycomedi.channel import AnalogChannel as _AnalogChannel
from pycomedi import constant as _constant
from pycomedi import utility as _utility


NUMPY_FREQ = 5e5
LOADER = {  # frequency,raw_signal = LOADER[extension](filename)
    '.npy': lambda filename: (NUMPY_FREQ, _numpy.load(filename)),
    '.wav':None,
    }


def setup_device(filename, subdevice, channels, range, aref):
    """Open the Comedi device at filename and setup analog output channels.
    """
    device = _Device(filename=filename)
    device.open()
    if subdevice is None:
        ao_subdevice = device.find_subdevice_by_type(
            _constant.SUBDEVICE_TYPE.ao, factory=_StreamingSubdevice)
    else:
        ao_subdevice = device.subdevice(subdevice, factory=_StreamingSubdevice)
    ao_channels = [
        ao_subdevice.channel(i, factory=_AnalogChannel, range=range, aref=aref)
        for i in channels]
    return (device, ao_subdevice, ao_channels)

def load(filename):
    """Load a date file and return (frequency, unit_output_signal)

    Values in unit_output_signal are scaled to the range [-1,1].
    """
    root,ext = _os_path.splitext(filename)
    loader = LOADER[ext]
    frequency,raw_signal = loader(filename)
    iinfo = _numpy.iinfo(raw_signal.dtype)
    raw_signal_midpoint = (iinfo.max + iinfo.min)/2.
    raw_signal_range = iinfo.max - raw_signal_midpoint
    unit_output_signal = (raw_signal - raw_signal_midpoint)/raw_signal_range
    return (frequency, unit_output_signal)

def generate_output_buffer(ao_subdevice, ao_channels, output_signal):
    """Setup an output buffer from unit_output_signal

    The output signal in bits is scaled so that -1 in
    unit_output_signal maps to the minimum output voltage for each
    channel, and +1 in unit_output_signal maps to the maximum output
    voltage for each channel.
    """
    ao_dtype = ao_subdevice.get_dtype()
    n_samps,n_chans = output_signal.shape
    assert n_chans <= len(ao_channels), (
            'need at least {0} channels but have only {1}'.format(
                n_chans, ao_channels))
    ao_buffer = _numpy.zeros((n_samps, n_chans), dtype=ao_dtype)
    for i in range(n_chans):
        range_ = ao_channels[i].range
        midpoint = (range_.max + range_.min)/2
        v_amp = range_.max - midpoint
        v_amp = 1.0
        converter = ao_channels[i].get_converter()
        unit_output_signal=output_signal[:,i]
        unit_output_signal = _numpy.divide(unit_output_signal.astype('float64'),_numpy.max(unit_output_signal))
        volt_output_signal = unit_output_signal*v_amp + midpoint
        # volt_output_signal[:] = 0
        # ao_buffer[:,i] = converter.from_physical(volt_output_signal)
        zero = (2**16)/2
        unit = int(round(float(2**16)/(2*v_amp)))
        # ao_buffer[:,i]=(volt_output_signal*unit+zero).astype(ao_dtype)
        ao_buffer[:,i]= converter.from_physical(volt_output_signal)

        # for k in range(volt_output_signal.shape[0]):
        #     print converter.from_physical(volt_output_signal[k])
        #     ao_buffer[k,i]=converter.from_physical(volt_output_signal[k])
    # from matplotlib import pyplot as plt
    # import ipdb; ipdb.set_trace()
    return ao_buffer

def setup_command(ao_subdevice, ao_channels, frequency, output_buffer):
    """Setup ao_subdevice.cmd to output output_buffer using ao_channels
    """
    scan_period_ns = int(1e9 / frequency)
    n_chan = output_buffer.shape[1]
    ao_cmd = ao_subdevice.get_cmd_generic_timed(n_chan, scan_period_ns)
    ao_cmd.start_src = _constant.TRIG_SRC.int
    ao_cmd.start_arg = 0
    ao_cmd.stop_src = _constant.TRIG_SRC.none
    ao_cmd.stop_arg = 0
    # ao_cmd.stop_src = _constant.TRIG_SRC.count
    # ao_cmd.stop_arg = len(output_buffer)
    ao_cmd.chanlist = ao_channels[:n_chan]
    import ipdb; ipdb.set_trace()
    ao_subdevice.cmd = ao_cmd

def run_command(device, ao_subdevice, output_buffer):
    """Write output_buffer using ao_subdevice

    Blocks until the output is complete.
    """
    ao_subdevice.command()
    writer = _utility.Writer(
        ao_subdevice, output_buffer,
        preload=ao_subdevice.get_buffer_size()/output_buffer.itemsize,
        block_while_running=False)
    import ipdb; ipdb.set_trace()
    writer.start()
    device.do_insn(_utility.inttrig_insn(ao_subdevice))
    import ipdb; ipdb.set_trace()
    writer.join()

def run(filename, subdevice, channels, range, aref, mmap=False, files=[]):

    import os
    import tempfile
    from numpy import arange, iinfo, int16, pi, save, sin, zeros

    # Create temporary files for testing.
    p = 5
    time = arange(p*NUMPY_FREQ, dtype=float)/NUMPY_FREQ
    f = 1e3
    iint16 = iinfo(int16)
    a = (iint16.max - iint16.min)/2.
    one_chan = zeros(time.shape, dtype=int16)
    one_chan[:] = a*sin(2*pi*f*time)
    # fd,one_chan_path = tempfile.mkstemp(prefix='pycomedi-', suffix='.npy')
    # fp = os.fdopen(fd, 'w')
    # >>> save(fp, one_chan)
    # >>> fp.close()

    # two_chan = zeros((NUMPY_FREQ,2), dtype=int16)
    # two_chan[:,0] = a*sin(f*time/(2*pi))
    # two_chan[:,1] = a*sin(2*f*time/(2*pi))
    # datadict = {'one_chan': one_chan, 'two_chan': two_chan}
    datadict = {'one_chan': one_chan}
    # >>> fd,two_chan_path = tempfile.mkstemp(prefix='pycomedi-', suffix='.npy')
    # >>> fp = os.fdopen(fd, 'w')
    # >>> save(fp, two_chan)
    # >>> fp.close()

    # >>> run(filename='/dev/comedi0', subdevice=None,
    # ...     channels=[0,1], range=0, aref=_constant.AREF.ground,
    # ...     files=[one_chan_path, two_chan_path])

    # >>> os.remove(one_chan_path)
    # >>> os.remove(two_chan_path)
    
    device,ao_subdevice,ao_channels = setup_device(
        filename=filename, subdevice=subdevice, channels=channels,
        range=range, aref=aref)

    for filename in datadict:
        unit_output_signal=datadict[filename]
        frequency = NUMPY_FREQ
        # frequency,unit_output_signal = load(filename=filename)
        if len(unit_output_signal.shape) == 1:
            unit_output_signal.shape = (unit_output_signal.shape[0], 1)
        output_buffer = generate_output_buffer(
            ao_subdevice, ao_channels, unit_output_signal)
        setup_command(ao_subdevice, ao_channels, frequency, output_buffer)
        run_command(device, ao_subdevice, output_buffer)
    device.close()


if __name__ == '__main__':
    import pycomedi_demo_args
# 
    # pycomedi_demo_args.ARGUMENTS['files'] = (['files'], {'nargs': '+'})
    # args = pycomedi_demo_args.parse_args(
        # description=__doc__,
        # argnames=[
            # 'filename', 'subdevice', 'channels', 'range', 'aref', 'mmap',
            # 'files', 'verbose'])

    run(filename='/dev/comedi0', subdevice=1,
        channels=[0, 1], range=0, aref=_constant.AREF.ground,
        mmap=False)
    # import time
    # time.sleep(5)
