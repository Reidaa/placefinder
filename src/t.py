from pydantic import BaseModel, StrictStr
from pydantic_extra_types.coordinate import Latitude, Longitude


class Env(BaseModel):
    GMAPS_API_KEY: str


class Shop(BaseModel):
    name: StrictStr
    address: str
    rating: float
    total_ratings: int
    place_id: str
    latitude: Latitude
    longitude: Longitude
