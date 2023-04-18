from nua.orchestrator.db.model.setting import Setting


def test_save(db_session):
    setting = Setting()
    db_session.add(setting)
    db_session.commit()
