{
  buildPythonApplication
, setuptools
, wheel
}:
{
  app_name
, runtimeInputs ? []
, propagatedBuildInputs ? []
}:
buildPythonApplication {
  meta.mainProgram = app_name;
  pname = app_name;

  version = "1.0.0";
  pyproject = true;

  src = ../apps + "/${app_name}";

  nativeBuildInputs = [
    setuptools
    wheel
  ];

  propagatedBuildInputs = [] ++ propagatedBuildInputs ++ runtimeInputs;
}