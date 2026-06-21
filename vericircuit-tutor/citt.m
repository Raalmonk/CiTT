function app = citt()
%CITT Launch the CiTT plugin from the repository root.
%   Preferred setup:
%       addpath(fullfile(pwd, "vericircuit-tutor", "matlab"))
%       citt
%   Set CITT_USE_NATIVE_UI=1 to use the MATLAB-native fallback UI.

repoRoot = fileparts(mfilename("fullpath"));
matlabRoot = fullfile(repoRoot, "matlab");
if exist(matlabRoot, "dir") == 7
    addpath(matlabRoot, "-begin");
end

if string(getenv("CITT_USE_NATIVE_UI")) == "1"
    app = feval('citt.openApp');
else
    app = feval('citt.openHtmlApp');
end
end
