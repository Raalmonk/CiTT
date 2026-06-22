function app = citt()
%CITT Launch the CiTT plugin.
%   Add this folder to the MATLAB path, then run:
%       citt
%   Set CITT_USE_NATIVE_UI=1 to use the MATLAB-native fallback UI.

if string(getenv("CITT_USE_NATIVE_UI")) == "1"
    app = feval('citt.openApp');
else
    app = feval('citt.openHtmlApp');
end
end
