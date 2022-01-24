class PluginResponse:
    """
    Response class to handle plug-in responses
    Works with just a response code or return a payload
    """
    def __init__(self, response_code: int, payload: dict = {}, abort: bool = False):
        self.response_code = response_code
        self.payload_response = payload
        self.abort = abort

    @property
    def has_payload(self):
        return bool(self.payload_response)
