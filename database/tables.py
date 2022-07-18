from peewee import Model, SqliteDatabase, PrimaryKeyField, IntegerField, BooleanField, TextField


conn = SqliteDatabase('main.db')


class BaseModel(Model):
    class Meta:
        database = conn


class Bet(BaseModel):
    id = PrimaryKeyField(null=False)
    bet_id = IntegerField(unique=True, null=False)
    placed = BooleanField(null=False, default=False)


class Data(BaseModel):
    login = TextField()
    password = TextField()
    first_desc = TextField()
    second_desc = TextField()
    certificate_name = TextField()
    only_EAT = TextField()
    tin = TextField()
    bets_to_exclude = TextField()
