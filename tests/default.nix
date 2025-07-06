{
  python3
, writeShellApplication
}:
let
  python = python3.withPackages (ps: [
    ps.pytest
    ps.ytarchive_lib
    ps.shortuuid
  ]);
in
writeShellApplication {
  name = "tests";
  runtimeInputs = [ python ];
  text = ''
    cd ${./tests}
    exec pytest "$@"
  '';
}