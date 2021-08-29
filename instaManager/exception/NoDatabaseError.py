class NoDatabaseError(Exception):
    def __init__(self, json, message="Error in Database"):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        self.json = json
