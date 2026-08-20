#!/bin/bash

# =================================================================
# OpenBMC Generic GDB Remote Debug Launch Script
# =================================================================

# Basic settings
WORKSPACE="/home/wilsonli/openbmc/build/custom-board"
SDK_ENV="/usr/local/oecore-x86_64/environment-setup-arm1176jzs-openbmc-linux-gnueabi"
TARGET_TRIPLET="arm1176jzs-openbmc-linux-gnueabi"

# Argument parsing
PKG_NAME=$1
TARGET_IP_PORT=${2:-"127.0.0.1:1234"}

# Print Help
if [ -z "$PKG_NAME" ]; then
  echo "Usage: $0 <package-name> [target-IP:Port]"
  echo "Example: $0 phosphor-settings-manager"
  echo "Example: $0 x86-power-control 192.168.1.15:1234"
  exit 1
fi

# Start Launching GDB
echo "[1/4] Loading SDK environment variables..."
source "$SDK_ENV"
export LC_ALL=C.UTF-8

echo "[2/4] Locating debug file and source code for ${PKG_NAME}..."
PKG_WORK_DIR="${WORKSPACE}/tmp/work/${TARGET_TRIPLET}/${PKG_NAME}"

DEBUG_BIN=$(find "$PKG_WORK_DIR" -path "*/package/usr/bin/.debug/${PKG_NAME}" -type f | head -n 1)

if [ -z "$DEBUG_BIN" ]; then
  echo "Error: Could not find the executable with debug symbols! Please verify the package name or whether it has been compiled."
  exit 1
fi

SRC_GIT=$(find "$PKG_WORK_DIR" -maxdepth 2 -name "git" -type d | head -n 1)
SRC_BUILD=$(find "$PKG_WORK_DIR" -maxdepth 2 -name "build" -type d | head -n 1)

echo "  -> Executable: $DEBUG_BIN"
echo "  -> Source: $SRC_GIT"

echo "[3/4] Assembling GDB start up commands..."

GDB_OPTS=()

GDB_OPTS+=("-ex" "set sysroot $OECORE_TARGET_SYSROOT")

if [ -n "$SRC_GIT" ]; then
  GDB_OPTS+=("-ex" "dir $SRC_GIT")
fi

if [ -n "$SRC_BUILD" ]; then
  GDB_OPTS+=("-ex" "dir $SRC_BUILD")
fi

GDB_OPTS+=("-ex" "target remote $TARGET_IP_PORT")

GDB_OPTS+=("-ex" "echo \n=== Successfully connected to QEMU ===\n")

echo "[4/4] Launching GDB..."

$GDB "${GDB_OPTS[@]}" "$DEBUG_BIN"
