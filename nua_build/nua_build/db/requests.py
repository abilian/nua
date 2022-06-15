from .connect import Session
from .model.image import Image
from .model.setting import Setting


def find_image_nua_tag(tag):
    """Find a Nua image in the local DB by Nua id."""
    with Session() as session:
        return session.query(Image).filter_by(nua_tag=tag).first()


def store_image(id_sha="", nua_tag="", app_id="", created="", size=0, nua_version=""):
    """Store a Nua image in the local DB."""
    new_image = Image(
        id_sha=id_sha,
        nua_tag=nua_tag,
        app_id=app_id,
        created=created,
        size=size,
        nua_version=nua_version,
    )
    with Session() as session:
        # enforce unicity
        existing = session.query(Image).filter_by(nua_tag=nua_tag).first()
        if existing:
            session.delete(existing)
        existing = session.query(Image).filter_by(id_sha=id_sha).first()
        if existing:
            session.delete(existing)
        session.add(new_image)
        session.commit()


def print_images():
    """Print all Nua images."""
    with Session() as session:
        images = session.query(Image).all()
        for img in images:
            print(
                f"{img.id_sha[7:15]}  {img.nua_tag:<40}  {img.created}  {img.size}MiB"
            )


def available_images():
    """Docker images ready to be mounted by Nua."""
    internals = {"nua-min", "nua-base"}
    with Session() as session:
        images = session.query(Image).all()
        return [i for i in images if i.app_id not in internals]
