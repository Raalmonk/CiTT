function test_html_app_surface_contract()
%TEST_HTML_APP_SURFACE_CONTRACT Keep the main teaching UI simple.

addpath(fileparts(fileparts(mfilename("fullpath"))));
config = feval('citt.loadConfig');
htmlPath = fullfile(config.MatlabRoot, "resources", "ui", "citt_app.html");
text = string(fileread(htmlPath));
appPath = fullfile(config.MatlabRoot, "+citt", "openHtmlApp.m");
appText = string(fileread(appPath));

assert(contains(text, "send(""chat_submit"""), "Composer submit should route through chat_submit.");
assert(~contains(text, "isEnterKey(event) && !event.shiftKey"), ...
    "Plain Enter in CiTT textareas should insert a newline, not submit.");
assert(contains(text, "(event.metaKey || event.ctrlKey) && isEnterKey(event)"), ...
    "Cmd/Ctrl+Enter should remain available as an explicit submit shortcut.");
assert(~contains(text, "data-action=""run_pipeline"""), "Main HTML must not expose run_pipeline as a visible button action.");
assert(contains(text, "<section class=""tool-groups"" aria-hidden=""true"">"), ...
    "Advanced tool groups should stay hidden from the primary teaching surface.");

composerBlock = extractBetween(text, "<form class=""composer""", "</form>");
assert(~isempty(composerBlock));
composerBlock = composerBlock(1);
assert(count(composerBlock, "<button") == 9, ...
    "Composer should expose one plus menu, seven hidden menu actions, and one Run submit.");
assert(contains(composerBlock, "id=""composerToolsButton"""));
assert(contains(composerBlock, "<button type=""submit"" class=""btn primary"">Run</button>"));

assert(contains(text, "<div class=""learning-more-menu"" id=""learningMoreMenu"">"));
assert(contains(text, "Reveal answer"));
assert(contains(text, "Show highlight"));
assert(contains(text, "Measure"));
assert(contains(text, ".learning-model img") && contains(text, "max-height: 100%;"), ...
    "Learning model evidence should fit inside the model pane instead of scrolling out of view.");
assert(~contains(text, ".learning-model img {" + newline + "      display: block;" + newline + "      width: 100%;" + newline + "      max-width: 100%;" + newline + "      max-height: none;"), ...
    "Learning model images must not be forced to full width with unlimited height.");
assert(contains(text, "data-zoom-surface=""learning""") && contains(text, "data-zoom-action=""in""") && ...
    contains(text, "wireModelZoom()") && contains(text, "function setModelZoom"), ...
    "Model evidence should support user zoom and pan in the learning surface.");

learningSurface = extractBetween(text, "function hasLearningSurface(currentState) {", "function renderState() {");
assert(~isempty(learningSurface));
learningSurface = learningSurface(1);
assert(contains(learningSurface, "return !!(hasModel && hasTeachingPlan);"), ...
    "Learning surface should not appear for model-only state without a concrete teaching plan.");

messageActions = extractBetween(text, "function messageActionsHtml(message) {", "function avatarText(role) {");
assert(~isempty(messageActions));
messageActions = messageActions(1);
assert(~contains(messageActions, "Open Teaching</button>"));
assert(~contains(messageActions, "Open Probe</button>"));
assert(~contains(messageActions, "Open Evidence</button>"));
assert(~contains(messageActions, "Model Tests</button>"));
assert(~contains(messageActions, "Traceability</button>"));

assert(contains(appText, "if taskId ~= activeTaskId"), ...
    "Selecting the already-active task must not overwrite saved artifacts with transient UI state.");
assert(contains(appText, "shouldRestoreTeaching") && contains(appText, "stage"), ...
    "Saved teach/probe/evidence tasks should restore a matching teaching plan even when event history is sparse.");
assert(contains(appText, "zoomLearningModel") && contains(appText, "model_zoom"), ...
    "UI QA hooks should be able to exercise the model zoom behavior.");
end
