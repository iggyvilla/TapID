from utils.responses import PluginResponse
from utils.parse_payload import TapAPIRequestPayload
from plugins.plugin_utils import attendance_utils
import psycopg2.errors


event_name = "attendance"


def run(jwt_decoded: dict, payload_data: TapAPIRequestPayload, args, conn) -> PluginResponse:
    try:
        attendance_utils.insert_into_attendance_logs(jwt_decoded["name"], payload_data.uid, conn)
        return PluginResponse(200, payload={"msg": "ok"})
    except psycopg2.errors.Error:
        return PluginResponse(500, payload={"msg": "internal server database error"})
