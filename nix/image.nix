{
  dockerTools
, buildEnv
, coreutils
, lib
, app
, writeShellApplication
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
  cmd = writeShellApplication {
    name = "${app.name}-docker-cmd";
    text = ''
      echo "nameserver 8.8.8.8" >> /etc/resolv.conf
      ${lib.getExe app}
    '';
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
      "${lib.getExe cmd}"
    ];
  };
}