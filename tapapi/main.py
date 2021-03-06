# Made by Enrique Villa, Grade 12 Da Vinci, SY 2022-2023

import re
import logging
import utils
import psycopg2
from datetime import datetime
import jwt.exceptions
from os import environ
from datetime import datetime as dt
from plugins.plugin_utils.library_utils import get_books_from_uid
from utils.configure_logger import configure_logger
from utils.configure_argparse import configure_argparse
from utils.responses.PluginResponse import PluginResponse
from flask import Flask, Response, request, abort, jsonify, render_template

# Set up the Flask server
# A good Flask tutorial: https://www.youtube.com/watch?v=Z1RJmh_OqeA&t=2358s
#  (P.S. freeCodeCamp is an amazing resource! I, as a fellow nerd, recommend most of their tutorials)
app = Flask(__name__)

# Grab command-line arguments
# This way, when launching the server, certain configurations can be made when launching the python file using
# the python command (ex. python3.9 main.py --level 1)
# Read more: https://docs.python.org/2/library/argparse.html#module-argparse
parser = configure_argparse()
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
log = configure_logger(log=log, args=args, filename=filename)

log.debug('Logging and basic server setup complete! Re-run with -h or --help flag to see arguments')

log.info('Loading plugins...')
with open('config.json', 'r') as f:
    plugin_dict, config_dict = utils.load_plugins(f=f, logger=log)


def create_connection():
    return psycopg2.connect(user=args.dbuser,
                            password=args.dbpass,
                            host="localhost",
                            port="5432",
                            database="tapid")


if not utils.is_db_valid(create_connection()):
    logging.critical("Database is invalid! Are you sure it has the proper tables? Consider running "
                     "extras/make_databases.py")
    exit()


@app.route('/')
def home_page():
    payload = {
        "api_version": config_dict.get('version', 'unknown'),
        "status": "online"
    }
    return jsonify(payload), 200


@app.route("/event", methods=["PUT", "POST"])
def route_event():
    payload = request.get_json()

    try:
        log.info(f'Received POST/PUT request with payload, (keys: {", ".join(list(payload.keys()))}).')
        payload_data = utils.parse_payload(payload)
    except (KeyError, AttributeError):
        log.warning('400: Invalid payload.')
        abort(Response("Invalid payload. Follow the format detailed in the GitHub page.", 400))
        return

    conn = create_connection()

    # If the payload is in the correct format, get the UID's public key
    public_key = utils.authentication.get_public_key_from_uid(
        uid=payload_data.uid,
        conn=conn
    )

    try:
        # Verify (decrypt) the attached JWT with the public key associated with the UID
        jwt_decoded = utils.authentication.verify_jwt_with_public_key(
            json_web_token=payload_data.jwt,
            public_key=bytes(public_key, 'utf-8')
        )
        log.info(f'Successfully authenticated \"{payload_data.uid}\"s JWT! Checking validity...')

        # Check if the JWT is valid (has the right format)
        if not utils.is_jwt_valid(jwt_decoded=jwt_decoded):
            log.critical(f"Invalid JWT detected from {payload_data.uid}!")
            return Response("Invalid JWT.", 400)

        log.info('JWT is valid.')

        # Check if the password present in the JWT is correct
        if jwt_decoded["pass"] != environ.get("TAPID_JWT_PASSWORD", None):
            log.critical(f"Invalid password detected from {payload_data.uid}!")
            return Response("Invalid password.", 401)

        log.info('Correct pass in JWT.')

        # Now grab the run() function of the event being requested
        event_func = plugin_dict.get(payload_data.event_name, None)

        # If the plug-in was configured properly, the plugin_dict should have the event's run() function
        if event_func:

            log.info(f'Imported {payload_data.event_name}\'s run() function, running it')

            # Run the run() function with the password-removed JWT
            jwt_decoded.pop("pass")
            resp = event_func(jwt_decoded=jwt_decoded, payload_data=payload_data, args=args, conn=create_connection())

            log.info(f'\"{payload_data.event_name}\" ran successfully!')

            # It will only accept PluginResponses. If you try and return something else it will return a 501.
            if type(resp) == PluginResponse:
                log.info(f'Received PluginResponse from \"{payload_data.event_name}\"')
                return jsonify(resp.payload), resp.response_code
            else:
                log.critical('Invalid plug-in return type. TapAPI plug-ins should only return a PluginResponse.')
                return Response('Invalid plug-in return type.', 501)
        else:
            # If the plug-in is not in the plugin_dict either it doesn't exist or wasn't setup properly
            log.critical(f'Unknown event name \"{payload_data.event_name}\"! Plug-in doesn\'t exist or improper '
                         f'configuration of the event_name/Ground Module.')
            return Response('Unknown event name.', 400)

    except jwt.exceptions.InvalidSignatureError:
        # If the card doesn't decrypt properly, something is suspicious!
        log.critical(f'Invalid signature detected. Investigate card {payload_data.uid} immediately!')
        abort(Response("Invalid signature. Card UID does not decrypt properly.", 403))

    # Always close the connection to free up resources
    conn.close()


@app.route("/metrics", methods=["POST"])
def status():
    """
    Handles Ground Module metrics
    """
    payload = request.get_json()
    if ("event_name" in payload.keys()) and ("metric_data" in payload.keys()):
        logging.info(f"Received metrics payload from {payload['event_name']}!")
        utils.handle_metrics(
            conn=create_connection(),
            metric_data=payload["metric_data"],
            event_name=payload["event_name"]
        )
    else:
        # Metrics payload is invalid
        logging.warning("Received invalid metrics payload")
        return Response('Invalid payload', 400)
    return Response('OK', 200)


@app.route("/library")
def library_home_page():
    return render_template("library_tracker.html")


@app.route("/library/uid", methods=["GET", "POST"])
def library_uid():
    log.info("Library UID request received.")
    result = re.fullmatch(r"([a-zA-Z0-9]{2} ?){4}", request.args['uid'])
    if result:
        books = get_books_from_uid(request.args['uid'].upper(), conn=create_connection())
        return render_template("library_tracker_success.html", books=books, now=datetime.now())
    else:
        return render_template("library_tracker.html", error=True)


if __name__ == '__main__':
    log.info(f'Welcome to TapAPI! Running on port {args.port}, debug level {args.level}')
    # If you ever want to test the server on the same machine, do a requests.put/post on http://localhost:<port>
    # The host="0.0.0.0" allows external connections to the server
    app.run(debug=True, port=args.port, host="0.0.0.0")
