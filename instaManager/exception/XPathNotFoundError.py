class XPathNotFoundError(Exception):
    def __init__(self, message="Cannot Find XpathFile"):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
