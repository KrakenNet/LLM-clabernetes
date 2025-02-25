#!/bin/bash

# Exit immediately if a command fails
set -e

echo "[INFO] Deploying Clabverter topology..."

clabverter --stdout --naming non-prefixed | kubectl apply -f -

echo "[SUCCESS] Clabverter topology deployed!"
