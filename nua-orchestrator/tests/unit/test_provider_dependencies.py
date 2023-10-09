import pytest

from nua.orchestrator.provider import Provider
from nua.orchestrator.provider_deps import ProviderDeps


def test_no_deps_1():
    a = Provider({"provider_name": "a", "env": {}})
    provider_deps = ProviderDeps()
    provider_deps.add_provider(a)

    result = provider_deps.solve()
    # result_names = [r.name for r in result]

    assert len(result) == 1


def test_no_deps_2():
    a = Provider({"provider_name": "a", "env": {}})
    b = Provider({"provider_name": "b", "env": {}})
    provider_deps = ProviderDeps()
    provider_deps.add_provider(a)
    provider_deps.add_provider(b)

    result = provider_deps.solve()
    result_names = [r.provider_name for r in result]

    assert result_names == ["a", "b"]


def test_deps_1():
    a = Provider(
        {
            "provider_name": "a",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
            },
        }
    )
    b = Provider({"provider_name": "b", "env": {}})
    provider_deps = ProviderDeps()
    provider_deps.add_provider(a)
    provider_deps.add_provider(b)

    result = provider_deps.solve()
    result_names = [r.provider_name for r in result]

    assert result_names == ["b", "a"]


def test_deps_2():
    a = Provider(
        {
            "provider_name": "a",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
            },
        }
    )
    b = Provider({"provider_name": "b", "env": {}})
    c = Provider(
        {
            "provider_name": "c",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
            },
        }
    )
    provider_deps = ProviderDeps()
    provider_deps.add_provider(a)
    provider_deps.add_provider(b)
    provider_deps.add_provider(c)

    result = provider_deps.solve()
    result_names = [r.provider_name for r in result]

    assert result_names == ["b", "a", "c"]


def test_deps_3():
    a = Provider(
        {
            "provider_name": "a",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
                "v2": {"from": "d", "key": "xxx"},
            },
        }
    )
    b = Provider({"provider_name": "b", "env": {}})
    c = Provider(
        {
            "provider_name": "c",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
            },
        }
    )
    d = Provider(
        {
            "provider_name": "d",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
            },
        }
    )
    provider_deps = ProviderDeps()
    provider_deps.add_provider(a)
    provider_deps.add_provider(b)
    provider_deps.add_provider(c)
    provider_deps.add_provider(d)

    result = provider_deps.solve()
    result_names = [r.provider_name for r in result]

    assert result_names == ["b", "c", "d", "a"]


def test_circular_1():
    a = Provider(
        {
            "provider_name": "a",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
            },
        }
    )
    b = Provider(
        {
            "provider_name": "b",
            "env": {
                "v2": {"from": "a", "key": "xxx"},
            },
        }
    )
    provider_deps = ProviderDeps()
    provider_deps.add_provider(a)
    provider_deps.add_provider(b)

    with pytest.raises(SystemExit):
        provider_deps.solve()


def test_circular_empty():
    a = Provider(
        {
            "provider_name": "a",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
            },
        }
    )
    b = Provider(
        {
            "provider_name": "b",
            "env": {
                "v2": {"from": "unknown", "key": "xxx"},
            },
        }
    )
    provider_deps = ProviderDeps()
    provider_deps.add_provider(a)
    provider_deps.add_provider(b)

    with pytest.raises(SystemExit):
        provider_deps.solve()
