from unittest import skip

from nua.orchestrator.db.store import store_image


@skip
def test_store(db_session):
    store_image()
