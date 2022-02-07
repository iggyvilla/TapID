import importlib
import json
from typing import Dict, TextIO, Callable, Tuple


def load_plugins(f: TextIO, logger) -> Tuple[Dict[str, Callable], dict]:
    """ Load the plug-ins via the config.json file and importlib """
    plugin_dict = {}

    config = json.load(f)

    for count, plugin in enumerate(config["plugins"]):
        try:
            plugin = importlib.import_module(plugin)
            plugin_dict[plugin.event_name] = plugin.run
            logger.info(f'Successfully loaded plugin "{plugin.event_name}" ({count+1}/{len(config["plugins"])})')
        except ModuleNotFoundError as e:
            logger.critical(f'{e}. Recheck your config.json setup or is the plug-in in the /plugins directory?')
        except AttributeError as e:
            logger.critical(f'{e}. Recheck your plug-in setup, make sure it meets the requirements in the wiki.')

    return plugin_dict, config
