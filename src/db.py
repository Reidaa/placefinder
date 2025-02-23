from datetime import datetime

from loguru import logger
from peewee import (
    CharField,
    DateTimeField,
    FloatField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField,
)

from src.t import Shop

db = SqliteDatabase("kebabs.sqlite3")


class BaseModel(Model):
    class Meta:
        database = db


class KebabShop(BaseModel):
    """Kebab shop model"""

    place_id = CharField(primary_key=True)
    name = CharField()
    address = TextField()
    rating = FloatField(null=True)
    total_ratings = IntegerField(null=True)
    website = CharField(null=True)
    latitude = FloatField()
    longitude = FloatField()
    last_updated = DateTimeField(default=datetime.now)

    def __str__(self):
        return f"{self.name} - {self.address}"

    class Meta:
        table_name = "kebab_shops"


def init_database():
    """Initialize the database and create tables"""
    db.connect()
    db.create_tables([KebabShop], safe=True)


def save_to_db(shops: list[Shop]):
    """
    Upsert the shop information in the database using Peewee ORM
    """
    init_database()
    with db.atomic():
        for shop in shops:
            logger.info(f"upsert-ing {shop.name}")
            (
                KebabShop.insert(
                    name=shop.name,
                    place_id=shop.place_id,
                    address=shop.address,
                    rating=shop.rating,
                    total_ratings=shop.total_ratings,
                    latitude=shop.latitude,
                    longitude=shop.longitude,
                )
                .on_conflict_replace()
                .execute()
            )

    db.close()
