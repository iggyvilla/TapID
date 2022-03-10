from utils.responses import PluginResponse
from utils.parse_payload import TapAPIRequestPayload

event_name = "attendance"


def run(jwt_decoded: dict, payload_data: TapAPIRequestPayload, args, conn) -> PluginResponse:
