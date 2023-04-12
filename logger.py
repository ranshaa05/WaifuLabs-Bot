import logging
import coloredlogs


class setup_logging:
    """Sets up logging for the bot."""

    def __init__(self):
        coloredlogs.install()
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        )
        self.log = logging.getLogger(__name__)
        logging.getLogger("nextcord").setLevel(logging.WARNING)
