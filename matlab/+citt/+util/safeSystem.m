function result = safeSystem(commandText)
%SAFESYSTEM Run a shell command and return a non-throwing result struct.

result = struct();
result.command = string(commandText);
result.status = -1;
result.stdout = "";
result.stderr = "";

try
    [status, output] = system(char(commandText));
    result.status = status;
    result.stdout = string(output);
catch systemError
    result.status = -1;
    result.stderr = string(systemError.message);
end
end
