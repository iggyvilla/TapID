from utils.responses import PluginResponse
from utils.parse_payload import TapAPIRequestPayload
from plugins.plugin_utils import attendance_utils
from datetime import datetime
import psycopg2.errors


event_name = "attendance"


def run(jwt_decoded: dict, payload_data: TapAPIRequestPayload, args, conn) -> PluginResponse:
    try:
        attendance_utils.insert_into_attendance_logs(jwt_decoded["name"], payload_data.uid, conn)
        # Format time to Day (name) Day (number) Hour (24-hour):minute
        return PluginResponse(200, payload={"msg": "ok", "data": {"time_now": datetime.now().strftime("%a %d %H:%I")}})
    except psycopg2.errors.Error:
        return PluginResponse(500, payload={"msg": "internal server database error"})
