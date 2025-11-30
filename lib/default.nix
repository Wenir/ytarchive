{
  buildPythonPackage
, hatchling
, yt-dlp
, boto3
, cryptography
, to_file_like_obj
, python-dotenv
, psycopg
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
  ];

  doCheck = false;

  pythonImportsCheck = [ "ytarchive_lib" ];
}