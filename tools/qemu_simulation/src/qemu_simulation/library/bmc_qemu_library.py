from robot.api.deco import library, keyword

from qemu_simulation.clients.qmp_client import QMPClient
from qemu_simulation.clients.redfish_client import RedfishClient
from qemu_simulation.simulation.virtual_cpld import VirtualCpld


@library(scope="GLOBAL", version="1.0")
class BmcQemuLibrary:
    """
    A Robot Framework custom library for OpenBMC QEMU simulation.
    It bridges high-level test keywords to low-level QMP and Redfish controls.
    """

    def __init__(self):
        self.qmp = None
        self.redfish = None

    @keyword("Connect To QEMU Simulation")
    def connect_to_qemu_simulation(
        self,
        qmp_host="127.0.0.1",
        qmp_port=4444,
        redfish_host="127.0.0.1",
        redfish_port=2443,
        bmc_username="root",
        bmc_password="0penBmc",
    ):
        """
        Initializes connections to both the QEMU QMP socket and the OpenBMC Redfish API.
        Must be called in Suite Setup.
        """
        self.qmp = QMPClient(host=qmp_host, port=int(qmp_port))
        self.qmp.connect()

        self.redfish = RedfishClient(
            host=redfish_host,
            port=int(redfish_port),
            username=bmc_username,
            password=bmc_password,
        )
        # Using print here instead of logging, as Robot Framework captures print statements into its HTML log
        print(
            f"Connected to QMP on port {qmp_port} and Redfish on port {redfish_port}."
        )

    @keyword("Disconnect From QEMU Simulation")
    def disconnect_from_qemu_simulation(self):
        """
        Closes the QMP socket connection.
        Must be called in Suite Teardown.
        """
        if self.qmp:
            self.qmp.disconnect()
            print("Disconnected from QMP.")

    @keyword("Get Bmc Power State")
    def get_bmc_power_state(self):
        """
        Queries and returns the current power state of the BMC via Redfish.
        Returns 'On' or 'Off'.
        """
        if not self.redfish:
            raise RuntimeError(
                "RedfishClient is not initialized. Call 'Connect To QEMU Simulation' first."
            )

        state = self.redfish.get_power_state()
        print(f"Current BMC Power State: {state}")
        return state

    @keyword("Trigger Redfish Power On")
    def trigger_redfish_power_on(self):
        """
        Sends a Redfish command to initiate the chassis power on sequence.
        """
        if not self.redfish:
            raise RuntimeError("RedfishClient is not initialized.")

        print("Sending Power On command via Redfish...")
        self.redfish.trigger_power_on()

    @keyword("Trigger Redfish Power Off")
    def trigger_redfish_power_off(self):
        """
        Sends a Redfish command to forcefully power off the chassis.
        """
        if not self.redfish:
            raise RuntimeError("RedfishClient is not initialized.")

        print("Sending ForceOff command via Redfish...")
        self.redfish.trigger_power_off()

    @keyword("Simulate Cpld Power Sequence")
    def simulate_cpld_power_sequence(self, timeout=10.0):
        """
        Acts as the virtual CPLD. Polls QEMU for the Power_Button (GPIOD0) assertion,
        simulates a motherboard boot delay, and asserts the PGOOD (GPIOD6) signal.
        Fails the test if the Power_Button is not asserted within the timeout.
        """
        if not self.qmp:
            raise RuntimeError("QMPClient is not initialized.")

        cpld = VirtualCpld(self.qmp)

        print(f"Waiting up to {timeout}s for BMC to assert Power_Button (GPIOD0)...")
        cpld.wait_for_power_button(timeout)

        print("Simulating physical motherboard boot delay (1.5s)...")
        cpld.assert_pgood()
        print("Asserted PGOOD signal (GPIOD6) High.")
