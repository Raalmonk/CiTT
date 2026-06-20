% CiTT generated artifact notice
% RC anti-aliasing before ADC
% Generated for the future MATLAB popup tutor. This script is inspectable text
% for the MVP API and does not make MATLAB a CI dependency.

%% CiTT Overview tab
% Lab: RC anti-aliasing before ADC
% Objective: compare hand cutoff, simple filter behavior, and sampled output.
% BME safety boundary: teaching signal-conditioning model, not patient safety approval.

%% Parameters
fs = 500;                 % Hz
target_fc = 40;           % Hz
R = 39788.7358;           % ohm
C = 100e-9;               % F
duration_s = 2.0;         % seconds
dt = 1/(20*fs);           % fine simulation step for the teaching artifact

%% Hand calculation
fc = 1/(2*pi*R*C);
nyquist = fs/2;
hand_fc_hz = fc;
attenuation_at_60_hz = 1/sqrt(1 + (60/fc)^2);

%% Example signal: ECG-like low-frequency component plus 60 Hz interference
t = 0:dt:duration_s;
ecg_like = 0.8*sin(2*pi*1.2*t) + 0.15*sin(2*pi*2.4*t);
interference_60hz = 0.25*sin(2*pi*60*t);
input_signal = ecg_like + interference_60hz;

%% Simple filter simulation
tau = R*C;
filtered_output = zeros(size(input_signal));
for k = 2:numel(t)
    alpha = dt/(tau + dt);
    filtered_output(k) = filtered_output(k-1) + alpha*(input_signal(k) - filtered_output(k-1));
end

sample_times = 0:(1/fs):duration_s;
sampled_output = interp1(t, filtered_output, sample_times, "linear");

%% Plots
figure("Name", "CiTT RC anti-aliasing before ADC");
subplot(3,1,1);
plot(t, input_signal);
title("Input: ECG-like signal + 60 Hz interference");
xlabel("Time (s)");
ylabel("Voltage (V)");

subplot(3,1,2);
plot(t, filtered_output);
title("Filtered output");
xlabel("Time (s)");
ylabel("Voltage (V)");

subplot(3,1,3);
stem(sample_times, sampled_output, ".");
title("Sampled output");
xlabel("Time (s)");
ylabel("Voltage (V)");

%% Named outputs
simulated_summary = struct( ...
    "fs_hz", fs, ...
    "target_fc_hz", target_fc, ...
    "hand_fc_hz", hand_fc_hz, ...
    "nyquist_hz", nyquist, ...
    "attenuation_at_60_hz", attenuation_at_60_hz);

citt_results = struct( ...
    "hand_fc_hz", hand_fc_hz, ...
    "simulated_summary", simulated_summary, ...
    "sample_times", sample_times, ...
    "sampled_output", sampled_output);

%% CiTT Teach tab
% Ask the student to predict whether 60 Hz is above or below the cutoff.
% Reveal fc = 1/(2*pi*R*C) only after the student commits to the role of R and C.

%% CiTT Probe tab
% Add voltage probe at RC output.
% Log input_signal and filtered_output.
% Compare pre-filter and post-filter 60 Hz component.

%% CiTT Lab Delta tab
% Compare hand_fc_hz, simulated cutoff, and measured cutoff.
% Likely causes include rad/s vs Hz, nF/uF mistakes, tolerance, loading,
% transient settling, Nyquist/sample-rate issues, ADC quantization, solver settings,
% and measurement noise.

%% Future model highlighting
% Future MATLAB plugin may call hilite_system for these blocks/lines.
% This artifact only describes the highlight plan; it does not require MATLAB in CI.
% Future Simulink highlight: input_path
% Future Simulink highlight: rc_filter
% Future Simulink highlight: sampling_stage
% Future Simulink highlight: output_signal
