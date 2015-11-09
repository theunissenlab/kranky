function [data] = load_open_ephys_continuous(filename, range)
%
% [data, timestamps, info] = load_open_ephys_data(filename)
%
%   Loads continuous, event, or spike data files into Matlab.
%
%   Inputs:
%
%     filename: path to file
%
%
%   Outputs:
%
%     data: either an array continuous samples (in microvolts),
%           a matrix of spike waveforms (in microvolts),
%           or an array of event channels (integers)
%
%     timestamps: in seconds
%
%     info: structure with header and other information
%
%
%
%   DISCLAIMER:
%
%   Both the Open Ephys data format and this m-file are works in progress.
%   There's no guarantee that they will preserve the integrity of your
%   data. They will both be updated rather frequently, so try to use the
%   most recent version of this file, if possible.
%
%

%
%     ------------------------------------------------------------------
%
%     Copyright (C) 2014 Open Ephys
%
%     ------------------------------------------------------------------
%
%     This program is free software: you can redistribute it and/or modify
%     it under the terms of the GNU General Public License as published by
%     the Free Software Foundation, either version 3 of the License, or
%     (at your option) any later version.
%
%     This program is distributed in the hope that it will be useful,
%     but WITHOUT ANY WARRANTY; without even the implied warranty of
%     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
%     GNU General Public License for more details.
%
%     <http://www.gnu.org/licenses/>.
%
if nargin<2
    range = [];
end

if isstr(filename)
    [~,~,filetype] = fileparts(filename);
    if ~any(strcmp(filetype,{'.continuous'}))
        error('File extension not ''.continuous''.');
    end
    fid = fopen(filename);
    just_opened = true;
else
    fid = filename;
    just_opened=false;
    
end

% get header info
fseek(fid,0,'eof');
filesize = ftell(fid);
NUM_HEADER_BYTES = 1024;
fseek(fid,0,'bof');
hdr = fread(fid, NUM_HEADER_BYTES, 'char*1');
info = getHeader(hdr);
if isfield(info.header, 'version')
    version = info.header.version;
else
    version = 0.0;
end

% set parameters
SAMPLES_PER_RECORD = 1024;
bStr = {'ts' 'nsamples' 'recNum' 'data' 'recordMarker'};
bTypes = {'int64' 'uint16' 'uint16' 'int16' 'uint8'};
bRepeat = {1 1 1 SAMPLES_PER_RECORD 10};
dblock = struct('Repeat',bRepeat,'Types', bTypes,'Str',bStr);
if version < 0.2, dblock(3) = []; end
if version < 0.1, dblock(1).Types = 'uint64'; dblock(2).Types = 'int16'; end


blockBytes = str2double(regexp({dblock.Types},'\d{1,2}$','match', 'once')) ./8 .* cell2mat({dblock.Repeat});
numIdx = floor((filesize - NUM_HEADER_BYTES)/sum(blockBytes));

% switch filetype
%     case '.events'
%         timestamps = segRead('timestamps')./info.header.sampleRate;
%         info.sampleNum = segRead('sampleNum');
%         info.eventType = segRead('eventType');
%         info.nodeId = segRead('nodeId');
%         info.eventId = segRead('eventId');
%         data = segRead('data');
%         if version >= 0.2, info.recNum = segRead('recNum'); end
%     case '.continuous'
%         info.ts = segRead('ts');
%         info.nsamples = segRead('nsamples');
%         if ~all(info.nsamples == SAMPLES_PER_RECORD)&& version >= 0.1, error('Found corrupted record'); end
%         if version >= 0.2, info.recNum = segRead('recNum'); end
%         data = segRead('data', 'b').*info.header.bitVolts; % read in data
        if isempty(range)
            data = segRead('data','b')*info.header.bitVolts;  
        else
            data = segReadRange('data','b',range)*info.header.bitVolts;  
        end
%         timestamps = nan(size(data));
%         current_sample = 0;
%         for record = 1:length(info.ts)
%             timestamps(current_sample+1:current_sample+info.nsamples(record)) = info.ts(record):info.ts(record)+info.nsamples(record)-1;
%             current_sample = current_sample + info.nsamples(record);
%         end
%     case '.spikes'
%         timestamps = segRead('timestamps')./info.header.sampleRate;
%         info.source = segRead('source');
%         info.samplenum = segRead('nSamples');
%         info.gain = permute(reshape(segRead('gain'), num_channels, numIdx), [2 1]);
%         info.thresh = permute(reshape(segRead('threshold'), num_channels, numIdx), [2 1]);
%         if version >= 0.4, info.sortedId = segRead('sortedId'); end
%         if version >= 0.2, info.recNum = segRead('recordingNumber'); end
%         data = permute(reshape(segRead('data'), num_samples, num_channels, numIdx), [3 1 2]);
%         data = (data-32768)./ permute(repmat(info.gain/1000,[1 1 num_samples]), [1 3 2]);
% end
if just_opened
fclose(fid);
end

function seg = segRead(segName, mf)
    if nargin == 1, mf = 'l'; end
    segNum = find(strcmp({dblock.Str},segName));
    fseek(fid, sum(blockBytes(1:segNum-1))+NUM_HEADER_BYTES, 'bof'); 
    seg = fread(fid, numIdx*dblock(segNum).Repeat, sprintf('%d*%s', dblock(segNum).Repeat,dblock(segNum).Types), sum(blockBytes) - blockBytes(segNum), mf);
end

function seg=segReadRange(segName,mf,range)
    segNum = find(strcmp({dblock.Str},segName));
    skip = sum(blockBytes) - blockBytes(segNum);
    rangeB(1)=dblock(segNum).Repeat*floor(range(1)/dblock(segNum).Repeat);
    blockNum = rangeB(1)/dblock(segNum).Repeat; 
    startidx = range(1)-rangeB(1)+1;
    rangeB(2)=range(2); 
    
    fseek(fid, sum(blockBytes(1:segNum-1))+NUM_HEADER_BYTES+blockNum*sum(blockBytes), 'bof'); 
    seg = fread(fid, rangeB(2)-rangeB(1), sprintf('%d*%s', dblock(segNum).Repeat,dblock(segNum).Types), skip, mf);
    seg=seg(startidx:end); 
end


end
function info = getHeader(hdr)
eval(char(hdr'));
info.header = header;
end
