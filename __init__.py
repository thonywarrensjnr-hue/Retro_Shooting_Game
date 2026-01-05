from .protocol import OpCode, GamePacket
from .room import GameRoom

__version__ = "1.0.0"
__author__ = "Jesse Jhonz INC"

__all__ = ["OpCode", "GamePacket", "GameRoom"]

import logging
logging.basicConfig(level=logging.INFO)
logging.info(f"Game package version {__version__} initialized.")
