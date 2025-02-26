from collections import defaultdict
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_extra_types.coordinate import Latitude, Longitude


class Env(BaseModel):
    GMAPS_API_KEY: SecretStr = Field(min_length=1)


class Location(BaseModel):
    name: str
    country: str
    radius: int
    districts: list[str]

    def __str__(self) -> str:
        return f"{self.name}, {self.country}"

    def __repr__(self) -> str:
        return str(self)


class PlacePhoto(BaseModel):
    height: int
    html_attributions: list[str]
    photo_reference: str
    width: int


class Place(BaseModel):
    """Pydantic model for a place"""

    place_id: str
    name: str
    address: str
    rating: Optional[float] = None
    total_ratings: Optional[int] = None
    latitude: Latitude
    longitude: Longitude
    opening_hours: Optional[str] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    menu_terms: list[str] = Field(default_factory=list)
    photos: list[PlacePhoto] = Field(default_factory=list)

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v):
        if v is not None and (v < 0 or v > 5):
            raise ValueError("Rating must be between 0 and 5")
        return v

    @field_validator("total_ratings")
    @classmethod
    def validate_total_ratings(cls, v):
        if v is not None and v < 0:
            raise ValueError("Total ratings cannot be negative")
        return v

    model_config = {
        "validate_assignment": True,
        "extra": "ignore",  # Ignore extra fields from Google API
    }


class PlaceCollection:
    """Collection of places with helper methods"""

    def __init__(self):
        self.places: list[Place] = []

    def add_place(self, place: Place) -> bool:
        """Add a place to the collection if it doesn't exist already"""
        # Check if place already exists
        if not any(existing.place_id == place.place_id for existing in self.places):
            self.places.append(place)
            return True
        return False

    def to_list(self) -> list[dict[str, Any]]:
        """Convert collection to list of dictionaries"""
        return [place.model_dump() for place in self.places]

    def get_top_rated(self, n: int = 5, exclude_suspicious: bool = True) -> list[Place]:
        """
        Get top N rated places

        Args:
            n: Number of places to return
            exclude_suspicious: If True, exclude places with less than 20 reviews and rating greater or equal to 4.9
        """

        if exclude_suspicious:
            return sorted(
                [
                    place
                    for place in self.places
                    if place.rating is not None
                    and place.total_ratings is not None
                    and place.rating < 4.9
                    and place.total_ratings >= 20
                ],
                key=lambda x: x.rating or 0,
                reverse=True,
            )[:n]

        return sorted(
            self.places,
            key=lambda x: x.rating or 0,
            reverse=True,
        )[:n]

    def get_rating_distribution(self) -> dict[str, int]:
        """Get rating distribution counts"""
        distribution = {
            "Excellent (4.5-5.0)": 0,
            "Very Good (4.0-4.4)": 0,
            "Good (3.5-3.9)": 0,
            "Average (3.0-3.4)": 0,
            "Below Average (<3.0)": 0,
            "Not Rated": 0,
        }

        for place in self.places:
            rating = place.rating
            if rating is None:
                distribution["Not Rated"] += 1
            elif rating >= 4.5:
                distribution["Excellent (4.5-5.0)"] += 1
            elif rating >= 4.0:
                distribution["Very Good (4.0-4.4)"] += 1
            elif rating >= 3.5:
                distribution["Good (3.5-3.9)"] += 1
            elif rating >= 3.0:
                distribution["Average (3.0-3.4)"] += 1
            else:
                distribution["Below Average (<3.0)"] += 1

        return distribution

    def get_places_with_menu_terms(self, terms: list[str]) -> list[Place]:
        """Get places that have any of the specified terms in their menu"""
        return [
            place
            for place in self.places
            if any(
                term.lower() in [t.lower() for t in place.menu_terms] for term in terms
            )
        ]

    def get_district_distribution(self) -> dict[str, int]:
        """Get distribution by Paris arrondissement"""
        districts: defaultdict = defaultdict(int)

        for place in self.places:
            district = None
            address = place.address

            # Look for the Paris postal code pattern (750XX)
            if "750" in address:
                for word in address.split():
                    if (
                        word.startswith("750")
                        and len(word) >= 5
                        and word[3:5].isdigit()
                    ):
                        district = word[3:5]
                        break

            if district:
                districts[district] += 1

        return districts
