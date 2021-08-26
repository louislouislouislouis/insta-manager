from termcolor import colored


class Log:
    def __init__(self, debut="NOT SET"):
        self.debut = debut

    def print(self, word, type="INFO", method="", color="white"):
        text = colored("[ " + self.debut + " - " + type + " - " + method + " ]: " + str(word), color)
        print(text)
