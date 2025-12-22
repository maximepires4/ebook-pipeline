from src import config
import json
import termcolor


class Logger:
    """
    Simple logging wrapper to standardize console output.
    Handles indentation and conditional verbosity.
    """

    @staticmethod
    def info(msg):
        """Standard info message."""
        print(msg)

    @staticmethod
    def verbose(msg):
        """Debug message, only shown if VERBOSE config is True."""
        if config.VERBOSE:
            print(termcolor.colored("VERBOSE", "cyan") + f": {msg}")

    @staticmethod
    def success(msg):
        """Success message with checkmark icon."""
        print(termcolor.colored("SUCCESS", "green") + f": {msg}")

    @staticmethod
    def warning(msg):
        """Warning message with alert icon."""
        print(termcolor.colored("WARNING", "yellow") + f": {msg}")

    @staticmethod
    def error(msg):
        """Error message with cross icon."""
        print(termcolor.colored("ERROR", "red") + f": {msg}")

    @staticmethod
    def full_json(data):
        """
        Dumps a dictionary as formatted JSON.
        Useful for debugging API responses.
        Only shown if FULL_OUTPUT config is True.
        """
        if config.FULL_OUTPUT:
            json_str = json.dumps(data, ensure_ascii=False)
            print("[FULL OUTPUT]")
            print(json_str)
