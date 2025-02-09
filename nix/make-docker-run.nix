{
  writeShellApplication
, skopeo
, podman
, opentofu
, lib
}:
{
  name
, image
}:
let
  tofu = "${lib.getExe opentofu}";
in
writeShellApplication {
  name = "docker-run-${name}";
  text = ''
    "${tofu}" output --raw job-environment | base64 -d > .env_tmp

    ${lib.getExe skopeo} \
        --insecure-policy \
        copy \
        "docker-archive://${image}" \
        "containers-storage:${name}:latest"

    "${lib.getExe podman}" run --rm -it -v "$PWD/.env_tmp:/.env" ${name}:latest
  '';
}