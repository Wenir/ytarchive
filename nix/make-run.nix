{
  writeShellApplication
, opentofu
, lib
}:
{
  app
}:
let
  tofu = "${lib.getExe opentofu}";
in
writeShellApplication {
  name = "${app.name}-run";
  text = ''
    cd tofu
    "${tofu}" output --raw job-environment | base64 -d > .env_tmp

    ${lib.getExe app}
  '';
}