class CommentsNotFoundError(Exception):
    def __init__(self, message="Not Connected"):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
