from sqlalchemy import create_engine, exc, func, or_
from sqlalchemy.orm import Session
from tinyrpc.dispatch import public

from ..model.auth import User
from ..rpc_utils import register_methods, rpc_trace


class AdminUser:
    def __init__(self, config):
        self.config = config
        self.url = config["db"]["url"]
        # self.session = None

    @public
    @rpc_trace
    def add(self, user_data: dict) -> dict:
        # def add(self, hmac_sig: str, user_data: dict) -> dict:
        engine = create_engine(self.url)
        new_user = User(
            id=str(user_data.get("id", 0)),
            username=str(user_data.get("username", "")),
            email=str(user_data.get("email", "")),
            password=str(user_data.get("password", "")),
            salt=str(user_data.get("salt", "")),
            role=str(user_data.get("role", "user")),
        )
        with Session(engine) as session:
            new_user.id = self.validate_new_id(session, int(user_data.get("id", -1)))
            session.add(new_user)
            try:
                session.commit()
            except exc.SQLAlchemyError as e:
                raise e
            # to get fields like "added timestamp":
            added_user = session.query(User).get(new_user.id)
            user_as_dict = added_user.to_dict()
        return user_as_dict

    @public
    @rpc_trace
    def count(self) -> int:
        engine = create_engine(self.url)
        with Session(engine) as session:
            cnt = session.query(User).count()
        return int(cnt)

    @public
    @rpc_trace
    def list(self, request: dict = None) -> list:
        if not request:
            request = {}
        engine = create_engine(self.url)
        all = request.get("all") or False
        ids = request.get("ids") or []
        names = request.get("names") or []
        mails = request.get("mails") or []
        if all or not (ids or names or mails):
            with Session(engine) as session:
                users = session.query(User).order_by(User.id).all()
        else:
            with Session(engine) as session:
                users = (
                    session.query(User)
                    .filter(
                        or_(
                            User.id.in_(ids),
                            User.username.in_(names),
                            User.email.in_(mails),
                        )
                    )
                    .order_by(User.id)
                    .all()
                )

        return [u.to_dict() for u in users]

    @public
    @rpc_trace
    def update(self, id: int, key: str, value: str) -> None:
        engine = create_engine(self.url)
        with Session(engine) as session:
            session.query(User).filter(User.id == id).update({key: value})
            try:
                session.commit()
            except exc.SQLAlchemyError as e:
                raise e

    @public
    @rpc_trace
    def delete(self, ids: list) -> None:
        if not ids:
            return
        engine = create_engine(self.url)
        with Session(engine) as session:
            session.query(User).filter(User.id.in_(ids)).delete()
            try:
                session.commit()
            except exc.SQLAlchemyError as e:
                raise e
        return

    @public
    @rpc_trace
    def delete_all(self) -> None:
        engine = create_engine(self.url)
        with Session(engine) as session:
            session.query(User).delete()
            try:
                session.commit()
            except exc.SQLAlchemyError as e:
                raise e
        return

    def validate_new_id(self, session, new_id: int) -> int:
        if new_id < 0 or self.id_already_used(session, new_id):
            new_id = self.max_used_id(session) + 1
        return new_id

    @staticmethod
    def id_already_used(session, new_id: str) -> int:
        return session.query(User.id).filter(User.id == new_id).count()

    @staticmethod
    def max_used_id(session) -> int:
        return session.query(func.max(User.id)).scalar() or 0


register_methods(AdminUser, "user_")
