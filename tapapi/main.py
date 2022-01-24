import logging
from datetime import datetime as dt
import argparse
from flask import Flask, Response, request

# Made by Enrique Villa, Grade 12 Da Vinci, SY 2022-2023

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
                    type=int)
parser.add_argument('-b', '--blind',
                    dest='blind',
                    help='Don\'t make the server panic on recognition of new cards',
                    action='store_true')

args = parser.parse_args()

# Next, setup logging (equivalent to printing, but syntactically makes easier to read code and logs)
# For instance, here we set it up to send to console AND a text file with the name as the date when main.py
# This way, if the server crashes, we still have a text file to read and see the cause of crash
# or determine where the server stopped

# Filename using datetime library (string FORMAT time method, hence strftime! NOT strptime!)
# Good resource - https://strftime.org
# Will show up as Jan_01_07_00_PM, for example (based on system clock)
filename = str(dt.now().strftime("%b_%d_%I_%M_%p")) + ".txt"

# Logging library setup
# Logging has different levels (NOTESET, DEBUG, INFO, WARNING, ERROR, CRITICAL)
# Depending on how we set it up, then the server will spit out more or less information
# We use a ternary operator here (read more: https://www.geeksforgeeks.org/ternary-operator-in-python/)
logging.basicConfig(level=args.level * 10 if args.level % 10 == 0 and args.level <= 50 else 10,
                    format=f'%(asctime)s %(levelname)s > %(message)s',
                    handlers=[
                        # logging.FileHandler(os.path.join("logs/", filename)),
                        logging.StreamHandler()
                    ])

logging.debug('Logging and basic server setup complete!')


# Time to get into the main event ;)

@app.route("/event", methods=["PUT"])
def route_event():
    payload = request.get_json()
    logging.info(payload)
    return Response("Test", 200)


if __name__ == '__main__':
    # If you ever want to test the server on the same machine, do a requests.put on http://localhost:5000
    app.run(debug=True, port=5000)
