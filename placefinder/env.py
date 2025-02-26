import os

from dotenv import load_dotenv

from placefinder.t import Env

load_dotenv(dotenv_path=".env", override=True, verbose=True)


env = Env(
    GMAPS_API_KEY=os.getenv("GMAPS_API_KEY", ""),
)
