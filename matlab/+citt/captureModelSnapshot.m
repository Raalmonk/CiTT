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
cropBlockPaths = optionStringList(options, "CropBlockPath");
explicitCropBlockPaths = optionStringList(options, "CropBlockPaths");
if ~isempty(explicitCropBlockPaths)
    cropBlockPaths = explicitCropBlockPaths;
end
showModel = optionLogical(options, "ShowModel", false);
trimWhitespace = optionLogical(options, "TrimWhitespace", true);

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
    if showModel
        open_system(char(modelName));
    end
catch openError
    error("CiTT:ModelSnapshotOpenFailed", "Could not open model for preview: %s", openError.message);
end

printTarget = snapshotTarget(modelName, targetSystem);
try
    if showModel
        try
            open_system(char(printTarget));
        catch
        end
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
    if ~isempty(cropBlockPaths)
        cropSnapshotAroundBlock(outputPath, modelName, cropBlockPaths);
    elseif cropHighlights
        cropHighlightedSnapshot(outputPath);
    end
    if trimWhitespace
        cropSnapshotToContent(outputPath);
    end
catch printError
    error("CiTT:ModelSnapshotPrintFailed", "Could not export Simulink preview: %s", printError.message);
end

if ~isExistingFile(outputPath)
    error("CiTT:ModelSnapshotNotWritten", "Simulink preview was not written: %s", outputPath);
end

result.success = true;
result.target_system = string(printTarget);
if trimWhitespace
    result.message = "Preview updated and cropped to model content.";
else
    result.message = "Preview updated.";
end
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

function values = optionStringList(options, fieldName)
values = strings(0, 1);
if ~isstruct(options) || ~isfield(options, fieldName)
    return
end
raw = options.(fieldName);
if isempty(raw)
    return
end
if iscell(raw)
    for i = 1:numel(raw)
        values(end + 1, 1) = string(raw{i}); %#ok<AGROW>
    end
else
    values = string(raw(:));
end
values = values(strlength(strtrim(values)) > 0);
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

function cropSnapshotToContent(outputPath)
try
    [imageData, ~, alpha] = imread(char(outputPath));
catch
    return
end
if ndims(imageData) < 3 || size(imageData, 3) < 3
    return
end

rgb = double(imageData(:, :, 1:3));
% Simulink exports a white canvas. Crop it by keeping dark/colored pixels,
% including anti-aliased text and highlighted diagram marks.
nearWhite = rgb(:, :, 1) > 246 & rgb(:, :, 2) > 246 & rgb(:, :, 3) > 246;
contentMask = ~nearWhite;
if ~isempty(alpha)
    contentMask = contentMask & alpha > 0;
end
[rows, cols] = find(contentMask);
if numel(rows) < 40
    return
end

[height, width, ~] = size(imageData);
padX = max(32, round(0.025 * width));
padY = max(28, round(0.025 * height));
rowMin = max(1, min(rows) - padY);
rowMax = min(height, max(rows) + padY);
colMin = max(1, min(cols) - padX);
colMax = min(width, max(cols) + padX);

if rowMax - rowMin < 90 || colMax - colMin < 120
    return
end
if rowMin == 1 && rowMax == height && colMin == 1 && colMax == width
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

function cropSnapshotAroundBlock(outputPath, modelName, blockPaths)
try
    [imageData, ~, alpha] = imread(char(outputPath));
catch
    cropHighlightedSnapshot(outputPath);
    return
end

blockPaths = string(blockPaths(:));
targetPositions = zeros(numel(blockPaths), 4);
validTargets = false(numel(blockPaths), 1);
for i = 1:numel(blockPaths)
    try
        targetPositions(i, :) = get_param(char(blockPaths(i)), "Position");
        validTargets(i) = true;
    catch
    end
end
targetPositions = targetPositions(validTargets, :);
if isempty(targetPositions)
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
    validBlockPaths = string(blocks(valid));
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

targetLeft = min(targetPositions(:, 1));
targetTop = min(targetPositions(:, 2));
targetRight = max(targetPositions(:, 3));
targetBottom = max(targetPositions(:, 4));
targetCenterX = (targetLeft + targetRight) / 2;
targetCenterY = (targetTop + targetBottom) / 2;
viewWidth = max(520, (targetRight - targetLeft) + 360);
viewHeight = max(220, (targetBottom - targetTop) + 240);
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

otherPositions = positions(~ismember(validBlockPaths, blockPaths), :);
if ~isempty(otherPositions)
    rightNeighborLefts = otherPositions(otherPositions(:, 1) > targetRight + 8 & otherPositions(:, 1) < coordRight, 1);
    if ~isempty(rightNeighborLefts)
        nearestRight = min(rightNeighborLefts);
        if nearestRight - targetRight < 80
            coordRight = min(coordRight, targetRight + 2);
        else
            coordRight = min(coordRight, max(targetRight + 10, nearestRight - 10));
        end
    end
    leftNeighborRights = otherPositions(otherPositions(:, 3) < targetLeft - 8 & otherPositions(:, 3) > coordLeft, 3);
    if ~isempty(leftNeighborRights)
        nearestLeft = max(leftNeighborRights);
        if targetLeft - nearestLeft < 80
            coordLeft = max(coordLeft, targetLeft - 2);
        else
            coordLeft = max(coordLeft, min(targetLeft - 10, nearestLeft + 10));
        end
    end
    aboveNeighborBottoms = otherPositions(otherPositions(:, 4) < targetTop - 8 & otherPositions(:, 4) > coordTop, 4);
    if ~isempty(aboveNeighborBottoms)
        coordTop = max(coordTop, min(targetTop - 10, max(aboveNeighborBottoms) + 10));
    end
    belowNeighborTops = otherPositions(otherPositions(:, 2) > targetBottom + 8 & otherPositions(:, 2) < coordBottom, 2);
    if ~isempty(belowNeighborTops)
        coordBottom = min(coordBottom, max(targetBottom + 10, min(belowNeighborTops) - 10));
    end
end

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
