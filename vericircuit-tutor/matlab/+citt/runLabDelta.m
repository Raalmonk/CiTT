function response = runLabDelta(labId, request)
%RUNLABDELTA Compare hand, simulation, and measured values.
% Uses the backend when available and a deterministic local fallback otherwise.

if nargin < 1 || strlength(string(labId)) == 0
    labId = "rc_antialias_adc";
end
if nargin < 2 || isempty(request)
    request = struct();
    request.lab_id = string(labId);
    request.hand_values = struct("fc_hz", 40);
    request.simulation_values = struct("fc_hz", 40.1);
    request.measured_values = struct("fc_hz", 251.3);
    request.notes = "Seed case for missing 2*pi or rad/s vs Hz.";
end

try
    url = "http://127.0.0.1:8000/matlab_playground/labs/" + string(labId) + "/lab_delta";
    options = weboptions("MediaType", "application/json", "Timeout", 2);
    response = webwrite(url, request, options);
catch apiError
    warning("CiTT:LabDeltaFallback", ...
        "Backend Lab Delta unavailable (%s). Using local fallback.", apiError.message);
    response = localLabDelta(labId, request);
end

disp(response);
end

function response = localLabDelta(labId, request)
response = struct();
response.lab_id = string(labId);
response.rows = struct([]);
response.likely_causes = struct([]);
response.recommended_probe = "filter_output_voltage_probe";
response.reflection_question = "Which single assumption would you test first?";

hand = request.hand_values.fc_hz;
measured = request.measured_values.fc_hz;
row = struct();
row.quantity = "fc_hz";
row.hand_value = hand;
row.simulation_value = request.simulation_values.fc_hz;
row.measured_value = measured;
row.unit = "Hz";
row.absolute_error = measured - hand;
row.percent_error = (measured - hand)/hand*100;
row.interpretation = "Local fallback compares measured value against hand cutoff.";
response.rows = row;

ratio = measured / hand;
if abs(ratio - 2*pi)/(2*pi) < 0.08
    response.likely_causes = struct("id", "rad_s_vs_hz", ...
        "label", "rad/s vs Hz", ...
        "explanation", "Measured value is near 2*pi times the hand cutoff.", ...
        "check_to_run", "Recompute fc = 1/(2*pi*R*C).", ...
        "severity", "high");
else
    response.likely_causes = struct("id", "measurement_noise", ...
        "label", "Measurement noise", ...
        "explanation", "No strong local pattern was detected.", ...
        "check_to_run", "Confirm probe placement and units.", ...
        "severity", "low");
end
end
