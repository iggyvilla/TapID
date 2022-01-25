class PluginResponse:
    """
    Response class to handle plug-in responses
    Works with just a simple response code or return a payload
    """
    def __init__(self, response_code: int, payload: dict = {}):
        self.response_code = response_code
        self.payload = payload

    @property
    def has_payload(self):
        return bool(self.payload)
