function image = readImageBytes(imagePath)
%READIMAGEBYTES Read an image and return bytes, MIME type, and base64 text.

imagePath = string(imagePath);
if strlength(imagePath) == 0 || exist(imagePath, "file") ~= 2
    error("CiTT:ImageMissing", "Image file not found: %s", imagePath);
end

fid = fopen(imagePath, "rb");
if fid < 0
    error("CiTT:ImageOpenFailed", "Could not open image file: %s", imagePath);
end
cleanup = onCleanup(@() fclose(fid));
bytes = fread(fid, Inf, "*uint8");

[~, ~, ext] = fileparts(imagePath);
ext = lower(string(ext));
switch ext
    case {".jpg", ".jpeg"}
        mimeType = "image/jpeg";
    case ".png"
        mimeType = "image/png";
    case ".gif"
        mimeType = "image/gif";
    case ".webp"
        mimeType = "image/webp";
    otherwise
        mimeType = "application/octet-stream";
end

try
    encoded = string(matlab.net.base64encode(bytes));
catch
    encoder = javaMethod('getEncoder', 'java.util.Base64');
    encoded = string(char(encoder.encodeToString(bytes)));
end

image = struct();
image.path = imagePath;
image.bytes = bytes;
image.mime_type = mimeType;
image.base64 = encoded;
end
