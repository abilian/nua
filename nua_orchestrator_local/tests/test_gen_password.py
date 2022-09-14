import string

from nua_orchestrator_local.gen_password import gen_password


def test_gen_password_len():
    """Expect len to be 16."""
    pwd = gen_password()

    assert len(pwd) >= 16


def test_gen_password_content():
    """Expect chars and digit."""
    pwd = gen_password()
    for char in pwd:
        assert char in string.ascii_letters or char in string.digits


def test_gen_password_different():
    """Test should fail 1/10e28."""
    pwd1 = gen_password()
    pwd2 = gen_password()

    assert pwd1 != pwd2
