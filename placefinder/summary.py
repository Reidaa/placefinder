from rich import box
from rich.table import Table

from placefinder import console
from placefinder.t import PlaceCollection


def rating_distribution(collection: PlaceCollection):
    total_places = len(collection.places)

    console.print("\n[bold]Rating Distribution:[/]")
    rating_table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    rating_table.add_column("Rating Range")
    rating_table.add_column("Count", justify="right")
    rating_table.add_column("Percentage", justify="right")

    rating_counts = collection.get_rating_distribution()

    for label, count in rating_counts.items():
        percentage = (count / total_places) * 100 if total_places > 0 else 0

        # Choose color based on rating category
        if "Excellent" in label:
            style = "green"
        elif "Very Good" in label:
            style = "lime"
        elif "Good" in label:
            style = "yellow"
        elif "Average" in label:
            style = "orange3"
        elif "Below" in label:
            style = "red"
        else:
            style = "grey70"

        rating_table.add_row(label, f"{count}", f"[{style}]{percentage:.1f}%[/]")

    console.print(rating_table)


def top_places(collection: PlaceCollection, top: int):
    console.print(f"\n[bold]Top {top} Rated Places:[/]")

    top_places = collection.get_top_rated(top)

    place_table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    place_table.add_column("Name")
    place_table.add_column("Rating", justify="center")
    place_table.add_column("Reviews", justify="right")
    place_table.add_column("Address")

    for place in top_places:
        # Color the rating based on its value
        rating = place.rating
        if rating is None:
            rating_text = "[grey]N/A[/]"
        elif rating >= 4.5:
            rating_text = f"[green]{rating}[/]"
        elif rating >= 4.0:
            rating_text = f"[lime]{rating}[/]"
        else:
            rating_text = f"[yellow]{rating}[/]"

        place_table.add_row(
            f"[bold]{place.name}[/]",
            rating_text,
            f"{place.total_ratings or 0}",
            place.address,
        )

    console.print(place_table)


def district_distribution(collection: PlaceCollection, location: str):
    if "paris" in location.lower():
        console.print("\n[bold]Distribution by Paris Arrondissement:[/]")

        # Get district distribution
        districts = collection.get_district_distribution()

        if districts:
            district_table = Table(
                show_header=True, header_style="bold cyan", box=box.ROUNDED
            )
            district_table.add_column("Arrondissement")
            district_table.add_column("Count", justify="right")

            for district, count in sorted(districts.items(), key=lambda x: int(x[0])):
                district_table.add_row(
                    f"{district}{'th' if district not in ['01', '1'] else 'st'}",
                    str(count),
                )

            console.print(district_table)

    else:
        raise NotImplementedError()
