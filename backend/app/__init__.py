
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debate.log"),
        logging.StreamHandler()
    ]
)

# Package version
__version__ = "0.1.0"


CHROMA_DIR = Path("./chroma_data")
CHROMA_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.info(f"Initialized debate-ai v{__version__}")