import os
import subprocess
import shutil
from src.utils.logger import Logger


class KepubHandler:
    """
    Wrapper for the 'kepubify' tool (Golang binary) used to convert EPUBs to KEPUBs.
    Kepubify is not included in this Python package and must be installed separately
    (or via Docker).
    """

    BINARY_NAME = "kepubify"

    @staticmethod
    def get_binary_path():
        """Attempts to locate the kepubify binary in system PATH or current directory."""
        # 1. Check system PATH (Preferred)
        path_bin = shutil.which(KepubHandler.BINARY_NAME)
        if path_bin:
            return path_bin

        # 2. Check current working directory (Legacy/Dev)
        local_bin = os.path.join(os.getcwd(), KepubHandler.BINARY_NAME)
        if os.path.exists(local_bin) and os.access(local_bin, os.X_OK):
            return local_bin

        return None

    @staticmethod
    def convert_to_kepub(input_path, output_path=None):
        """
        Executes the conversion command.

        Args:
            input_path: Path to the source .epub file.
            output_path: Optional path for the destination .kepub.epub file.
                         If omitted, defaults to source name + .kepub.epub suffix.
        """
        if input_path.lower().endswith(".kepub.epub"):
            Logger.warning("Skipping conversion (already KEPUB).", indent=4)
            return True

        binary = KepubHandler.get_binary_path()
        if not binary:
            Logger.error("'kepubify' not found in PATH.", indent=4)
            Logger.info(
                "Please install it from: https://github.com/pgaskin/kepubify",
                indent=4,
            )
            Logger.info("Or ensure it is in your system PATH.", indent=4)
            return False

        if not output_path:
            if input_path.lower().endswith(".epub"):
                output_path = input_path[:-5] + ".kepub.epub"
            else:
                output_path = input_path + ".kepub.epub"

        # kepubify input.epub -o output.kepub.epub
        cmd = [binary, input_path, "-o", output_path]

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            Logger.success(
                f"Converted to KEPUB: {os.path.basename(output_path)}", indent=4
            )
            return True

        except subprocess.CalledProcessError as e:
            Logger.error(f"kepubify failed: {e.stderr.strip()}", indent=4)
            return False
        except Exception as e:
            Logger.error(f"Conversion error: {e}", indent=4)
            return False
