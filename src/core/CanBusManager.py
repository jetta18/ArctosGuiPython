"""
This module provides CAN bus management functionality for the Arctos robotic arm.
It handles the initialization and management of the CAN bus interface.
"""

import platform
import subprocess
import logging
from typing import Optional

import can

logger = logging.getLogger(__name__)

class CanBusManager:
    """
    Manages the CAN bus interface for the Arctos robotic arm.
    
    This class handles the initialization and management of the CAN bus interface,
    including checking interface status and providing access to the bus object.
    """
    
    def __init__(self):
        """
        Initialize the CanBusManager with the specified interface and bitrate.
        """

        if platform.system() == "Windows":
            can_interface = "COM5"  # or load from config file
        else:
            can_interface = "can0"
        self.can_interface = can_interface
        self.bitrate = 500000
        self.bus = None
    
    def is_interface_up(self) -> bool:
        """
        Check if the CAN interface is active.
        
        On Windows, checks if the COM port is available in the list of serial ports.
        On Linux, uses the `ip link show` command to check if the interface is up.
        
        Returns:
            bool: True if the interface is active, False otherwise.
        """
        if platform.system() == "Windows":
            # On Windows, check if the COM port is available
            import serial.tools.list_ports
            ports = [port.device for port in serial.tools.list_ports.comports()]
            return self.can_interface in ports
        else:
            try:
                result = subprocess.run(
                    ["ip", "link", "show", self.can_interface],
                    capture_output=True,
                    text=True
                )
                return "UP" in result.stdout
            except Exception as e:
                logger.error(f"Error checking CAN interface: {e}")
                return False
    
    def initialize(self) -> can.Bus:
        """
        Initialize the CAN bus interface.
        
        Returns:
            can.Bus: The initialized CAN bus object.
            
        Raises:
            RuntimeError: If the CAN interface is not available or if there is an error 
                       initializing the CAN bus.
        """
        if not self.is_interface_up():
            if platform.system() == "Windows":
                raise RuntimeError(f"CAN interface is not available on {self.can_interface}.")
            else:
                raise RuntimeError("CAN interface is not active. Please run 'setup_canable.sh' first.")

        try:
            if platform.system() == "Windows":
                self.bus = can.interface.Bus(
                    bustype="slcan",
                    channel=self.can_interface,
                    bitrate=self.bitrate
                )
            else:
                self.bus = can.interface.Bus(
                    bustype="socketcan",
                    channel=self.can_interface
                )

            logger.info(f"CAN bus successfully initialized on {self.can_interface} with bitrate {self.bitrate}.")
            return self.bus
            
        except Exception as e:
            logger.error(f"Error initializing CAN bus: {e}")
            raise RuntimeError(f"Error initializing CAN bus: {e}")
    
    def get_bus(self) -> Optional[can.Bus]:
        """
        Get the CAN bus instance.
        
        Returns:
            Optional[can.Bus]: The CAN bus instance if initialized, None otherwise.
        """
        return self.bus
    
    def shutdown(self):
        """
        Clean up and shut down the CAN bus interface.
        """
        if self.bus is not None:
            try:
                self.bus.shutdown()
                logger.info("CAN bus interface has been shut down.")
            except Exception as e:
                logger.error(f"Error shutting down CAN bus: {e}")
