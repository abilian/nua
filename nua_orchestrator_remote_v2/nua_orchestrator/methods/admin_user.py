from copy import deepcopy

from sqlalchemy import create_engine, exc, func, or_
from sqlalchemy.orm import Session
from tinyrpc.dispatch import public

from ..db.model.auth import User
from ..db.store import installed_nua_settings
from ..keys_utils import parse_private_rsa_key_content, public_key_from_rsa_key
from ..rpc_utils import register_methods, rpc_trace

# from ..server_utils.mini_log import log_me


class AdminUser:
    prefix = "user_"

    def __init__(self, config: dict):
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
            data={},
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
    def update(self, update_data: dict) -> None:
        uid = int(update_data["uid"])
        key = update_data["key"]
        value = update_data["value"]
        engine = create_engine(self.url)
        with Session(engine) as session:
            session.query(User).filter(User.id == uid).update({key: value})
            try:
                session.commit()
            except exc.SQLAlchemyError as e:
                raise e

    @public
    @rpc_trace
    def pubkey(self, key_data: dict) -> None:
        username = key_data["username"]
        key_name = key_data["key_name"]
        key_content = key_data["key_content"]
        if not key_name or not username:
            return
        engine = create_engine(self.url)
        with Session(engine) as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                print("User not found.")
            data = deepcopy(user.data)
            pub_keys = data.get("pub_keys", {})
            if key_content == "erase":
                if key_name in pub_keys:
                    del pub_keys[key_name]
            else:
                pub_keys[key_name] = key_content
            data["pub_keys"] = pub_keys
            user.data = data
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

    @public
    @rpc_trace
    def host_add(self, host_data: dict) -> dict:
        username = host_data["username"]
        host_account = host_data["host_account"]
        host_address = host_data["host_address"]
        host_port = host_data["host_port"]
        host_label = host_data["host_label"]
        engine = create_engine(self.url)
        with Session(engine) as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return {"message": "User not found."}
            data = deepcopy(user.data)
            hosts = data.get("hosts", {})
            hosts[host_label] = {
                "address": host_address,
                "account": host_account,
                "port": host_port,
            }
            try:
                session.commit()
            except exc.SQLAlchemyError as e:
                raise e

    @public
    @rpc_trace
    # FIXME: command to move elsewhere, maybe not public or in external script
    def nua_pubkey(self, user_data: dict) -> dict:
        # username not usefull here, username only for auth:
        # username = user_data.get("username")
        data = installed_nua_settings() or {}
        priv_key = data.get("hosts", {}).get("host_priv_key_blob", "")
        if not priv_key:
            raise ValueError("No Nua key found in settings.")
        key_instance = parse_private_rsa_key_content(priv_key)
        pub_key = public_key_from_rsa_key(key_instance)
        return {"nua_pub": pub_key}


register_methods(AdminUser)
