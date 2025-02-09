{
  description = "A basic flake with a shell";
  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; config.allowUnfree = false; };
        lib = pkgs.lib;

        to_file_like_obj = pkgs.python3Packages.callPackage ./nix/to_file_like_obj.nix {};

        python = pkgs.python3.withPackages (
          ps: [
            ps.yt-dlp
            ps.python-dotenv
            ps.cryptography
            ps.boto3
            to_file_like_obj
            #pytest #pyzmq #pyqt5 #opencv4 #scikit-image #paramiko #pandas #seaborn #flask #pytz #pyserial #requests #pyyaml #requests-cache #matplotlib #numpy #shapely #cdt
          ]
        );

        make-docker-push = pkgs.callPackage ./nix/make-docker-push.nix {};
        make-docker-run = pkgs.callPackage ./nix/make-docker-run.nix {};
        make-run = pkgs.callPackage ./nix/make-run.nix {};

        make_app = app_name: runtimeInputs: rec {
          app = pkgs.callPackage ./nix/app.nix { mypython = python; app_name = app_name; inherit runtimeInputs; };
          image = pkgs.callPackage ./nix/image.nix { app = app; };
          push = make-docker-push { name = app_name + "-app"; image = image; };
          docker-run = make-docker-run { name = app_name + "-app"; image = image; };
          run = make-run { app = app; };
        };

        #main = pkgs.writeShellApplication {
        #  name = "main";
        #  runtimeInputs = [ pkgs.ffmpeg ];
        #  text = ''
        #    ${python}/bin/python ${./worker/main.py}
        #  '';
        #};
      in
      rec {
        apps.tofu = {
          type = "app";
          program = "${pkgs.opentofu}/bin/tofu";
        };
        apps.nom = {
          type = "app";
          program = "${pkgs.nix-output-monitor}/bin/nom";
        };
        legacyPackages = rec {
          playlist = make_app "playlist" [];
          download = make_app "download" [ pkgs.ffmpeg ];
          decrypt_local = pkgs.callPackage ./nix/app.nix { mypython = python; app_name = "decrypt_local"; };
          #docker-push-playlist = make-docker-push { name = "playlist-app"; image = playlist-image; };
          #docker-run-playlist = make-docker-run { name = "playlist-app"; image = playlist-image; };


          pushall = pkgs.writeShellApplication {
            name = "pushall";
            text = ''
              ${pkgs.lib.getExe playlist.push}
              ${pkgs.lib.getExe download.push}
            '';
          };



          #build_main = pkgs.writeShellScriptBin "build_main" ''
          #  nix build .#main_docker && docker load < result
          #'';
          #run_main = pkgs.writeShellScriptBin "run_main" ''
          #  source .env

          #  ${pkgs.docker}/bin/docker run --rm -it \
          #      --env AWS_DEFAULT_REGION=us-east-1 \
          #      --env AWS_ACCESS_KEY_ID="$APP_KEY" \
          #      --env AWS_SECRET_ACCESS_KEY="$APP_SECRET" \
          #      --env DATA_KEY="$DATA_KEY" \
          #      --env DATA_IV="$DATA_IV" \
          #      --workdir /work   main_docker:latest
          #'';

        };



        devShells.default = pkgs.mkShell {
          packages = [ 
            python
            pkgs.ffmpeg
          ];
          #pkgs.opentofu #pkgs.awscli2 #pkgs.gcc #pkgs.gdb #pkgs.arduino-ide #pkgs.valgrind #pkgs.cmake #pkgs.hiredis #pkgs.zeromq #pkgs.curl #pkgs.boost183 #pkgs.redis #pkgs.libuuid #pkgs.pkg-config #pkgs.makeWrapper #pkgs.boost
        };
      });
}



          #docker-login = pkgs.writeShellApplication {
          #  name = "docker-login";
          #  text = ''
          #    ${pkgs.docker}/bin/docker login -u AWS -p $(aws ecr get-login-password --region us-east-1)
          #  '';
          #};