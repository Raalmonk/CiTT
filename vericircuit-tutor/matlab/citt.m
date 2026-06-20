function app = citt()
%CITT Launch the MATLAB-native CiTT plugin.
%   Add this folder to the MATLAB path, then run:
%       citt

app = feval('citt.openApp');
end
