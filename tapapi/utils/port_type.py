import argparse


def port_type(port: str) -> int:
    """Custom type for argparse module to prevent ports over 16 bytes (65,535)"""
    port = int(port)
    if port > 65535:
        raise argparse.ArgumentTypeError("Maximum port is 65,535")
    return port

