function recname=write_kranky_recfile(datapath)


% load pbrec file
DIR = dir(datapath);
for k=1:length(DIR)
    [ph name ext] = fileparts(DIR(k).name); 
    if strcmp(ext, '.pbrec')
        [ph pbrecname ext] = fileparts(DIR(k).name); 
        break
    end
end
recname = fullfile(datapath, [pbrecname '.rec']);
pbrecname = fullfile(datapath, [pbrecname '.pbrec']);
rec = kranky_parse_rec(pbrecname); 

% add session parameters to rec from session info
sessioninfo = get_session_info(datapath);
% look for bandpass Filter
processer_idxs = 1:length(sessioninfo.processors(:,1));
bpf_logic = strcmp(sessioninfo.processors(:,2),'Filters/Bandpass Filter');
srfpga_logic = strcmp(sessioninfo.processors(:,2),'Sources/Rhythm FPGA');
has_channels_logic = ~cellfun(@isempty,sessioninfo.processors(:,3));
srfpga_idx = processer_idxs(srfpga_logic & has_channels_logic);
bpf_idx = processer_idxs(bpf_logic & has_channels_logic);
if ~isempty(bpf_idx)
    spike_processor = sessioninfo.processors{bpf_idx(1),1};
    
elseif ~isempty(srfpga_idx)
    lfp_processor = sessioninfo.processors{srfpga_idx(1),1};
end

if ~isempty(srfpga_idx)
    lfp_processor = sessioninfo.processors{srfpga_idx(1),1};
end
% get kranky triggers from ai data
trigger_ch = 1; 
[data, timestamps, info] = load_open_ephys_data_faster(fullfile(datapath,'all_channels.events'));
[cd, cts, cinfo] = load_open_ephys_data_faster(fullfile(datapath,sprintf('%d_CH1.continuous',spike_processor)));
first_timestamp = cts(1);
n_samples = length(cts); 
event_idxs = data==trigger_ch;
event_times = timestamps(event_idxs);
event_values = info.eventId(event_idxs); 
[trigger_times, packet_values] = parse_kranky_triggers(event_times, event_values);

% add parameters to rec
rec.spike_processor = num2str(spike_processor);
rec.lfp_processor = num2str(lfp_processor);
rec.first_timestamp = num2str(first_timestamp);  
rec.n_ai_chan = num2str(length(sessioninfo.processors{1,3}));
rec.ai_freq = num2str(info.header.sampleRate);
rec.n_samples = num2str(n_samples); 

%% open new .rec file
% pbrecfid = fopen(pbrecname, 'r');
recfid = fopen(recname, 'w');

%% write params to new .rec file
parameters_not_to_write = {'original_recfilename','filename','recfilename','stim', 'trial'};
recfields = fields(rec); 
for kfield = 1:length(recfields);
    if any(strcmp(recfields{kfield},parameters_not_to_write))
        continue
    end
    fprintf(recfid,'%s: %s\n',recfields{kfield},getfield(rec, recfields{kfield}));
end

%% write stims to new .rec file
for kstim = 1:length(rec.stim)
    fprintf(recfid, 'stim[%d]: file="%s";\n',kstim-1, rec.stim(kstim).file{1});
end
%% write trials to new .rec file
% calculate ai sample ranges from trigger times
ntrials = min(length(trigger_times), length(rec.trial));

trial_samples = zeros(ntrials,2);
for ktl = 1:ntrials-1
    trial_samples(ktl,:) = [trigger_times(ktl) trigger_times(ktl+1)]*info.header.sampleRate-first_timestamp;
end
% this sucks - need to calculate final trigger time from ao sample range.  
trial_samples(end,1) = trigger_times(end)*info.header.sampleRate-first_timestamp;
ao_range = rec.trial(ntrials).ao_range; 
trial_samples(end,2) = trial_samples(end,1)+(ao_range(2)-ao_range(1))/ str2num(rec.ao_freq) * info.header.sampleRate-first_timestamp;  
% write trial lines to rec file
for ktl = 1:ntrials
%     disp(trial_lines{ktl})
    fprintf(recfid, 'trial[%d]: stim_index=%d;ai_range=[%.f,%.f];ao_range=[%.f,%.f]\n', ktl-1, rec.trial(ktl).stim_index, trial_samples(ktl, 1), trial_samples(ktl, 2), rec.trial(ktl).ao_range(1), rec.trial(ktl).ao_range(2));
end
fclose(recfid);

% while test
%     line = fgets(pbrecfid);
%     all_lines{end+1}=line; 
%     if strfind(line, 'ao_range')
%         break
%     end
%     fprintf(recfid,line);
% end
% trial_lines = {};
% while line~=-1
%     all_lines{end+1}=line; 
%     trial_lines{end+1}=line;
%     line = fgets(pbrecfid);
% end
% fclose(pbrecfid);
% this sucks - need to calculate final trigger time from ao sample range.  
% idx_last_trial = find(~cellfun(@isempty, strfind(trial_lines, sprintf('trial[%d]', ntrials-1))),1,'first');
% last_trial_line = trial_lines{idx_last_trial};
% idx_ao_range = strfind(last_trial_line,'ao_range=');
% idx_ao_range_end = strfind(last_trial_line(idx_ao_range:end),']');
% idx_ao_range_end = idx_ao_range_end(1) + idx_ao_range-1;
% ao_range = str2num(last_trial_line(idx_ao_range+9:idx_ao_range_end));
% idx_ao_rate_line = find(~cellfun(@isempty, strfind(all_lines,'ao_freq:')),1,'first');
% ao_rate_line = all_lines{idx_ao_rate_line};
% ao_rate_line_idx = strfind(ao_rate_line,'ao_freq:')+8;
% ao_freq = str2num(ao_rate_line(ao_rate_line_idx:end));
% trial_length = (ao_range(2)-ao_range(1))/ao_freq;
% trial_samples(end,2) = trial_samples(end,1) + round(trial_length*info.header.sampleRate);

% [last_trial_line(idx_ao_range:idx_ao_range_end) ';'])


% % write trial lines to rec file
% ktrial = 0; 
% for ktl = 1:ntrials
% %     disp(trial_lines{ktl})
%     tline = trial_lines{ktl};
%     if ~isempty(strfind(tline, sprintf('trial[%d]:',ktrial)))
%         fprintf(recfid, [tline(1:end-1) '; ai_range=[%d,%d]\n'], trial_samples(ktl,1) , trial_samples(ktl,2));
%         ktrial = ktrial+1; 
%     end
% end
% fclose(recfid);
% 
% 
% 
% 


