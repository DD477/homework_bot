from requests import status_codes


class ResponseIsNot200(Exception):
    """Код ответа не 200."""
    pass