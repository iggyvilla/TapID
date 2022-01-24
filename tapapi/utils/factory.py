import importlib
import json
import logging
from types import ModuleType
from typing import Dict, TextIO


def load_plugins(f: TextIO, logger) -> Dict[str, ModuleType]:
    plugin_dict = {}

    config = json.load(f)

    for count, plugin in enumerate(config["plugins"]):
        try:
            plugin = importlib.import_module(plugin)
            plugin_dict[plugin.event_name] = plugin.run
            logger.info(f'Successfully loaded plugin {plugin.event_name} ({count+1}/{len(config["plugins"])})')
        except ModuleNotFoundError as e:
            logger.critical(f'{e}. Recheck your config.json setup, or is the plug-in in the /plugins directory?')

    return plugin_dict


if __name__ == '__main__':
    p_dict = load_plugins()
    print(p_dict)
