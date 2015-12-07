
class SleipnirError(Exception): pass
class SleipnirDbError(SleipnirError): pass
class SleipnirDbBadRequestError(SleipnirDbError): pass  # 400
class SleipnirDbNotFoundError(SleipnirDbError): pass  # 404
class SleipnirDbConflictError(SleipnirDbError): pass  # 409
