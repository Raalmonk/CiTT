function toolboxes = findAvailableToolboxes()
%FINDAVAILABLETOOLBOXES Summarize relevant installed MATLAB products.

toolboxes = struct();
toolboxes.installed_names = strings(0, 1);
toolboxes.simulink = false;
toolboxes.simscape = false;
toolboxes.simscape_electrical = false;

try
    installed = ver;
    names = strings(numel(installed), 1);
    for i = 1:numel(installed)
        names(i) = string(installed(i).Name);
    end
    toolboxes.installed_names = names;
    toolboxes.simulink = any(names == "Simulink") || exist("simulink", "file") == 2;
    toolboxes.simscape = any(names == "Simscape") || exist("ssc_new", "file") == 2;
    toolboxes.simscape_electrical = any(names == "Simscape Electrical");
catch
    toolboxes.simulink = exist("simulink", "file") == 2;
    toolboxes.simscape = exist("ssc_new", "file") == 2;
    toolboxes.simscape_electrical = false;
end

toolboxes.simulink_license = testLicense("simulink");
toolboxes.simscape_license = testLicense("simscape");
toolboxes.simscape_electrical_license = testLicense("power_system_blocks");
end

function value = testLicense(featureName)
try
    value = logical(license("test", featureName));
catch
    value = false;
end
end
