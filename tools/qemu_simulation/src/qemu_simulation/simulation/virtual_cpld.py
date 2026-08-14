import time
import logging


class VirtualCpld:
    """
    Simulates the virtual CPLD hardware handshake against QEMU's QMP.

    Owns the QOM GPIO path, the pin names, and the power-sequence timing so
    that callers never touch those details.
    """

    GPIO_PATH = "/machine/soc/gpio"
    POWER_BUTTON_PIN = "gpioD0"
    PGOOD_PIN = "gpioD6"
    BOOT_DELAY_SECONDS = 1.5

    def __init__(self, qmp):
        self.qmp = qmp
        self.logger = logging.getLogger(__name__)

    def wait_for_power_button(self, timeout=10.0):
        """
        Polls QMP until the BMC asserts Power_Button (pulled Low), or raises
        AssertionError if the timeout elapses first.
        """
        timeout = float(timeout)
        start_time = time.time()
        button_asserted = False

        while (time.time() - start_time) < timeout:
            btn_val = self.qmp.qom_get(self.GPIO_PATH, self.POWER_BUTTON_PIN)

            if btn_val is False or btn_val == 0:
                self.logger.info("Detected Power_Button signal pulled Low by BMC.")
                button_asserted = True
                break

            time.sleep(0.5)

        if not button_asserted:
            raise AssertionError(
                f"Timeout: BMC did not pull down Power_Button within {timeout} seconds."
            )

    def assert_pgood(self):
        """
        Simulates the motherboard boot delay, then asserts PGOOD High.
        """
        time.sleep(self.BOOT_DELAY_SECONDS)
        self.qmp.qom_set(self.GPIO_PATH, self.PGOOD_PIN, True)
