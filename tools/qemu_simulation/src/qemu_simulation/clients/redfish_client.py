import requests
import urllib3
import logging

# Suppress insecure HTTPS request warnings for BMC self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RedfishClient:
    """
    A client to interact with the OpenBMC Redfish REST API.
    Handles basic authentication, self-signed certificates, and common system operations.
    """

    def __init__(
        self,
        host="127.0.0.1",
        port=2443,
        username="root",
        password="0penBmc",
        timeout=10.0,
    ):
        self.base_url = f"https://{host}:{port}"
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

        # Use a session to persist basic auth and SSL verification settings across requests
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.verify = False  # Ignore self-signed certificate warnings
        self.session.headers.update({"Content-Type": "application/json"})

    def _request(self, method, endpoint, payload=None):
        """
        Internal method to execute HTTP requests and handle exceptions.
        """
        url = f"{self.base_url}{endpoint}"
        self.logger.debug(f"Redfish {method} {url}")

        try:
            response = self.session.request(
                method=method, url=url, json=payload, timeout=self.timeout
            )
            response.raise_for_status()

            # Return JSON dictionary if content exists, else return empty dictionary (e.g., 204 No Content)
            return response.json() if response.content else {}

        except requests.exceptions.HTTPError as e:
            self.logger.error(
                f"HTTP Error: {e.response.status_code} - {e.response.text}"
            )
            raise
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise

    def get_power_state(self):
        """
        Queries the current power state of the system.
        Returns 'On' or 'Off'.
        """
        endpoint = "/redfish/v1/Systems/system"
        self.logger.info("Querying BMC power state...")

        response = self._request("GET", endpoint)
        state = response.get("PowerState", "Unknown")
        self.logger.info(f"Current power state: {state}")

        return state

    def trigger_power_on(self):
        """
        Sends a Redfish command to power on the system.
        """
        endpoint = "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset"
        payload = {"ResetType": "On"}
        self.logger.info("Triggering Power On via Redfish...")
        return self._request("POST", endpoint, payload=payload)

    def trigger_power_off(self):
        """
        Sends a Redfish command to forcefully power off the system.
        """
        endpoint = "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset"
        payload = {"ResetType": "ForceOff"}
        self.logger.info("Triggering Power Off via Redfish...")
        return self._request("POST", endpoint, payload=payload)
