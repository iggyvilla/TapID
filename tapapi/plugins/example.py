from utils.responses import PluginResponse

event_name = "example_event"


def run(jwt_decoded: dict, event_data: dict, args) -> PluginResponse:
    return PluginResponse(response_code=200, payload={"hello": "world", "echo": event_data, "jwt_decoded": jwt_decoded})
