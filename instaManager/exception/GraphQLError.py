class GraphQLError(Exception):
    def __init__(self, json, message="Error in GraphQl"):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        self.json = json
