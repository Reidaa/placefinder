from typing import List

from rich.panel import Panel
from rich.text import Text

from placefinder import console
from placefinder.MenuAnalyzer import VisualAnalyzer
from placefinder.services.GMaps import GMapsService
from placefinder.summary import top_places
from placefinder.t import PlaceCollection
from placefinder.terminal import Banner, ProgressBar, WorkingOnIt

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

# exclude_terms = ["takoyaki", "udon", "soba"]
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


def search_places(location: str, search_terms: List[str]) -> PlaceCollection:
    """
    Fetches places in specified location using Google Maps Places API
    """
    collection = PlaceCollection()

    gmaps = GMapsService()

    with WorkingOnIt("[bold blue]Initializing OCR engine...[/]"):
        visual_analyzer = VisualAnalyzer(languages=["en", "fr"])

    places = gmaps.get_places(location, search_terms, 10000)

    with ProgressBar() as progress:
        task = progress.add_task(
            description="[yellow]Parsing places ...", total=len(places)
        )

        for place in places:
            if place.photos:
                progress.update(
                    task,
                    description=f"[cyan]Analyzing {place.name}'s photos ...",
                )
                found_words = visual_analyzer.analyze_place_photos(place.photos)
                print(found_words)

            collection.add_place(place)

            progress.update(task, advance=1)

    return collection


def main():
    Banner("🔍 Places Finder 🔍", "Powered by Google Maps API")

    collection = search_places(location, search_terms)

    # location_slug = location.lower().replace(",", "").replace(" ", "_")
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # filename = f"{location_slug}_places_{timestamp}.csv"
    # save_to_csv(collection, filename)

    total_places = len(collection.places)

    console.print(
        Panel(
            Text(f"{location} Places Data Summary", style="bold magenta"),
            border_style="magenta",
        )
    )

    console.print(f"[bold cyan]Total places found:[/] [yellow]{total_places}[/]")

    top_places(collection, 50)


if __name__ == "__main__":
    main()
