import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4.1-mini")

# Sampling
TEMPERATURE = 0.7
MAX_TOKENS = 1024

# Controller defaults
MIN_SAMPLES = 4
MAX_SAMPLES = 8
STEP_SIZE = 2
CONFIDENCE_THRESHOLD = 0.7
MIN_AGREEMENT_COUNT = 3
