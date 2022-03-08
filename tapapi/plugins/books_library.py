from plugins.plugin_utils import library_utils
from utils.parse_payload import TapAPIRequestPayload
import os
import logging
import psycopg2.errors
from utils.responses import PluginResponse
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


event_name = "borrow_book"
_log = logging.getLogger("main.logger")

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Sheets API code from https://developers.google.com/sheets/api/quickstart/python
# Edit with spreadsheet ID
SPREADSHEET_ID = '12mlNwnZBP7GxGX5OJ0oCd19DcYDErBRVncyljzSwiwI'
# Edit with the length of the first row of headers
RANGE_NAME = 'borrow_log!A1:D1'

creds = None

# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('plugins/token.json'):
    creds = Credentials.from_authorized_user_file('plugins/token.json', SCOPES)

# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'plugins/credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('plugins/token.json', 'w') as token:
        token.write(creds.to_json())


def run(jwt_decoded: dict, payload_data: TapAPIRequestPayload, args, conn) -> PluginResponse:
    data = payload_data.event_data
    try:
        db_entry = library_utils.borrow_book(
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
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        #               Borrow ID    Book Title   Student Name         Due When
        sheets_entry = (db_entry[0], db_entry[1], jwt_decoded["name"], db_entry[2].strftime("%A %b %d, %Y"))
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={
                "values": [sheets_entry]
            }
        ).execute()

        if result:
            return PluginResponse(response_code=200, payload={"google_resp": result, "entry": sheets_entry})
        else:
            return PluginResponse(response_code=500, payload={"msg": "google api error"})

    return PluginResponse(response_code=200, payload={"msg": "ok"})
