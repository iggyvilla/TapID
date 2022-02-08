def is_jwt_valid(jwt_decoded: dict):
    """
    Checks if a JWT is valid

    :param jwt_decoded: The decoded JWT
    :return: True/False
    """
    if all(k in jwt_decoded for k in ("name", "grade", "pass")):
        return True
    else:
        return False
