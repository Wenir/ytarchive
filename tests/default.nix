{
  python3
, writeShellApplication
}:
let
  python = python3.withPackages (ps: [
    ps.pytest
    ps.pytest-asyncio
    ps.pytest-xdist
    ps.ytarchive_lib
    ps.shortuuid
    ps.filelock
    ps.psycopg
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