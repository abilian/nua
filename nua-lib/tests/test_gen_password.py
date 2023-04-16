import string

from nua.lib.gen_password import gen_password, gen_randint


def test_gen_password_len():
    """Expect len to be 24."""
    pwd = gen_password()

    assert len(pwd) >= 24


def test_gen_password_content():
    """Expect chars and digit."""
    pwd = gen_password()
    for char in pwd:
        assert char in string.ascii_letters or char in string.digits


def test_gen_password_different():
    """Test should fail 1/10e43."""
    pwd1 = gen_password()
    pwd2 = gen_password()

    assert pwd1 != pwd2


def test_gen_randint():
    """Chck result is int."""
    randint = gen_randint()

    assert isinstance(randint, int)
    assert randint >= 0
