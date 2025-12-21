from src import config
import json


class Logger:
    """
    Simple logging wrapper to standardize console output.
    Handles indentation and conditional verbosity.
    """

    @staticmethod
    def info(msg, indent=0):
        """Standard info message."""
        print(" " * indent + msg)

    @staticmethod
    def verbose(msg, indent=0):
        """Debug message, only shown if VERBOSE config is True."""
        if config.VERBOSE:
            print(" " * indent + msg)

    @staticmethod
    def success(msg, indent=0):
        """Success message with checkmark icon."""
        print(" " * indent + f"✅ {msg}")

    @staticmethod
    def warning(msg, indent=0):
        """Warning message with alert icon."""
        print(" " * indent + f"⚠️  {msg}")

    @staticmethod
    def error(msg, indent=0):
        """Error message with cross icon."""
        print(" " * indent + f"❌ {msg}")

    @staticmethod
    def full_json(data, indent=0):
        """
        Dumps a dictionary as formatted JSON.
        Useful for debugging API responses.
        Only shown if FULL_OUTPUT config is True.
        """
        if config.FULL_OUTPUT:
            json_str = json.dumps(data, indent=4, ensure_ascii=False)
            indented_lines = [" " * indent + line for line in json_str.split("\n")]
            print(" " * indent + "[FULL OUTPUT]")
            print("\n".join(indented_lines))
