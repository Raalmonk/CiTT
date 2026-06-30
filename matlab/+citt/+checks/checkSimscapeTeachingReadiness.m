function result = checkSimscapeTeachingReadiness(modelPath)
%CHECKSIMSCAPETEACHINGREADINESS Run the CiTT teaching readiness review.

result = feval('citt.runTeachingModelReview', struct("ModelPath", string(modelPath)));
end
