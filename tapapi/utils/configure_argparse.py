import argparse
from utils.port_type import port_type


def configure_argparse():
    """
    Configure argparse for TapAPI
    :return: a TapAPI-configured ArgumentParser object
    """
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
                        type=port_type)

    parser.add_argument('-user', '--db-user',
                        dest='dbuser',
                        help='PostgreSQL user password',
                        required=True,
                        action='store',
                        type=str)

    parser.add_argument('-pass', '--db-password',
                        dest='dbpass',
                        help='PostgreSQL database password',
                        required=True,
                        action='store',
                        type=str)

    return parser
