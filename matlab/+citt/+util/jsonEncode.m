function text = jsonEncode(value)
%JSONENCODE Encode JSON with pretty formatting when the MATLAB version can.

try
    text = jsonencode(value, "PrettyPrint", true);
catch
    text = jsonencode(value);
end

if isstring(text)
    text = char(text);
end
end
