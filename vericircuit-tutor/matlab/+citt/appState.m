function state = appState()
%APPSTATE Build the mutable state struct used by the CiTT UI callbacks.

config = feval('citt.loadConfig');
state = struct();
state.Config = config;
state.ImagePath = "";
state.PromptText = "";
state.Spec = [];
state.SpecPath = config.LastSpecPath;
state.AgentTaskPath = config.AgentTaskPath;
state.AgentRun = [];
state.ModelPath = config.GeneratedModelPath;
state.ModelSnapshotPath = config.ModelSnapshotPath;
state.FocusMapPath = config.FocusMapPath;
state.ProbeMapPath = config.ProbeMapPath;
state.TeachingPlan = [];
state.TeachingStepIndex = 1;
state.HintLevel = 0;
state.TeachingImagePath = "";
state.LastSetupReport = [];
state.LastModelCheck = [];
state.LastSimulation = [];
state.LastBode = [];
state.LastProbe = [];
state.LabCsvPath = "";
state.OpAmpPart = "";
state.LastLabDelta = [];
state.EvidencePackPath = config.EvidencePackPath;
state.LastEvidencePack = [];
state.LastRequirements = [];
state.LastSweep = [];
state.LastFaults = [];
state.LastExplainability = [];
state.LastAssessment = [];
state.LastEconomics = [];
state.LastScopeGuardrail = [];
end
