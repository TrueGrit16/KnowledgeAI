import logging, sys, pathlib
import logging.handlers
LOG_DIR = pathlib.Path("~/KnowledgeAI/logs").expanduser()
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.handlers.RotatingFileHandler(LOG_DIR/"pipeline.log",
                                             maxBytes=5_000_000, backupCount=5)
    ]
)
