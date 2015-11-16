function rec = kranky_parse_rec(filename)

% rec = gk_parse_rec(filename)
% filename: fullpath datafile name

% GK modification
%   1) accepts .rec file as well
%   2) works even if some parameter values in rec file is empty

pvpair = {};

% [fpath,fname,fext,ver] = fileparts(filename);
% [fpath,fname,fext] = fileparts(filename);
% if strcmp(fext,'.rec')
%   filename = fullfile(fpath,fname); % GK: if rec file, remove '.rec'
% end
% rec.original_filename = filename;
rec.original_recfilename = [filename];
[fpath,fname,fext] = fileparts(filename);
rec.filename = [fname, fext];
rec.recfilename = [fname, fext, '.rec'];
fid=fopen(rec.original_recfilename);
if fid == -1
  error(['Could not open file: ', rec.recfilename]) 
end

while 1
  tline = fgetl(fid);
  if ~ischar(tline), break, end
  if isspace(tline), continue, end
%  disp(tline)
  
  if strmatch('date:',tline)
    stuff=strread(tline,'date: %s','delimiter','');
    rec.date = stuff{1};
%     rec.timestamp = char(rec.timestamp);
% %    [rec.day,rec.month,rec.daynum,rec.year,rec.time] = ...
% %	strread(rec.timestamp,'%s%s%s%s%s', 'delimiter', ', ');
% %    rec.day = char(rec.day);
% %    rec.month = char(rec.month);
% %    rec.daynum = char(rec.daynum);
% %    rec.year = char(rec.year);
% %    rec.time = char(rec.time);  
  elseif strmatch('format:',tline)
      stuff=strread(tline,'format: %s','delimiter','');
      rec.format=stuff{1}; 
  elseif findstr(': ',tline)
    idx = strfind(tline,': ');
    param =tline(1:idx-1); 
    val = tline(idx+2:end);
   %[param, val] = strread(tline,'%s%s','delimiter',': ');
    pvpair = [pvpair; {param,val}];
%  elseif findstr('=',tline)
%    [param, val] = strread(tline,'%s%s',-1,'delimiter','=');
%    pvpair = [pvpair; cellstr([param,val])];
  end
  
end
fclose(fid);

% Replace params with spaces in them with underscores instead
params = strrep(lower(deblank({pvpair{:,1}})),' ','_');
params = strrep(params,'[','(');
params = strrep(params,']',')');
% Remove blanks from the values (hopefully this is OK).
values = {pvpair{:,2}};
%values = deblank({pvpair{:,2}});
nparams = length(params);

% OK, now discriminate between simple and complex values
cmplx_param_idx = [];
ck = 0; 
sk = 0;

for i=1:length(values)

  % Convert vector parameters to matlab format
  lparen_idx = findstr('(',params{i});
  rparen_idx = findstr(')',params{i});
  if lparen_idx
    idx = str2num(params{i}(lparen_idx+1:rparen_idx-1));
    idx = idx+1;
    params{i}  = [params{i}(1:lparen_idx) num2str(idx) ...
	  params{i}(rparen_idx:end)];
  end  
  
  % if there is a semicolon separated list, of param=value pairs then
  % split up the list
  sc_idx = strfind(values{i},';');
  if sc_idx
%    disp(['Parameter: ' params{i} ' is complex.'])  % comment GK
    cmplx_param_idx = [cmplx_param_idx i];
    ck = ck + 1;
    paramspec = strread(values{i},'%s',-1,'delimiter',';');
    % Extract the subparameters and their values.
    for isp=1:length(paramspec)
      eq_idx = strfind(paramspec{isp},'='); % GK
      if strcmp(paramspec{isp}(end),'=') | strcmp(paramspec{isp}(end),' ') % GK: if values is empty
        subparam{ck}{isp} = paramspec{isp}(1:eq_idx-1);
        subval{ck}{isp} = 'Empty';
      else
        [subparam{ck}(isp), subval{ck}(isp)] = strread(paramspec{isp},'%s%s',1,'delimiter','=');
      end
      % Convert quoted strings
      if findstr('"',char(subval{ck}(isp)))
    	subval{ck}(isp) = strread(char(subval{ck}(isp)),'%q',1);
      end
      
    end
  
  else 
  % Else remainder are the simple parameters
    sk = sk + 1;
    smplparams{sk} = params{i};
    smplvalues{sk} = values{i};   
    if findstr('"',char(smplvalues{sk}))
      smplvalues{sk} = strread(char(smplvalues{sk}),'%q',1);
    end
  end
end

%for i=1:length(values)
%  idx = findstr(values{i},' ms');
%  if idx
%    values{i} = values{i}(1:idx);
%    params{i} = [params{i}, '_ms'];
%  end  
%  values{i} = strrep(values{i},' ','');
%  if ~isletter(values{i})
%    values{i} = str2num(values{i});
%  end
%end

for i=1:length(smplvalues)
  try
      if ~isletter(char(smplvalues{i})) & isspace(char(smplvalues{i}))
        eval(['rec.' smplparams{i} ' = ' smplvalues{i} ';'])
      else
        eval(['rec.' smplparams{i} ' = ' 'smplvalues{i};'])
      end
  catch
      warning(sprintf('Unable to read rc param - %s: %s', smplparams{i}, smplvalues{i}))
  end

end

for i=1:length(cmplx_param_idx)
  for k=1:length(subparam{i})
    char(params{cmplx_param_idx(i)});
    subparam{i}(k);
    subval{i}(k);
    try
    if ~isletter(char(subval{i}(k)))      
      eval(['rec.' params{cmplx_param_idx(i)} '.' char(subparam{i}(k)) ...
	    ' = ' char(subval{i}(k)) ';']);
    else
      eval(['rec.' params{cmplx_param_idx(i)} '.' char(subparam{i}(k)) ...
	    ' = ' 'subval{i}(k);']);
    end
    catch 
        warning(sprintf('Unable to read rc param - %s: ', ['rec.' params{cmplx_param_idx(i)} '.' char(subparam{i}(k)) ...
	    ' = ' char(subval{i}(k)) ';']))
    end
  end    
end

%smplvalues = [struct2cell(rec)' smplvalues];
%smplparams = [fieldnames(rec)' smplparams];
%rec = cell2struct(smplvalues,smplparams,2);


