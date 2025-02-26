import csv

from placefinder import console
from placefinder.t import PlaceCollection
from placefinder.terminal import WorkingOnIt


def save_to_csv(collection: PlaceCollection, filename: str) -> None:
    """
    Saves the place collection to a CSV file
    """

    with WorkingOnIt(f"[bold green]Saving to {filename}..."):
        # Convert to list of dicts
        data = collection.to_list()

        # Get all fieldnames from the first item
        if data:
            fieldnames = data[0].keys()

            # Write to CSV
            with open(filename, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

    console.print(
        f"[bold green]✓[/] [bold]Successfully saved {len(collection.places)} places to {filename}[/]"
    )
