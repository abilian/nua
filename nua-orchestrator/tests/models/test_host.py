from nua.orchestrator.db.model.host import Host


def test_save(db_session):
    host = Host(hostname="example.com")
    db_session.add(host)
    db_session.commit()
