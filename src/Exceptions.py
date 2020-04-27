
class APIException(OSError):

    def __init__(self, message = None, url="https://Bungie.net/"):
        msg = "There was an error when accessing the Destiny API"
        if message is not None:
            msg += ": " + message
        super().__init__(msg)
        self._url = url
        self._message = msg

    @property
    def url(self):
        return self._url

    @property
    def message(self):
        return self._message

class GeneralException(Exception):

    def __init__(self, message):
        super().__init__(message)

class ManifestError(IOError):

    def __init__(self, message, SQL=None):
        super().__init__(message)
        self._SQL = SQL

    @property
    def SQL(self):
        return self._SQL
    
    
    

