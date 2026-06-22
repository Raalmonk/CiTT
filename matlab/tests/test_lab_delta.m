function test_lab_delta()
%TEST_LAB_DELTA Verify CSV Lab Delta matching and cause detection.

addpath(fileparts(fileparts(mfilename("fullpath"))));
config = feval('citt.loadConfig');
csvPath = fullfile(config.WorkDir, "test_lab_delta.csv");
fid = fopen(csvPath, "w");
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "quantity,hand,simulation,measured,unit\n");
fprintf(fid, "fc_hz,40,40.1,251.3,Hz\n");
clear cleanup

reportPath = fullfile(config.WorkDir, "test_lab_delta_report.json");
report = feval('citt.compareLabDelta', struct(), struct(), csvPath, struct("OutputPath", reportPath));
assert(report.success);
assert(numel(report.rows) == 1);
assert(exist(reportPath, "file") == 2);
labels = string({report.likely_causes.label});
assert(any(labels == "2*pi error"));
assert(report.likely_causes(1).severity == "likely");
end
