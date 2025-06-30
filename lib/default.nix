{
  buildPythonPackage
, hatchling
, boto3
, cryptography
, to_file_like_obj
}:
buildPythonPackage {
  pname = "ytarchive-lib";
  version = "1.0.0";

  src = ./.;

  format = "pyproject";

  nativeBuildInputs = [
    hatchling
  ];

  propagatedBuildInputs = [
    boto3
    to_file_like_obj
    cryptography
  ];

  doCheck = false;

  pythonImportsCheck = [ "ytarchive_lib" ];
}