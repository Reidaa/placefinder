import time

import googlemaps

from placefinder.env import env
from placefinder.t import Place, PlacePhoto
from placefinder.terminal import ProgressBar, WorkingOnIt


class GMapsService:
    def __init__(self):
        self.gmaps = googlemaps.Client(key=env.GMAPS_API_KEY)

    def _geocode(self, location: str):
        with WorkingOnIt(f"[bold green]Geocoding {location}..."):
            geocode_result = self.gmaps.geocode(location)
            if not geocode_result:
                raise Exception(f"Could not geocode location: {location}")

            location_coords = geocode_result[0]["geometry"]["location"]

        return location_coords

    def _place(self, place_id: str) -> dict:
        """Get detailed information from a place_id

        Args:
            place_id (str)
        """
        details: dict = self.gmaps.place(
            place_id,
            fields=[
                "name",
                "formatted_address",
                "rating",
                "user_ratings_total",
                # "opening_hours",
                "photo",
            ],
        )["result"]

        return details

    def get_places(
        self, location: str, search_terms: list[str], radius: int = 10000
    ) -> list[Place]:
        """
        Searches for places using Google Maps Places API based on given search terms in a specified location.
        For each place found, retrieves detailed information including name, address, rating, and coordinates.
        The function shows a progress bar while searching and processing results, handling pagination
        to get all available results for each search term.

        Args:
            location (str): Location to search in (e.g., "Paris, France")
            search_terms (list[str]): List of search terms to find places
            radius (int, optional): Search radius in meters. Defaults to 10000.
        """
        all_places: list[dict] = []
        location_coords = self._geocode(location)

        with ProgressBar() as progress:
            search_task = progress.add_task(
                f"[yellow]Searching for places in {location} ...",
                total=len(search_terms),
            )

            for term in search_terms:
                progress.update(
                    search_task, description=f"[yellow]Searching with '{term}' ..."
                )

                # Token for pagination
                page_token = None
                page_count = 0

                while True:
                    # Perform the search
                    places_result: dict = self.gmaps.places_nearby(
                        location=location_coords,
                        keyword=term,
                        radius=radius,
                        page_token=page_token,
                    )

                    results = places_result.get("results", [])
                    page_count += 1

                    place_task = progress.add_task(
                        f"[cyan]Processing page {page_count} results...",
                        total=len(results),
                    )

                    # Process each place
                    for i, place in enumerate(results):
                        progress.update(place_task, advance=1)

                        details = self._place(place["place_id"])

                        place_info = {
                            "place_id": place["place_id"],
                            "name": details.get("name", ""),
                            "address": details.get("formatted_address", ""),
                            "rating": details.get("rating"),
                            "total_ratings": details.get("user_ratings_total"),
                            "latitude": place["geometry"]["location"]["lat"],
                            "longitude": place["geometry"]["location"]["lng"],
                            "photos": details.get("photos", []),
                            # "opening_hours": "; ".join(
                            #     details.get("opening_hours", {}).get("weekday_text", [])
                            # )
                        }

                        all_places.append(place_info)

                    progress.remove_task(place_task)

                    # Get the next page token
                    page_token = places_result.get("next_page_token")

                    # If no more pages, break the loop
                    if not page_token:
                        break

                    # Sleep to avoid hitting rate limits
                    time.sleep(2)

                progress.update(search_task, advance=1)

        return self.sanitize(all_places)

    def sanitize(self, raws: list[dict]) -> list[Place]:
        places: list[Place] = []

        for raw in raws:
            places.append(
                Place(
                    place_id=raw["place_id"],
                    name=raw["name"],
                    address=raw["address"],
                    rating=raw["rating"],
                    total_ratings=raw["total_ratings"],
                    latitude=raw["latitude"],
                    longitude=raw["longitude"],
                    photos=[
                        PlacePhoto(
                            height=raw_photo_data["height"],
                            width=raw_photo_data["width"],
                            photo_reference=raw_photo_data["photo_reference"],
                            html_attributions=raw_photo_data["html_attributions"],
                        )
                        for raw_photo_data in raw["photos"]
                    ],
                )
            )

        return places
