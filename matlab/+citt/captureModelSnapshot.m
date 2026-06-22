function result = captureModelSnapshot(modelPath, options)
%CAPTUREMODELSNAPSHOT Export the current Simulink diagram view to a PNG.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(modelPath)
    modelPath = config.GeneratedModelPath;
end
if nargin < 2 || isempty(options)
    options = struct();
end

outputPath = optionString(options, "OutputPath", config.ModelSnapshotPath);
targetSystem = optionString(options, "TargetSystem", "");
cropHighlights = optionLogical(options, "CropHighlights", false);
cropBlockPath = optionString(options, "CropBlockPath", "");

result = struct();
result.success = false;
result.image_path = string(outputPath);
result.target_system = "";
result.message = "";

if strlength(strtrim(modelPath)) == 0 || ~isExistingFile(modelPath)
    error("CiTT:ModelSnapshotMissingModel", "No Simulink model is available for preview.");
end

folder = fileparts(char(outputPath));
if exist(folder, "dir") ~= 7
    mkdir(folder);
end

[~, modelName, ~] = fileparts(char(modelPath));
try
    load_system(char(modelPath));
    open_system(char(modelName));
catch openError
    error("CiTT:ModelSnapshotOpenFailed", "Could not open model for preview: %s", openError.message);
end

printTarget = snapshotTarget(modelName, targetSystem);
try
    try
        open_system(char(printTarget));
    catch
    end
    try
        set_param(char(printTarget), "ZoomFactor", "FitSystem");
    catch
        try
            set_param(char(modelName), "ZoomFactor", "FitSystem");
        catch
        end
    end
    drawnow;
    pause(0.15);
    print(char("-s" + printTarget), "-dpng", "-r160", char(outputPath));
    if strlength(strtrim(cropBlockPath)) > 0
        cropSnapshotAroundBlock(outputPath, modelName, cropBlockPath);
    elseif cropHighlights
        cropHighlightedSnapshot(outputPath);
    end
catch printError
    error("CiTT:ModelSnapshotPrintFailed", "Could not export Simulink preview: %s", printError.message);
end

if ~isExistingFile(outputPath)
    error("CiTT:ModelSnapshotNotWritten", "Simulink preview was not written: %s", outputPath);
end

result.success = true;
result.target_system = string(printTarget);
result.message = "Preview updated.";
end

function value = optionString(options, fieldName, defaultValue)
value = string(defaultValue);
if isstruct(options) && isfield(options, fieldName)
    raw = options.(fieldName);
    if ~isempty(raw)
        value = string(raw);
    end
end
end

function value = optionLogical(options, fieldName, defaultValue)
value = logical(defaultValue);
if isstruct(options) && isfield(options, fieldName)
    try
        value = logical(options.(fieldName));
    catch
        value = logical(defaultValue);
    end
end
end

function cropHighlightedSnapshot(outputPath)
try
    [imageData, ~, alpha] = imread(char(outputPath));
catch
    return
end
if ndims(imageData) < 3 || size(imageData, 3) < 3
    return
end

red = double(imageData(:, :, 1));
green = double(imageData(:, :, 2));
blue = double(imageData(:, :, 3));
mask = red < 100 & green > 120 & blue > 120 & (green - red) > 45 & (blue - red) > 45;
[rows, cols] = find(mask);
if numel(rows) < 40
    return
end

[height, width, ~] = size(imageData);
rowMin = max(1, min(rows) - 120);
rowMax = min(height, max(rows) + 120);
colMin = max(1, min(cols) - 180);
colMax = min(width, max(cols) + 180);

if (rowMax - rowMin) < 160
    center = round((rowMin + rowMax) / 2);
    rowMin = max(1, center - 90);
    rowMax = min(height, center + 90);
end
if (colMax - colMin) < 260
    center = round((colMin + colMax) / 2);
    colMin = max(1, center - 150);
    colMax = min(width, center + 150);
end

cropped = imageData(rowMin:rowMax, colMin:colMax, :);
if isempty(alpha)
    imwrite(cropped, char(outputPath));
else
    croppedAlpha = alpha(rowMin:rowMax, colMin:colMax);
    imwrite(cropped, char(outputPath), "Alpha", croppedAlpha);
end
end

function cropSnapshotAroundBlock(outputPath, modelName, blockPath)
try
    [imageData, ~, alpha] = imread(char(outputPath));
    targetPosition = get_param(char(blockPath), "Position");
catch
    cropHighlightedSnapshot(outputPath);
    return
end

try
    blocks = find_system(char(modelName), "SearchDepth", 1, "Type", "Block");
    positions = zeros(numel(blocks), 4);
    valid = false(numel(blocks), 1);
    for i = 1:numel(blocks)
        try
            positions(i, :) = get_param(blocks{i}, "Position");
            valid(i) = true;
        catch
        end
    end
    positions = positions(valid, :);
    if isempty(positions)
        cropHighlightedSnapshot(outputPath);
        return
    end
catch
    cropHighlightedSnapshot(outputPath);
    return
end

[height, width, ~] = size(imageData);
diagramLeft = min(positions(:, 1)) - 100;
diagramTop = min(positions(:, 2)) - 100;
diagramRight = max(positions(:, 3)) + 100;
diagramBottom = max(positions(:, 4)) + 100;
if diagramRight <= diagramLeft || diagramBottom <= diagramTop
    cropHighlightedSnapshot(outputPath);
    return
end

targetCenterX = mean(targetPosition([1 3]));
targetCenterY = mean(targetPosition([2 4]));
viewWidth = max(360, (targetPosition(3) - targetPosition(1)) + 420);
viewHeight = max(220, (targetPosition(4) - targetPosition(2)) + 260);
viewAspect = 2.65;
if viewWidth / viewHeight > viewAspect
    viewHeight = viewWidth / viewAspect;
else
    viewWidth = viewHeight * viewAspect;
end

coordLeft = targetCenterX - viewWidth / 2;
coordRight = targetCenterX + viewWidth / 2;
coordTop = targetCenterY - viewHeight / 2;
coordBottom = targetCenterY + viewHeight / 2;

colMin = coordToPixel(coordLeft, diagramLeft, diagramRight, width);
colMax = coordToPixel(coordRight, diagramLeft, diagramRight, width);
rowMin = coordToPixel(coordTop, diagramTop, diagramBottom, height);
rowMax = coordToPixel(coordBottom, diagramTop, diagramBottom, height);

colMin = max(1, min(width, colMin));
colMax = max(1, min(width, colMax));
rowMin = max(1, min(height, rowMin));
rowMax = max(1, min(height, rowMax));
if colMax - colMin < 80 || rowMax - rowMin < 80
    cropHighlightedSnapshot(outputPath);
    return
end

cropped = imageData(rowMin:rowMax, colMin:colMax, :);
if isempty(alpha)
    imwrite(cropped, char(outputPath));
else
    croppedAlpha = alpha(rowMin:rowMax, colMin:colMax);
    imwrite(cropped, char(outputPath), "Alpha", croppedAlpha);
end
end

function pixel = coordToPixel(value, coordMin, coordMax, pixelCount)
pixel = round(((double(value) - double(coordMin)) / (double(coordMax) - double(coordMin))) * double(pixelCount));
end

function target = snapshotTarget(modelName, requestedTarget)
target = string(modelName);
requestedTarget = string(requestedTarget);
if strlength(strtrim(requestedTarget)) == 0
    return
end
try
    if strcmp(get_param(char(requestedTarget), "Type"), "block")
        parent = string(get_param(char(requestedTarget), "Parent"));
        if strlength(strtrim(parent)) > 0
            target = parent;
            return
        end
    end
    target = requestedTarget;
catch
    target = string(modelName);
end
end

function tf = isExistingFile(pathValue)
code = exist(string(pathValue), "file");
tf = code == 2 || code == 4;
end
