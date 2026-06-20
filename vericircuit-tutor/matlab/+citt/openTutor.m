function app = openTutor(labId)
%OPENTUTOR Open the CiTT MATLAB/Simscape tutor popup.

if nargin < 1 || strlength(string(labId)) == 0
    labId = "rc_antialias_adc";
end

app = citt(labId);
end
