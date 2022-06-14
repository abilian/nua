from .connect import Session
from .model.images import Images


def find_image_nua_tag(tag):
    """Find a Nua image in the local DB by Nua id."""
    with Session() as session:
        return session.query(Images).filter_by(nua_tag=tag).first()


def store_image(id_sha="", nua_id=0, nua_tag="", created="", size=0, nua_version=""):
    """Store a Nua image in the local DB."""
    new_image = Images(
        id_sha=id_sha,
        nua_id=nua_id,
        nua_tag=nua_tag,
        created=created,
        size=size,
        nua_version=nua_version,
    )
    with Session() as session:
        # enforce unicity
        existing = session.query(Images).filter_by(nua_tag=nua_tag).first()
        if existing:
            session.delete(existing)
        existing = session.query(Images).filter_by(id_sha=id_sha).first()
        if existing:
            session.delete(existing)
        session.add(new_image)
        session.commit()


def print_images():
    """Print all Nua images."""
    with Session() as session:
        images = session.query(Images).all()
        for img in images:
            print(
                f"{img.id_sha[7:15]}  {img.nua_tag:<40}  {img.created}  {img.size}MiB"
            )


def available_images():
    """Docker images ready to be mounted by Nua."""
    with Session() as session:
        images = session.query(Images).all()
        return [i for i in images if i.nua_id not in {"nua-min", "nua-base"}]
