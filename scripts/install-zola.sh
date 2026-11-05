#!/usr/bin/env bash
# Downloads the pinned Zola release to .bin/zola, verifying its checksum.
# Idempotent: does nothing if .bin/zola already reports the pinned version.
set -euo pipefail

ZOLA_VERSION="0.23.6"
ZOLA_SHA256="8f5132b3522412d04e395e0b25f6d68613ad272a873e54a2b3ebf664873024a4"
ZOLA_TARBALL="zola-v${ZOLA_VERSION}-x86_64-unknown-linux-gnu.tar.gz"
ZOLA_URL="https://github.com/getzola/zola/releases/download/v${ZOLA_VERSION}/${ZOLA_TARBALL}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${REPO_ROOT}/.bin"
ZOLA_BIN="${BIN_DIR}/zola"

if [ -x "${ZOLA_BIN}" ] && "${ZOLA_BIN}" --version 2>/dev/null | grep -qx "zola ${ZOLA_VERSION}"; then
  exit 0
fi

mkdir -p "${BIN_DIR}"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

curl -sL -o "${WORK_DIR}/${ZOLA_TARBALL}" "${ZOLA_URL}"
echo "${ZOLA_SHA256}  ${WORK_DIR}/${ZOLA_TARBALL}" | sha256sum -c -
tar -xzf "${WORK_DIR}/${ZOLA_TARBALL}" -C "${WORK_DIR}"
mv "${WORK_DIR}/zola" "${ZOLA_BIN}"
chmod +x "${ZOLA_BIN}"

"${ZOLA_BIN}" --version
