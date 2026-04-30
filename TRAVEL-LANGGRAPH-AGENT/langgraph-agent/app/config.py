import os
from dotenv import load_dotenv

import logging
import sys

# Configure logging to output to stdout for CloudWatch
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("travel-agent")

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
DUFFEL_ACCESS_TOKEN = os.getenv("DUFFEL_ACCESS_TOKEN")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")