function result = buildPlayground(labId)
%BUILDPLAYGROUND Build or summarize a MATLAB/Simscape playground.
% Simscape is attempted first where a generated builder exists. When the
% builder or products are unavailable, CiTT returns a hand-check fallback.

if nargin < 1 || strlength(string(labId)) == 0
    labId = "rc_antialias_adc";
end

result = struct();
result.lab_id = string(labId);
result.mode = "hand_check_fallback";
result.model_name = "";
result.messages = strings(0);

try
    if string(labId) == "rc_antialias_adc" && exist("citt_build_rc_antialias_adc_simscape", "file") == 2
        result.model_name = citt_build_rc_antialias_adc_simscape();
        result.mode = "simscape_or_simulink";
        result.messages(end + 1) = "Generated builder completed.";
    else
        result.messages(end + 1) = "No generated builder on path; using hand-check fallback.";
    end
catch buildError
    warning("CiTT:BuildFallback", ...
        "Playground build did not complete (%s). Using hand-check fallback.", buildError.message);
    result.messages(end + 1) = "Build fallback used.";
end

result.hand_check = localHandCheck(labId);
disp(result);
end

function hand = localHandCheck(labId)
if string(labId) == "instrumentation_amplifier_feedback"
    R = 10e3;
    Rg = 1e3;
    vDiff = 1e-3;
    gain = 1 + 2*R/Rg;
    hand = struct("gain_v_per_v", gain, "vout_ideal_v", gain*vDiff);
else
    fs = 500;
    target_fc = 40;
    C = 100e-9;
    R = 1/(2*pi*target_fc*C);
    fc = 1/(2*pi*R*C);
    hand = struct("fs_hz", fs, "target_fc_hz", target_fc, ...
        "R_ohm", R, "C_f", C, "citt_hand_fc_hz", fc, "citt_nyquist_hz", fs/2);
end
end
