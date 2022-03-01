from utils.responses import PluginResponse

event_name = "example_event"


def run(jwt_decoded: dict, payload_data, args, conn) -> PluginResponse:
    return PluginResponse(response_code=200, payload={"hello": "world", "echo": payload_data.event_data, "jwt_decoded": jwt_decoded})
