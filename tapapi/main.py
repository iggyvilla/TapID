import logging
from datetime import datetime as dt
from flask import Flask

# Made by Enrique Villa, Grade 12 Da Vinci, SY 2022-2023

# Setup the Flask server (need to pass in the __name__ dunder variable)
# A good Flask tutorial: https://www.youtube.com/watch?v=Z1RJmh_OqeA&t=2358s
# (P.S. freeCodeCamp is an amazing resource!)

# Read more on python-defined variables: https://bic-berkeley.github.io/psych-214-fall-2016/two_dunders.html
app = Flask(__name__)

# Setup logging (equivalent to printing, but syntactically makes more sense and easier to read logs)
# For instance, here we set it up to send to console AND a text file with the name as the date when main.py
# was started (ex, Jan-24-2-41-pm

# This way, if the server crashes, we still have a text file to read and see the cause of crash
# or determine where the server stopped
logging.basicConfig(level=logging.INFO,
                    format=f'%(asctime)s %(levelname)s > %(message)s',
                    handlers=[
                        logging.FileHandler("debug.log"),
                        logging.StreamHandler()
                    ])
