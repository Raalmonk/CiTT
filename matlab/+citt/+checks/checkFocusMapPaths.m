function result = checkFocusMapPaths(modelPath, focusMapPath)
%CHECKFOCUSMAPPATHS Review focus map paths through the CiTT teaching review.

context = struct("ModelPath", string(modelPath), "FocusMapPath", string(focusMapPath));
result = feval('citt.runTeachingModelReview', context);
end
