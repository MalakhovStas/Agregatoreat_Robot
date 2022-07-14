from peewee import SqliteDatabase, IntegrityError, DoesNotExist

from .tables import Bet, BaseModel, conn


class Controller:
    def __init__(self):
        self.bets: Bet = Bet
        self.conn: SqliteDatabase = conn
        self.conn.create_tables([self.bets], safe=True)

    def bet_exists(self, _id: int) -> bool:
        return False if self.bets.get(self.bets.id == _id) else True

    def add_bet(self, bet_id: int, placed: bool = False):
        try:
            self.bets.insert(bet_id=bet_id, placed=placed).execute()
        except IntegrityError:
            pass

    def update_bet_status(self, status: bool, **kwargs):
        try:
            self.bets.update(status=status).where(kwargs).execute()
        except DoesNotExist:
            pass

    def get_bet_status(self, bet_id: int):
        try:
            return self.bets.get(self.bets.bet_id == bet_id).placed
        except DoesNotExist:
            return None
