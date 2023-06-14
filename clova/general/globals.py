from clova.config.character import CHARACTER_CONFIG_PROMPT as GLOBAL_CHARACTER_CONFIG_PROMPT

from clova.config.character import CharacterProvider
from clova.config.config import ConfigurationProvider
from clova.general.queue import SpeechQueue
from clova.io.local.db import Database
from clova.io.local.led import IllminationLed
from clova.io.local.volume import VolumeController
from clova.io.network .debug_interface import RemoteInteractionInterface

global_config_prov = ConfigurationProvider()
global_speech_queue = SpeechQueue()
global_led_ill = IllminationLed()
global_db = Database()
global_debug_interface = RemoteInteractionInterface()
global_character_prov = CharacterProvider(global_config_prov, global_speech_queue)
global_vol = VolumeController(global_speech_queue)

__all__ = ['GLOBAL_CHARACTER_CONFIG_PROMPT', 'global_character_prov', 'global_config_prov', 'global_speech_queue', 'global_db', 'global_led_ill', 'global_vol', 'global_debug_interface']
