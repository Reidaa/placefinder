import csv
import time
from datetime import datetime
from typing import List

import googlemaps
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.text import Text

from placefinder import console
from placefinder.env import env
from placefinder.MenuAnalyzer import MenuAnalyzer
from placefinder.summary import (
    district_distribution,
    rating_distribution,
    top_places,
)
from placefinder.t import PlaceCollection

location = "Paris, France"

# base_terms = [
#     "cider",
#     "cidrerie",
# ]

# base_terms = [
#     "berliner kebab",
#     "döner kebab",
#     "kebab shop",
#     "kebab",
#     "kebap",
#     "turkish",
# ]

# base_terms = ["bubble tea", "bubble tea shop"]

# base_terms = ["korean", "korean bbq"]

base_terms = ["ramen"]

exclude_terms = ["takoyaki", "udon", "soba"]
menu_terms: list[str] = []

paris_postal_codes = [
    "75001",
    # "75002",
    # "75003",
    # "75004",
    # "75005",
    # "75006",
    # "75007",
    # "75008",
    # "75009",
    # "75010",
    # "75011",
    # "75012",
    # "75013",
    # "75014",
    # "75015",
    # "75016",
    # "75017",
    # "75018",
    # "75019",
    # "75020",
]


search_terms = []

for term in base_terms:
    for po in paris_postal_codes:
        search_terms.append(f"{term} {po}")


def search_places(
    api_key: str, location: str, search_terms: List[str]
) -> PlaceCollection:
    """
    Fetches places in specified location using Google Maps Places API
    Returns a collection of places
    """
    # Initialize collection
    collection = PlaceCollection()

    # Initialize Google Maps client
    gmaps = googlemaps.Client(key=api_key)

    menu_analyzer = None
    if menu_terms:
        menu_analyzer = MenuAnalyzer(languages=["en", "fr"])

    with console.status(f"[bold green]Geocoding {location}...") as status:
        # Get the geometry of the location
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            raise Exception(f"Could not geocode location: {location}")

        location_coords = geocode_result[0]["geometry"]["location"]

    # Search radius in meters (roughly 10km)
    radius = 10000

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[bold green]{task.completed} of {task.total}"),
        TimeElapsedColumn(),
    ) as progress:
        search_task = progress.add_task(
            f"[yellow]Searching for places in {location}...", total=len(search_terms)
        )

        for term in search_terms:
            progress.update(
                search_task, description=f"[yellow]Searching for '{term}'..."
            )

            # Token for pagination
            page_token = None
            page_count = 0

            while True:
                try:
                    # Perform the search
                    places_result = gmaps.places_nearby(
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

                        try:
                            # Get detailed information for each place
                            details = gmaps.place(
                                place["place_id"],
                                fields=[
                                    "name",
                                    "formatted_address",
                                    "rating",
                                    "user_ratings_total",
                                    "opening_hours",
                                    "photo",
                                ],
                            )["result"]

                            place_info = {
                                "place_id": place["place_id"],
                                "name": details.get("name", ""),
                                "address": details.get("formatted_address", ""),
                                "rating": details.get("rating"),
                                "total_ratings": details.get("user_ratings_total"),
                                "latitude": place["geometry"]["location"]["lat"],
                                "longitude": place["geometry"]["location"]["lng"],
                                "opening_hours": "; ".join(
                                    details.get("opening_hours", {}).get(
                                        "weekday_text", []
                                    )
                                ),
                                "menu_terms": [],
                            }

                            if menu_analyzer and menu_terms and "photos" in details:
                                photos = details.get("photos", [])
                                progress.update(
                                    place_task,
                                    description=f"[cyan]Analyzing menu for {place_info['name']}...",
                                )
                                found_terms = menu_analyzer.analyze_place_photos(
                                    place["place_id"], photos, api_key, menu_terms
                                )
                                place_info["menu_terms"] = found_terms

                            # Add to collection
                            collection.add_place(place_info)

                        except Exception as e:
                            console.print(
                                f"[bold red]Error processing place {place.get('name', 'Unknown')}: {str(e)}"
                            )

                    progress.remove_task(place_task)

                    # Get the next page token
                    page_token = places_result.get("next_page_token")

                    # If no more pages, break the loop
                    if not page_token:
                        break

                    # Sleep to avoid hitting rate limits
                    time.sleep(2)

                except Exception as e:
                    console.print(
                        f"[bold red]Error occurred while fetching places: {str(e)}"
                    )
                    break

            progress.update(search_task, advance=1)

    return collection


def save_to_csv(collection: PlaceCollection, filename: str) -> None:
    """
    Saves the place collection to a CSV file
    """
    with console.status(f"[bold green]Saving to {filename}..."):
        # Convert to list of dicts
        data = collection.to_list()

        # Get all fieldnames from the first item
        if data:
            fieldnames = data[0].keys()

            # Write to CSV
            with open(filename, "w", newline="", encoding="utf-8-sig") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

    console.print(
        f"[bold green]✓[/] [bold]Successfully saved {len(collection.places)} places to {filename}[/]"
    )


def main():
    try:
        # Print banner
        console.print(
            Panel.fit(
                Text("🔍 Places Finder 🔍", style="bold yellow"),
                subtitle="Powered by Google Maps API",
                border_style="yellow",
            )
        )  # Default location

        # Generate filename
        location_slug = location.lower().replace(",", "").replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{location_slug}_places_{timestamp}.csv"

        # Fetch places
        collection = search_places(env.GMAPS_API_KEY, location, search_terms)

        # Save to CSV
        # save_to_csv(collection, filename)

        total_places = len(collection.places)

        header = Text(f"{location} Places Data Summary", style="bold magenta")
        console.print(Panel(header, border_style="magenta"))

        console.print(f"[bold cyan]Total places found:[/] [yellow]{total_places}[/]")

        top_places(collection, 50)

        print([place.menu_terms for place in collection.places])

    except Exception as e:
        console.print(f"[bold red]An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
