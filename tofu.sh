#!/usr/bin/env bash

cd tofu

nix run ".#tofu" -- "$@"