function result = checkProbeMapCoverage(specPath, probeMapPath)
%CHECKPROBEMAPCOVERAGE Review requested-output to probe-map coverage.

context = struct("SpecPath", string(specPath), "ProbeMapPath", string(probeMapPath));
result = feval('citt.runTeachingModelReview', context);
end
