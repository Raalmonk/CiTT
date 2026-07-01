function test_snapshot_crop_contract()
%TEST_SNAPSHOT_CROP_CONTRACT Guard focus snapshots against sparse-line crops.

addpath(fileparts(fileparts(mfilename("fullpath"))));
config = feval('citt.loadConfig');
sourcePath = fullfile(config.MatlabRoot, "+citt", "captureModelSnapshot.m");
sourceText = string(fileread(sourcePath));

assert(contains(sourceText, "denseRows = find(rowCounts >= rowThreshold);"), ...
    "Snapshot content crop should ignore sparse rows from long wires or corner highlights.");
assert(contains(sourceText, "denseCols = find(colCounts >= colThreshold);"), ...
    "Snapshot content crop should ignore sparse columns from long wires or corner highlights.");
assert(~contains(sourceText, "coordRight = min(coordRight, targetRight + 2);"), ...
    "Focus crop must not trim to the exact target block edge when a nearby block exists.");
end
