function app = citt()
%CITT Launch the MATLAB-native CiTT plugin from the repository root.
%   Preferred setup:
%       addpath(fullfile(pwd, "vericircuit-tutor", "matlab"))
%       citt

repoRoot = fileparts(mfilename("fullpath"));
matlabRoot = fullfile(repoRoot, "matlab");
if exist(matlabRoot, "dir") == 7
    addpath(matlabRoot, "-begin");
end

app = feval('citt.openApp');
end
