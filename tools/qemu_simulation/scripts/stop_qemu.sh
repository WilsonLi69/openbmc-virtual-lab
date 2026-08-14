#!/bin/bash
# stop_qemu.sh
# Stops the background QEMU process cleanly.

QEMU_PID_FILE="qemu.pid"

if [ -f "$QEMU_PID_FILE" ]; then
  PID=$(cat $QEMU_PID_FILE)
  echo "Stopping QEMU (PID: $PID)..."

  # Send SIGTERM for graceful shutdown
  kill $PID

  # Wait for process to terminate
  while kill -0 $PID 2>/dev/null; do
    sleep 1
  done

  rm -f $QEMU_PID_FILE
  echo "QEMU successfully stopped and cleaned up."
else
  echo "No PID file found. Is QEMU running?"
fi
