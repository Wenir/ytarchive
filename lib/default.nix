{
  buildPythonPackage
, hatchling
, yt-dlp
, boto3
, cryptography
, to_file_like_obj
, python-dotenv
, psycopg
, pyyaml
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
    yt-dlp
    boto3
    to_file_like_obj
    cryptography
    python-dotenv
    psycopg
    pyyaml
  ];

  doCheck = false;

  pythonImportsCheck = [ "ytarchive_lib" ];
}