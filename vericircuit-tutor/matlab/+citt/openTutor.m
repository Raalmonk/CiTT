function app = openTutor()
%OPENTUTOR Compatibility wrapper for the MATLAB-native CiTT plugin.

app = feval('citt.openApp');
end
