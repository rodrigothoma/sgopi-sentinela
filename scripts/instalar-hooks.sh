#!/usr/bin/env bash
# Ativa os hooks versionados em .githooks/ neste clone (rodar uma vez após o git clone).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks
chmod +x .githooks/*
echo "Hooks ativados: $(ls .githooks | tr '\n' ' ')"
