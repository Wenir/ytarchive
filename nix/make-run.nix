{
  writeShellApplication
, opentofu
, lib
}:
{
  app
, runtimeInputs ? []
}:
let
  tofu = "${lib.getExe opentofu}";
in
writeShellApplication {
  name = "${app.name}-run";
  inherit runtimeInputs;
  text = ''
    pushd tofu

    "${tofu}" output --raw job-environment | base64 -d > .env_tmp

    set -o allexport

    # shellcheck source=/dev/null
    source .env_tmp

    set +o allexport

    export ENV_FILE="$PWD/.env_tmp"

    popd

    ${lib.getExe app} "$@"
  '';
}