import httplib2
import os
import psycopg2.errors
import logging
from utils.responses import PluginResponse
from googleapiclient.discovery import build
from plugins.plugin_utils import library_utils
from utils.parse_payload import TapAPIRequestPayload

_log = logging.getLogger("main.logger")

event_name = "borrow_book"


# Edit with spreadsheet ID and it has to be public (i.e., "Anyone with the link can edit")
# If you don't want that, modify the code to use OAuth 2.0
#  see https://developers.google.com/sheets/api/quickstart/python
SPREADSHEET_ID = "12mlNwnZBP7GxGX5OJ0oCd19DcYDErBRVncyljzSwiwI"

# The Google Sheets REST API
discovery_url = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
service = build(
    'sheets',
    'v4',
    http=httplib2.Http(),
    discoveryServiceUrl=discovery_url,
    developerKey=os.environ['GAPIKEY']
)


def run(jwt_decoded: dict, payload_data: TapAPIRequestPayload, args, conn) -> PluginResponse:
    data = payload_data.event_data
    try:
        added_row = library_utils.borrow_book(
            uid=payload_data.uid,
            book_id=data['book_id'],
            due_on=data['due_on'],
            conn=conn
        )
    except KeyError:
        return PluginResponse(response_code=400, payload={"msg": "invalid data"})
    except psycopg2.errors.Error:
        return PluginResponse(response_code=500, payload={"msg": "internal server error"})

    if data['save_to_google_docs']:
        req = service.spreadsheets().values().append(
            SPREADSHEET_ID,
            range="borrow_log!A1:D1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={
                "values": [
                    # Borrow no.   Book Title	 Student Name	      Due When
                    (added_row[0], added_row[1], jwt_decoded['name'], added_row[2])
                ]
            }
        )
        resp = req.execute()
        _log.debug(f"Google API resp: {resp}")
        return PluginResponse(response_code=200, payload={"resp": resp})

    return PluginResponse(response_code=200, payload={"msg": "ok"})
