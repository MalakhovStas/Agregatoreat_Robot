from typing import Tuple

from peewee import SqliteDatabase, IntegrityError, DoesNotExist

from .tables import Bet, conn, Data


class Controller:
    def __init__(self) -> None:
        self.bets: Bet = Bet
        self.conn: SqliteDatabase = conn
        self.conn.create_tables([self.bets], safe=True)

    def bet_exists(self, _id: int) -> bool:
        return False if self.bets.get(self.bets.id == _id) else True

    def add_bet(self, bet_id: int, placed: bool = False) -> None:
        try:
            self.bets.insert(bet_id=bet_id, placed=placed).execute()
        except IntegrityError:
            pass

    def update_bet_status(self, status: bool, **kwargs) -> None:
        try:
            self.bets.update(status=status).where(kwargs).execute()
        except DoesNotExist:
            pass

    def get_bet_status(self, bet_id: int) -> None:
        try:
            return self.bets.get(self.bets.bet_id == bet_id).placed
        except DoesNotExist:
            return None


class DataController:
    def __init__(self) -> None:
        self.data: Data = Data
        self.conn: SqliteDatabase = conn
        self.conn.create_tables([self.data], safe=True)

    def add_data(self, login: str, password: str, first_desc: str, second_desc: str, certificate_name: str,
                 only_EAT: str, tin: str, bets_to_exclude: str) -> None:
        try:
            self.data.insert(login=login, password=password, first_desc=first_desc, second_desc=second_desc,
                             certificate_name=certificate_name, only_EAT=only_EAT, tin=tin,
                             bets_to_exclude=bets_to_exclude).execute()
        except IntegrityError:
            pass

    def update_data(self, login: str, password: str, first_desc: str, second_desc: str, certificate_name: str,
                    only_EAT: str, tin: str, bets_to_exclude: str) -> None:
        try:
            self.data.update(login=login, password=password, first_desc=first_desc, second_desc=second_desc,
                             certificate_name=certificate_name, only_EAT=only_EAT, tin=tin,
                             bets_to_exclude=bets_to_exclude).where(self.data.get_by_id(1)).execute()
        except DoesNotExist:
            pass

    def get_data(self) -> Tuple | None:
        try:
            return self.data.get().login, self.data.get().password, self.data.get().first_desc, \
                   self.data.get().second_desc, self.data.get().certificate_name, self.data.get().only_EAT, \
                   self.data.get().tin, self.data.get().bets_to_exclude

        except DoesNotExist:
            return None
