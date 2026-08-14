import socket
import json
import time
import logging


class QMPClient:
    """
    A client to interact with QEMU Machine Protocol (QMP) via TCP sockets.
    Handles connection, handshake, and executing QOM (QEMU Object Model) commands.
    """

    def __init__(self, host="127.0.0.1", port=4444, timeout=5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._socket = None
        self.logger = logging.getLogger(__name__)

    def connect(self):
        """
        Establishes the socket connection and performs the initial QMP handshake.
        """
        self.logger.info(f"Connecting to QMP on {self.host}:{self.port}...")
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self.timeout)

        try:
            self._socket.connect((self.host, self.port))

            # 1. Receive the initial greeting from QEMU
            greeting = self._socket.recv(4096).decode("utf-8")
            if "QMP" not in greeting:
                raise ConnectionError("Invalid QMP greeting received.")

            # 2. Send 'qmp_capabilities' to exit negotiation mode and enter command mode
            self.execute("qmp_capabilities")
            self.logger.info("QMP connection established and capabilities negotiated.")

        except Exception as e:
            self.logger.error(f"Failed to connect to QMP: {e}")
            if self._socket:
                self._socket.close()
                self._socket = None
            raise

    def disconnect(self):
        """Closes the socket connection gracefully."""
        if self._socket:
            self.logger.info("Closing QMP connection.")
            self._socket.close()
            self._socket = None

    def execute(self, command, arguments=None):
        """
        Sends a QMP command and waits for the corresponding response.
        Ignores asynchronous QMP events during the wait.
        """
        if not self._socket:
            raise ConnectionError("Socket is not connected. Call connect() first.")

        payload = {"execute": command}
        if arguments:
            payload["arguments"] = arguments

        try:
            self._socket.sendall((json.dumps(payload) + "\n").encode("utf-8"))

            # Loop to read responses, ignoring asynchronous events
            while True:
                response_data = self._socket.recv(8192).decode("utf-8")

                # QMP may send multiple JSON objects in one stream, separated by newlines
                for line in response_data.splitlines():
                    if not line.strip():
                        continue

                    response = json.loads(line)

                    # Ignore asynchronous events
                    if "event" in response:
                        self.logger.debug(f"Ignored QMP event: {response['event']}")
                        continue

                    # Return the actual command response or raise error
                    if "error" in response:
                        error_desc = response["error"].get("desc", "Unknown QMP Error")
                        self.logger.error(f"QMP Error: {error_desc}")
                        raise RuntimeError(f"QMP Command Failed: {error_desc}")

                    if "return" in response:
                        return response["return"]

        except socket.timeout:
            self.logger.error(f"QMP command '{command}' timed out.")
            raise
        except Exception as e:
            self.logger.error(f"Error executing QMP command '{command}': {e}")
            raise

    def qom_get(self, path, property_name):
        """
        Reads a property value from a specified QOM path.
        """
        args = {"path": path, "property": property_name}
        self.logger.debug(f"Reading QOM property: {path} -> {property_name}")
        return self.execute("qom-get", args)

    def qom_set(self, path, property_name, value):
        """
        Writes a value to a specified QOM property.
        """
        args = {"path": path, "property": property_name, "value": value}
        self.logger.debug(f"Setting QOM property: {path} -> {property_name} = {value}")
        return self.execute("qom-set", args)
