final: prev: {
  make-app = prev.python3Packages.callPackage ./make-app.nix {};
  make-run = prev.callPackage ./make-run.nix {};
  make-image = prev.callPackage ./make-image.nix {};
  make-docker-push = prev.callPackage ./make-docker-push.nix {};
  make-docker-run = prev.callPackage ./make-docker-run.nix {};
  make-bundle = prev.callPackage ./make-bundle.nix {};

  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (python-final: python-prev: {
      to_file_like_obj = python-final.callPackage ./to_file_like_obj.nix {};
      ytarchive_lib = python-final.callPackage ../lib {};
    })
  ];
}