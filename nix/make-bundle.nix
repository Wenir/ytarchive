{
  callPackage
, python3Packages
, make-app
, make-run
, make-image
, make-docker-push
, make-docker-run
}:
{
  app_name
, runtimeInputs ? []
, python-libs ? (ps: [])
}:
rec {
  app = make-app {
    inherit app_name runtimeInputs;
    propagatedBuildInputs = python-libs python3Packages;
  };
  run = make-run {
    inherit app;
  };
  image = make-image {
    inherit app;
  };
  push = make-docker-push {
    name = app_name + "-app";
    inherit image;
  };
  docker-run = make-docker-run {
    name = app_name + "-app";
    inherit image;
  };
}