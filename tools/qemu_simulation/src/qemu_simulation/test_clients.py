import time
import logging
from qmp_client import QMPClient
from redfish_client import RedfishClient

# Setup basic logging to trace the sequence
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("IntegrationTest")


def main():
    # Initialize clients. Update the password to match your BMC root password.
    qmp = QMPClient()
    redfish = RedfishClient(username="admin", password="0penBmc")

    try:
        # 1. Connect to QEMU's QMP socket
        qmp.connect()

        # 2. Check initial power state. If it's already On, force it Off first.
        initial_state = redfish.get_power_state()
        if initial_state == "On":
            logger.info(
                "System is currently On. Sending ForceOff to reset the test environment..."
            )
            redfish.trigger_power_off()
            logger.info("Waiting 5 seconds for BMC state to settle...")
            time.sleep(5)

        logger.info("--- Starting Power Sequence Test ---")

        # 3. Trigger Power On via Redfish API
        redfish.trigger_power_on()

        # 4. Polling QMP for Power_Button (GPIOD0) assertion
        # Note: In OpenBMC, pressing the power button usually pulls the GPIO Low (False/0).
        timeout = 10.0
        start_time = time.time()
        button_asserted = False

        logger.info("Polling QEMU for Power_Button (GPIOD0) signal...")
        while (time.time() - start_time) < timeout:
            # We assume the property is named "gpio-d0". Adjust if qom-list showed differently.
            btn_val = qmp.qom_get("/machine/soc/gpio", "gpioD0")

            # Check if the signal went Low
            if btn_val is False or btn_val == 0:
                logger.info("Detected Power_Button signal pulled Low by BMC!")
                button_asserted = True
                break

            time.sleep(0.5)

        if not button_asserted:
            raise TimeoutError(
                "BMC did not pull down the Power_Button within the timeout period."
            )

        # 5. Simulate the physical delay of a motherboard powering up
        logger.info("Simulating motherboard boot delay (1.5 seconds)...")
        time.sleep(1.5)

        # 6. Send Power Good (PGOOD) signal back via QMP (GPIOD6)
        logger.info("Sending PGOOD signal (GPIOD6) to HIGH...")
        qmp.qom_set("/machine/soc/gpio", "gpioD6", True)

        # 7. Wait for OpenBMC's State Manager to process the GPIO change
        logger.info("Waiting 3 seconds for BMC to sync D-Bus state...")
        time.sleep(3)

        # 8. Verify the final power state via Redfish
        final_state = redfish.get_power_state()
        if final_state == "On":
            logger.info("TEST PASSED: End-to-End Power Sequence Successful!")
        else:
            logger.error(
                f"TEST FAILED: Expected PowerState 'On', but got '{final_state}'"
            )

    except Exception as e:
        logger.error(f"Test aborted due to error: {e}")
    finally:
        qmp.disconnect()


if __name__ == "__main__":
    main()
