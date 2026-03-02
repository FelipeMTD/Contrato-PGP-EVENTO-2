import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    URL = os.getenv("EPS_URL")
    USER_TYPE = os.getenv("EPS_USER_TYPE")
    USER_ID = os.getenv("EPS_USER_ID")
    PASSWORD = os.getenv("EPS_USER_PASS")
    HEADLESS = os.getenv("HEADLESS", "True").lower() == "true"
    SLOW_MO = int(os.getenv("SLOW_MO", 0))