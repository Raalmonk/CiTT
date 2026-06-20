function varargout = citt(labId)
%CITT Open the CiTT MATLAB popup tutor using bundled offline artifacts.
%   This offline-first launcher does not require a local server.

if nargin < 1 || strlength(string(labId)) == 0
    labId = "rc_antialias_adc";
end

bundle = citt.loadOfflineBundle(labId);
fig = citt.openPopup(bundle);

if nargout > 0
    bundle.popup_figure = fig;
    varargout{1} = bundle;
end
end
