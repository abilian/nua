from nua.orchestrator.db.model.image import Image


def test_save(db_session):
    image = Image(id_sha="xxx", nua_tag="yyy")
    db_session.add(image)
    db_session.commit()
