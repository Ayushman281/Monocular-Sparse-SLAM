class JobError(Exception):
    def __init__(self, message: str, code: str = "invalid_video"):
        super().__init__(message)
        self.code = code
