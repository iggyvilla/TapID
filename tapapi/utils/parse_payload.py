from typing import Union


class TapAPIRequestPayload:
    def __init__(self, jwt: str, event_name: str, uid: str, event_data: dict):
        """
        Data wrapper class for easy Ground Module payload data access.

        :param jwt: The private-key encrypted JSON Web Token present in the RFID card.
        :param event_name: The name of the event. Must be equal to one event_name in the /plugins directory or else an
         error will be thrown.
        :param uid: The UID of the card (must be hex casted to string).
        :param event_data: The data associated with the event.
        """
        self.jwt = jwt
        self.event_name = event_name
        self.uid = uid
        self.event_data = event_data


def parse_payload(payload: dict) -> Union[KeyError, TapAPIRequestPayload]:
    """Parse a dict-converted JSON payload from the Ground Module."""
    # Read up on list comprehensions, the all() function, and the in keyword
    # Checks if all keys in the tuple are in the payload
    if all(k in payload for k in ("jwt", "uid", "event_name", "event_data")):
        return TapAPIRequestPayload(payload["jwt"], payload["event_name"], payload["uid"], payload["event_data"])
    else:
        return KeyError("Incomplete payload")
