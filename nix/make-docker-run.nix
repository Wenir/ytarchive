{
  writeShellApplication
, skopeo
, podman
, opentofu
, lib
, make-run
}:
let
  tofu = "${lib.getExe opentofu}";
in
{
  name
, image
}:
let
  app = writeShellApplication {
    name = "docker-run-${name}";
    text = ''
      ${lib.getExe skopeo} \
          --insecure-policy \
          copy \
          "docker-archive://${image}" \
          "containers-storage:${name}:latest"

      "${lib.getExe podman}" run --rm -it -v "$ENV_FILE:/.env" ${name}:latest
    '';
  };
in
make-run {
  inherit app;
}