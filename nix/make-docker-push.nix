{
  writeShellApplication
, skopeo
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
  name = "docker-push-${name}";
  text = ''
    cd tofu
    endpoint="$("${tofu}" output --raw registry-endpoint)"
    key="$("${tofu}" output --raw registry-key)"

    ${lib.getExe skopeo} \
        --insecure-policy \
        copy \
        --dest-creds "nologin:$key" \
        "docker-archive://${image}" \
        "docker://$endpoint/${name}:latest"
  '';
}