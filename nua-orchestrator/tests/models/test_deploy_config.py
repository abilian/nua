from nua.orchestrator.db.model.deployconfig import DeployConfig


def test_save(db_session):
    deploy_config = DeployConfig()
    db_session.add(deploy_config)
    db_session.commit()
