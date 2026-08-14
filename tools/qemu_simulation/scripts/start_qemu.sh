#!/bin/bash
# start_qemu.sh
# Starts QEMU in the background for CI/CD automation.

# Default variables
IMAGE_PATH=$1
QEMU_PID_FILE="qemu.pid"
QMP_PORT=${2:-4444}
REDFISH_PORT=${3:-2443}
SSH_PORT=${4:-2222}

if [ -z "$IMAGE_PATH" ]; then
  echo "Error: Must provide the path to the OpenBMC ROM image."
  echo "Usage: ./start_qemu.sh <path_to_image> [qmp_port] [redfish_port] [ssh_port]"
  exit 1
fi

if [ ! -f "$IMAGE_PATH" ]; then
  echo "Error: Image file not found at $IMAGE_PATH"
  exit 1
fi

echo "Starting QEMU in background..."
echo "Image: $IMAGE_PATH"
echo "QMP Port: $QMP_PORT | Redfish Port: $REDFISH_PORT | SSH Port: $SSH_PORT"

# The critical flags here are:
# -daemonize : Run in background
# -pidfile   : Save the PID so we can kill it later
qemu-system-arm -m 1024 \
  -M witherspoon-bmc,fmc-model=mx66l51235f \
  -nographic \
  -drive file="$IMAGE_PATH",format=raw,if=mtd \
  -net nic \
  -net user,hostfwd=:127.0.0.1:${SSH_PORT}-:22,hostfwd=:127.0.0.1:${REDFISH_PORT}-:443,hostname=qemu \
  -qmp tcp:localhost:${QMP_PORT},server,nowait \
  -daemonize \
  -pidfile $QEMU_PID_FILE

if [ $? -eq 0 ]; then
  echo "QEMU started successfully. PID saved to $QEMU_PID_FILE"
else
  echo "Failed to start QEMU."
  exit 1
fi

# In a CI environment, bmcweb needs time to start up before Redfish APIs are available.
# We add a smart polling loop to wait for the API to become responsive.
echo "Waiting for Redfish API to become available on port $REDFISH_PORT (Timeout: 180s)..."
MAX_RETRIES=36
RETRY_INTERVAL=5

for i in $(seq 1 $MAX_RETRIES); do
  # Use curl to ping the Systems endpoint. -k ignores self-signed certs.
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k -u root:0penBmc https://127.0.0.1:${REDFISH_PORT}/redfish/v1/Systems)

  if [ "$HTTP_CODE" == "200" ]; then
    echo "Redfish API is UP! QEMU environment is ready for testing."
    exit 0
  fi
  echo "Attempt $i/$MAX_RETRIES: API not ready yet (HTTP $HTTP_CODE)... waiting ${RETRY_INTERVAL}s"
  sleep $RETRY_INTERVAL
done

echo "Error: Timed out waiting for Redfish API to start."
# Clean up since the environment is broken
./stop_qemu.sh
exit 1
