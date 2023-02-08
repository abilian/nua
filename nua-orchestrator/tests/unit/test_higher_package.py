from nua.orchestrator.higher_package import higher_package


def test_not_listed():
    input_name = "unknown"
    required_version = ">=10"
    expected = {}

    result = higher_package(input_name, required_version)

    assert result == expected


def test_postgres():
    input_name = "postgres"
    required_version = ">=10"
    expected = "15.1"

    result = higher_package(input_name, required_version)

    assert result["version"] == expected


def test_postgres_max():
    input_name = "postgres"
    required_version = ">=10,<15"
    expected = "14.6"

    result = higher_package(input_name, required_version)

    assert result["version"] == expected


def test_postgres_no_version():
    input_name = "postgres"
    required_version = ">=18"
    expected = None

    result = higher_package(input_name, required_version)

    assert result.get("version") == expected
