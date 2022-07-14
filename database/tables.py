from peewee import Model, SqliteDatabase, PrimaryKeyField, IntegerField, BooleanField


conn = SqliteDatabase('main.db')


class BaseModel(Model):
    class Meta:
        database = conn


class Bet(BaseModel):
    id = PrimaryKeyField(null=False)
    bet_id = IntegerField(unique=True, null=False)
    placed = BooleanField(null=False, default=False)
