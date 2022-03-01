from utils.responses import PluginResponse
from utils.parse_payload import TapAPIRequestPayload
from plugins.plugin_utils import canteen_utils

event_name = "canteen_event"


def run(jwt_decoded: dict, payload_data: TapAPIRequestPayload, args, conn) -> PluginResponse:
    uid = payload_data.uid
    event_data = payload_data.event_data

    old_bal = canteen_utils.get_balance_of_uid(conn, uid)

    if "action" not in event_data:
        return PluginResponse(400, payload={"msg": "Invalid dict"})

    if event_data["action"] == "subtract":
        new_bal = old_bal - event_data["bal"]
    elif event_data["action"] == "add":
        new_bal = old_bal + event_data["bal"]
    else:
        return PluginResponse(400, payload={"msg": "Invalid action"})

    # If there isn't enough balance
    if new_bal < 0:
        return PluginResponse(response_code=403, payload={"msg": "missing balance"})
    else:
        canteen_utils.update_balance_of_uid(conn, uid, new_bal=new_bal)
        return PluginResponse(response_code=200, payload={"msg": "success", "new_bal": new_bal})
