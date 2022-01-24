class PluginInterface:

    @staticmethod
    def event_name() -> None:
        """Name which triggers the event"""

    @staticmethod
    def run(payload: dict, args):
        """Code that will be run when event is called"""
