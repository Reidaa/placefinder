import time

import googlemaps
from loguru import logger

from src.db import save_to_db
from src.env import env
from src.t import Shop


@logger.catch
def get_kebab_shops(api_key: str):
    """
    Fetches kebab shops in Paris using Google Maps Places API
    Returns a list of dictionaries containing shop information
    """
    gmaps = googlemaps.Client(key=api_key)

    location = "Paris, France"

    # Get the geometry of Paris for the search
    geocode_result = gmaps.geocode(location)
    if not geocode_result:
        raise Exception("Could not geocode Paris location")

    paris_location = geocode_result[0]["geometry"]["location"]

    all_shops: list[Shop] = []

    search_terms = [
        "kebab",
        "döner kebab",
        "kebab shop",
        "Kebab shop",
        "berliner kebab",
        "kebap",
        "kebab à emporter",
        "spécialités turques",
        "turkish",
        "kebab 75001",
        "kebab 75002",
        "kebab 75003",
        "kebab 75004",
        "kebab 75005",
        "kebab 75006",
        "kebab 75007",
        "kebab 75008",
        "kebab 75009",
        "kebab 75010",
        "kebab 75011",
        "kebab 75012",
        "kebab 75013",
        "kebab 75014",
        "kebab 75015",
        "kebab 75016",
        "kebab 75017",
        "kebab 75018",
        "kebab 75019",
        "kebab 75020",
    ]

    # Search radius in meters (Paris is roughly 10km across)
    radius = 10000

    for term in search_terms:
        logger.info(f"Using search term: {term}")

        # Token for pagination
        page_token = None

        while True:
            try:
                # Perform the search
                places_result = gmaps.places_nearby(
                    location=paris_location,
                    keyword=term,
                    radius=radius,
                    page_token=page_token,
                )

                # Process each place
                for place in places_result.get("results", []):
                    # Get detailed information for each place
                    details = gmaps.place(
                        place["place_id"],
                        fields=[
                            "name",
                            "formatted_address",
                            "formatted_phone_number",
                            "rating",
                            "user_ratings_total",
                            "opening_hours",
                            "website",
                        ],
                    )["result"]

                    shop_info = Shop(
                        name=details.get("name", ""),
                        address=details.get("formatted_address", ""),
                        rating=details.get("rating", 0),
                        total_ratings=details.get("user_ratings_total", 0),
                        place_id=place["place_id"],
                        latitude=place["geometry"]["location"]["lat"],
                        longitude=place["geometry"]["location"]["lng"],
                    )

                    # Only add if not already in list (checking by place_id)
                    if not any(
                        shop.place_id == shop_info.place_id for shop in all_shops
                    ):
                        all_shops.append(shop_info)

                # Get the next page token
                page_token = places_result.get("next_page_token")

                # If no more pages, break the loop
                if not page_token:
                    break

                # Sleep to avoid hitting rate limits
                time.sleep(2)

            except Exception as e:
                print(f"Error occurred while fetching places: {str(e)}")
                break

    return all_shops


def main():
    logger.info("Fetching kebab shops in Paris...")
    shops = get_kebab_shops(str(env.GMAPS_API_KEY))

    logger.info(f"Found {len(shops)} unique kebab shops")
    save_to_db(shops)
