function app = openTutor()
%OPENTUTOR Compatibility wrapper for the CiTT plugin.

if string(getenv("CITT_USE_NATIVE_UI")) == "1"
    app = feval('citt.openApp');
else
    app = feval('citt.openHtmlApp');
end
end
