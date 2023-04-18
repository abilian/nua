from nua.orchestrator.db.model.instance import Instance


def test_save(db_session):
    instance = Instance()
    db_session.add(instance)
    db_session.commit()
