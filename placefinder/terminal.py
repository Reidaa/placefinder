from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.status import Status
from rich.text import Text

from placefinder import console


def ProgressBar() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        TextColumn("[bold green]{task.completed} of {task.total}"),
        TimeElapsedColumn(),
    )


def WorkingOnIt(text: str) -> Status:
    return console.status(text)


def Banner(title: str, subtitle: str) -> None:
    """Print banner

    Args:
        title (str)
        subtitle (str)
    """
    console.print(
        Panel(
            Text(title, style="bold yellow", justify="center"),
            subtitle=subtitle,
            border_style="yellow",
        )
    )
