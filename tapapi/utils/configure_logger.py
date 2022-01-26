import logging
import os


def configure_logger(log, args, filename):
    """
    Configure the TapAPI logger

    :param log: The log object (using logging.getLogger('...'))
    :param args: argument object from argparse
    :param filename: the filename of the log file
    :return: configured logging object
    """
    # Logging has different levels (NOTESET, DEBUG, INFO, WARNING, ERROR, CRITICAL)
    # Depending on how we set it up, then the server will spit out more or less information
    # We use a ternary operator here (read more: https://www.geeksforgeeks.org/ternary-operator-in-python/)
    log_level = args.level * 10 if args.level % 10 == 0 and args.level <= 50 else 10
    log.setLevel(log_level)

    # Handlers tell the logger where to spit out the logs
    # In this case, we tell it to send it to a log file (via FileHandler) and the console (via StreamHandler)
    tapapi_logging_format = ' %(asctime)s  %(filename)-17s  [%(levelname)8s]  %(message)s '

    streamhandler = logging.StreamHandler()
    streamhandler.setFormatter(logging.Formatter(tapapi_logging_format))

    filehandler = logging.FileHandler(os.path.join("logs/", filename))
    filehandler.setFormatter(logging.Formatter(tapapi_logging_format))
    filehandler.setLevel(log_level)

    log.addHandler(filehandler)
    log.addHandler(streamhandler)

    return log
