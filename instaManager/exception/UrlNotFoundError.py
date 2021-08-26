class UrlNotFoundError(Exception):
    def __init__(self, message="Cannot Find url"):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
