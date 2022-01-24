from utils import PluginResponse

event_name = "example_event"


def run(payload: dict, args) -> PluginResponse:
    return PluginResponse(response_code=200, payload={"hello": "world"})
