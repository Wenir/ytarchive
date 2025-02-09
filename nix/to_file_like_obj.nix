{ buildPythonPackage
, hatchling
, fetchPypi
, lib
}:
buildPythonPackage rec {
  pname = "to_file_like_obj";
  version = "0.0.6";

  buildInputs = [ hatchling ];

  src = fetchPypi {
    inherit pname version;
    sha256 = "sha256-r3WndQLH+Q0SP0FsF+vcZ+O/7P4vmRSWVre3UcM7Jwk=";
  };
  format = "pyproject";

  doCheck = false;

  meta = {
    homepage = https://github.com/uktrade/to-file-like-obj;
    description = "Python utility function to convert an iterable of bytes or str to a readable file-like object ";
    license = lib.licenses.mit;
    maintainers = [];
  };
}