import secrets
import string

MIN_DIGIT = 3


def gen_password(length: int=16) -> str:
    """Generate random passord.

    With ascii and digits, lenght 16, log10(62**16) ~ 28, and basic constraints.
    """
    alphabet = string.ascii_letters + string.digits
    while True:
        password = "".join(secrets.choice(alphabet) for i in range(length))
        if (
            any(char.islower() for char in password)
            and any(char.isupper() for char in password)
            and tuple(char.isdigit() for char in password).count(True) >= MIN_DIGIT
        ):
            break
    return password
