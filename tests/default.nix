{
  python3
, writeShellApplication
}:
let
  python = python3.withPackages (ps: [
    ps.pytest
    ps.pytest_xdist
    ps.ytarchive_lib
    ps.shortuuid
    ps.filelock
  ]);
in
writeShellApplication {
  name = "tests";
  runtimeInputs = [ python ];
  text = ''
    cd ${./tests}
    exec pytest -n auto "$@"
  '';
}