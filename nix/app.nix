{
  writeShellApplication
, mypython
, app_name
, runtimeInputs ? []
}:
writeShellApplication {
  name = "${app_name}-app";

  runtimeInputs = [] ++ runtimeInputs;

  text = ''
    ${mypython}/bin/python ${../worker}/${app_name}.py "$@"
  '';
}