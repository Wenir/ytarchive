{
  buildPythonApplication
, setuptools
, wheel
, pytest
, shortuuid
, ytarchive_lib
, writeShellApplication
, lib
}:
let
  app = buildPythonApplication {
    meta.mainProgram = "tests";
    pname = "tests";

    version = "1.0.0";
    pyproject = true;

    src = ./.;

    nativeBuildInputs = [
      setuptools
      wheel
    ];

    propagatedBuildInputs = [
      pytest
      ytarchive_lib
      shortuuid
    ];

    doCheck = false;
  };
in
writeShellApplication {
  name = "tests";
  text = ''
    cd ${./tests}
    exec ${lib.getExe app} "$@"
  '';
}