# flake8: noqa

from typing import Optional, Callable

# Values
LOW = 0
HIGH = 1

# Modes
BCM = 11
BOARD = 10

# Pull
PUD_OFF = 20
PUD_DOWN = 21
PUD_UP = 22

# Edges
RISING = 31
FALLING = 32
BOTH = 33

# Functions
OUT = 0
IN = 1
SERIAL = 40
SPI = 41
I2C = 42
HARD_PWM = 43
UNKNOWN = -1

# Versioning
RPI_REVISION = 2
VERSION = '0.5.6'

def setmode(mode: int) -> None: ...

def setup(channel: int, state: int, initial: Optional[int] = None, pull_up_down: Optional[int] = None) -> None: ...

def output(channel: int, state: int) -> None: ...

def input(channel: int) -> int: ...

def cleanup(channel: Optional[int] = None) -> None: ...

def setwarnings(state: bool) -> None: ...

def add_event_detect(channel: int, edge: int, callback: Callable[[int], None], bouncetime: Optional[int] = None) -> None: ...

def remove_event_detect(channel: int) -> None: ...

def event_detected(channel: int) -> bool: ...

def wait_for_edge(channel: int, edge: int, timeout: Optional[int] = None) -> None: ...

def gpio_function(channel: int) -> int: ...
