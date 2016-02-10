
# thanks: http://flask.pocoo.org/docs/0.10/patterns/apierrors/
class SleipnirError(Exception):
    status_code = 500

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self, message)
        self.message = message  # redundant?
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

# class SleipnirBadRequestError(SleipnirError): status_code = 400
# class SleipnirNotFoundError(SleipnirError): status_code = 404
# class SleipnirConflictError(SleipnirError): status_code = 409
class SleipnirDbError(SleipnirError): pass
