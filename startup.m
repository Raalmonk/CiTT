%STARTUP Make CiTT source commands available when MATLAB opens in repo root.
repoRoot = fileparts(mfilename("fullpath"));
matlabRoot = fullfile(repoRoot, "matlab");

if exist(fullfile(matlabRoot, "citt.m"), "file") == 2
    addpath(matlabRoot, "-begin");
    rehash;
end
