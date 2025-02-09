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
    "${tofu}" output --raw job-environment | base64 -d > .env

    ${lib.getExe app}
  '';
}