# Made by Enrique Villa, Grade 12 Da Vinci, SY 2022-2023

import logging
import os
import utils
import argparse
import psycopg2
import jwt.exceptions
from datetime import datetime as dt
from utils.responses.PluginResponse import PluginResponse
from utils.responses.PluginAbort import PluginAbort
from flask import Flask, Response, request, abort, jsonify

# Set up the Flask server
# A good Flask tutorial: https://www.youtube.com/watch?v=Z1RJmh_OqeA&t=2358s
# (P.S. freeCodeCamp is an amazing resource! I, as a fellow nerd, recommend most of their tutorials)
app = Flask(__name__)

# Grab command-line arguments
# This way, when launching the server, certain configurations can be made when launching the python file using
# the python command (ex. python3.9 main.py --level 1)
# Read more: https://docs.python.org/2/library/argparse.html#module-argparse
parser = argparse.ArgumentParser(
    description="Meet the TapID authentication server, TapAPI. Run with arguments or none to use default settings."
)

parser.add_argument('-l', '--level',
                    dest='level',
                    help='Set logging level (1-5)',
                    action='store',
                    default=1,
                    type=int)

parser.add_argument('-p', '--port',
                    dest='port',
                    help='Change web port TapAPI will run in',
                    action='store',
                    required=True,
                    type=utils.port_type)

parser.add_argument('-user', '--db-user',
                    dest='dbuser',
                    help='PostgreSQL user password',
                    required=True,
                    action='store_true')

parser.add_argument('-pass', '--db-password',
                    dest='dbpass',
                    help='PostgreSQL database password',
                    required=True,
                    action='store_true')

args = parser.parse_args()

# Next, setup logging (equivalent to printing, but syntactically makes easier to read code and logs)
# For instance, here we set it up to send to console AND a text file with the name as the date
# This way, if the server crashes, we still have a text file to read and see the cause of crash
#  and determine where the server stopped

# Make filename using datetime library (string FORMAT time method, hence strftime! NOT strptime!)
# Good resource - https://strftime.org
# Will show up as Jan_01_01_00_AM.txt, for example (based on system clock)
filename = str(dt.now().strftime("%b_%d_%I_%M_%p")) + ".txt"

# LOGGER SETUP
log = logging.getLogger('main.logger')

# Logging has different levels (NOTESET, DEBUG, INFO, WARNING, ERROR, CRITICAL)
# Depending on how we set it up, then the server will spit out more or less information
# We use a ternary operator here (read more: https://www.geeksforgeeks.org/ternary-operator-in-python/)
log_level = args.level * 10 if args.level % 10 == 0 and args.level <= 50 else 10
log.setLevel(log_level)

# Handlers tell the logger where to spit out the logs
# In this case, we tell it to send it to a log file (via FileHandler) and the console (via StreamHandler)
tapapi_logging_format = ' %(asctime)s  %(filename)-10s  [%(levelname)8s]  %(message)s '

streamhandler = logging.StreamHandler()
streamhandler.setFormatter(logging.Formatter(tapapi_logging_format))

filehandler = logging.FileHandler(os.path.join("logs/", filename))
filehandler.setFormatter(logging.Formatter(tapapi_logging_format))
filehandler.setLevel(log_level)

log.addHandler(filehandler)
log.addHandler(streamhandler)

log.debug('Logging and basic server setup complete! Re-run with -h or --help flag to see arguments')

log.info('Loading plugins...')
with open('config.json', 'r') as f:
    plugin_dict = utils.load_plugins(f=f, logger=log)

conn = psycopg2.connect(user=args.dbuser,
                        password=args.dbpass,
                        host="localhost",
                        port="5432",
                        database="tapid")


@app.route("/event", methods=["PUT"])
def route_event():
    payload = request.get_json()
    log.info(f'Received PUT request with payload, (keys: {", ".join(list(payload.keys()))}).')
    try:
        payload_data = utils.parse_payload(payload)
    except KeyError:
        log.warning('400: Invalid payload.')
        abort(Response("Invalid payload. Follow the format detailed in the GitHub page.", 400))
        return

    # If the payload is in the correct format, get the UID's public key
    public_key = utils.authentication.get_public_key_from_uid(
        uid=payload_data.uid,
        conn=conn,
        save_priv_key_on_new_uid=True
    )

    try:
        # Verify the attached JWT with the public key associated with the UID
        jwt_decoded = utils.authentication.verify_jwt_with_public_key(
            json_web_token=payload_data.jwt,
            public_key=bytes(public_key, 'utf-8')
        )

        event_func = plugin_dict.get(payload_data.event_name, None)

        if event_func:
            resp = event_func(jwt_decoded=jwt_decoded, event_data=payload_data.event_data, args=args)

            if type(resp) == PluginResponse:
                log.info(f'Received PluginResponse from \"{payload_data.event_name}\"')
                return jsonify(resp.payload), resp.response_code
            elif type(resp) == PluginAbort:
                return abort(Response(resp.reason, resp.response_code))
            else:
                log.critical('Invalid plug-in return type. TapAPI plug-ins should only return a PluginResponse.')
                return Response('Invalid plug-in return type.', 501)

    except jwt.exceptions.InvalidSignatureError:
        # If the card doesn't decrypt properly, something suspicious is up
        log.critical(f'Invalid signature detected. Investigate card {payload_data.uid} immediately!')
        abort(Response("Invalid signature. Card UID does not decrypt properly.", 403))


if __name__ == '__main__':
    log.warning(f'Running TapAPI on port {args.port}, debug level {args.level}')
    # If you ever want to test the server on the same machine, do a requests.put on http://localhost:<port>
    app.run(debug=True, port=args.port)
