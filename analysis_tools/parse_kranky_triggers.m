function [trigger_times packet_values] = parse_kranky_triggers(event_times, event_values)
plottest = false;
baudrate = 1e3;
bap = 1/baudrate; 
interval_forward = 25*bap;
trigger_times  = [];
packet_values = [];


tDiff = diff(event_times);

% find trigger intro sequences
idxsdiff = strfind(round(tDiff(:)',3), [bap bap bap bap bap]);
idxsval = strfind(event_values(:)', [1 0 1 0 1 0]);
idxs_trigger_start = intersect(idxsdiff, idxsval); 


% filter triggers for at least x time preceeding
triggerok = ones(size(idxs_trigger_start));
for kt= 1:length(idxs_trigger_start)
    if idxs_trigger_start(kt) ~= 1
        if tDiff(idxs_trigger_start(kt)-1) < interval_forward
%             error('bad trigger')
            triggerok(kt) = 0;
            
        end
    end
end
idxs_trigger_start=idxs_trigger_start(triggerok==1);

% find trigger times
trigger_times = event_times(idxs_trigger_start);


% parse trigger packets
for kt = 1:length(idxs_trigger_start)
    try
        kt_idxs = find(event_times >= event_times(idxs_trigger_start(kt)) & event_times < event_times(idxs_trigger_start(kt)) + interval_forward);  
        kt_times = event_times(kt_idxs); 
        kt_times = kt_times-kt_times(1);  
        kt_values = event_values(kt_idxs);
        logic = times2logic(kt_times,kt_values, baudrate);
        bitstr = mat2str(double(logic(7:22)));
        bitstr = bitstr(~isspace(bitstr));
        bitstr = bitstr(2:end-1);
        packet_values(end+1) = bin2dec(bitstr);
    catch
        if kt==length(idxs_trigger_start)
            warning(sprintf('Final Trigger (%d of %d) Trunkated, ignoring it', kt, length(idxs_trigger_start)))
            idxs_trigger_start = idxs_trigger_start(1:end-1);
            trigger_times = trigger_times(1:end-1);
        else
            error(sprintf('Error parsing trigger %d of %d', kt, length(idxs_trigger_start)))
        end
    end
        
end

% check that packet values match trials
if packet_values ~= 0:length(trigger_times)-1
    error('Packet values did not return expected ascending numbers. Could be missind a trial!')
end

% do plots
if plottest
    plot(event_times,event_values)
    hold on;
    for tt=trigger_times
        plot([tt tt], [0 1], 'r')
    end
end
% end of main function 
end

%% subfunctions
function logic = times2logic(times, values, baudrate)
    bap = 1/baudrate; 
    checktimes = bap/2:bap:max(times)+bap/2; 
    logic = [];
    for t = checktimes 
        idx_last = find(times<t, 1, 'last');
        idx_next = find(times>t, 1, 'first');
        if (values(idx_last)==0 & values(idx_next)==1)
            logic(end+1) = 0;
        elseif (values(idx_last)==1 & values(idx_next)==0)
            logic(end+1) = 1; 
        elseif isempty(idx_next)
            logic(end+1) = values(idx_last);  
        else
            error('Bad Trigger, this should never happen')
        end
    end
    logic = logic==1;
end

