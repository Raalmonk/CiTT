function response = runLabDelta(request)
%RUNLABDELTA Compatibility wrapper around the MATLAB-native Lab Delta path.

if nargin < 1 || isempty(request)
    error("CiTT:LabDeltaRequestRequired", ...
        "runLabDelta requires a request with hand_values, simulation_values, and lab_csv_path.");
end

response = feval('citt.compareLabDelta', request);
disp(response);
end
