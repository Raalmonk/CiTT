function result = checkModelTestInterface(modelPath)
%CHECKMODELTESTINTERFACE Review whether the model exposes CiTT_TestInterface.

result = feval('citt.runTeachingModelReview', struct("ModelPath", string(modelPath)));
end
