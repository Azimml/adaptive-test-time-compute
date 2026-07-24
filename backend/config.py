"""Central configuration for the controller and sampler.

Values are read from the environment (via a ``.env`` file, see
``.env.example``) with sensible defaults, so the package imports cleanly
without any environment set up — an API key is only needed to make a real
request. The controller defaults define the triple stopping gate; individual
runs can override them per call via the ``config`` argument to
``adaptive_solve``.
"""
import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4.1-mini")

# Sampling
TEMPERATURE = 0.7          # higher temperature -> more diverse samples to vote over
MAX_TOKENS = 1024          # per-sample completion cap

# Controller defaults (the triple stopping gate)
MIN_SAMPLES = 4            # never stop before this many samples exist
MAX_SAMPLES = 8            # hard budget cap
STEP_SIZE = 2              # samples added per round (reachable stops: 4, 6, 8)
CONFIDENCE_THRESHOLD = 0.7  # majority ratio required to stop early
MIN_AGREEMENT_COUNT = 3    # majority answer must appear at least this many times
