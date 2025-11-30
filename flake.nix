{
  description = "A basic flake with a shell";
  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = false;
          overlays = [ (import ./nix/overlay.nix) ];
        };

        python-libs = ps: [
          #ps.yt-dlp
          #ps.cryptography
          #ps.boto3
          #ps.to_file_like_obj
          ps.ytarchive_lib
          #ps.psycopg
        ];

        python = pkgs.python3.withPackages python-libs;
      in
      rec {
        legacyPackages = rec {
          playlist = pkgs.make-bundle {
            app_name = "playlist";
            inherit python-libs;
          };

          download = pkgs.make-bundle {
            app_name = "download";
            inherit python-libs;
            runtimeInputs = [ pkgs.ffmpeg pkgs.deno ];
          };

          decrypt_local = pkgs.make-run {
            app = pkgs.make-app {
              app_name = "decrypt_local";
              propagatedBuildInputs = python-libs pkgs.python3Packages;
            };
          };

          tests = pkgs.make-run { app = pkgs.callPackage ./tests {}; };

          pushall = pkgs.writeShellApplication {
            name = "pushall";
            text = ''
              ${pkgs.lib.getExe playlist.push}
              ${pkgs.lib.getExe download.push}
            '';
          };
        };

        devShells.default = pkgs.mkShell { packages = [ python pkgs.ffmpeg pkgs.deno pkgs.grafana-loki ]; };
        apps.tofu = { type = "app"; program = "${pkgs.opentofu}/bin/tofu"; };
      });
}

            # pkgs.ffmpeg
#pytest #pyzmq #pyqt5 #opencv4 #scikit-image #paramiko #pandas #seaborn #flask #pytz #pyserial #requests #pyyaml #requests-cache #matplotlib #numpy #shapely #cdt
#pkgs.opentofu #pkgs.awscli2 #pkgs.gcc #pkgs.gdb #pkgs.arduino-ide #pkgs.valgrind #pkgs.cmake #pkgs.hiredis #pkgs.zeromq #pkgs.curl #pkgs.boost183 #pkgs.redis #pkgs.libuuid #pkgs.pkg-config #pkgs.makeWrapper #pkgs.boost

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

        #main = pkgs.writeShellApplication {
        #  name = "main";
        #  runtimeInputs = [ pkgs.ffmpeg ];
        #  text = ''
        #    ${python}/bin/python ${./worker/main.py}
        #  '';
        #};
