class PluginAbort:
    """Tell the plug-in handler that the plug-in is aborted"""
    def __init__(self, response_code: int, reason: str):
        self.response_code = response_code
        self.reason = reason
