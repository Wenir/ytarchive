{
  dockerTools
, buildEnv
, coreutils
, lib
, app
}:
let
  env = buildEnv {
    name = "image-root";
    pathsToLink = [ "/bin" ];
    paths = [
      dockerTools.binSh
      dockerTools.fakeNss
      coreutils
    ];
  };
in
dockerTools.buildLayeredImage {
  name = "${app.name}-image";
  tag = "latest";
  contents = [
    env
  ];
  config = {
    Cmd = [
     "${lib.getExe app}"
    ];
  };
}