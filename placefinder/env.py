import os

from dotenv import load_dotenv
from pydantic import SecretStr

from placefinder.t import Env

load_dotenv(dotenv_path=".env", override=True, verbose=True)


env = Env(
    GMAPS_API_KEY=SecretStr(os.getenv("GMAPS_API_KEY", "")),
)
