function sl_customization(cm)
%SL_CUSTOMIZATION Register CiTT customization hook placeholder.
%
% CiTT currently emits MATLAB-native teaching review reports through
% citt.runTeachingModelReview. This hook intentionally stays lightweight so
% future SATK agentic-review authoring can register Model Advisor checks
% without changing the public CiTT report schema.

try
    cm.addCustomMenuFcn('Simulink:ToolsMenu', @cittTeachingReviewMenu);
catch
end
end

function schemaFcns = cittTeachingReviewMenu(callbackInfo) %#ok<INUSD>
schemaFcns = {@cittTeachingReviewAction};
end

function schema = cittTeachingReviewAction(callbackInfo) %#ok<INUSD>
schema = sl_container_schema;
schema.label = 'CiTT Teaching Model Review';
schema.childrenFcns = {};
end
