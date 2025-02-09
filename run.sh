#!/usr/bin/env bash

cd tofu

nix run .#nom -- build "$1"
nix run "$@"