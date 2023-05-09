from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from .extensions import db


class Book(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author: Mapped[str]
    pages_num: Mapped[int]
    review: Mapped[str]
    date_added: Mapped[datetime] = mapped_column(default=datetime.now)
