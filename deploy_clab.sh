#!/bin/bash
set -e

echo "[INFO] Deploying Clabverter topology..."
sudo docker run --user $(id -u) -v $(pwd):/clabernetes/work --rm ghcr.io/srl-labs/clabernetes/clabverter --stdout --naming non-prefixed | kubectl apply -f -
