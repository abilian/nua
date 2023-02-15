import pytest

from nua.orchestrator.resource import Resource
from nua.orchestrator.resource_deps import ResourceDeps


def test_no_deps_1():
    a = Resource({"resource_name": "a", "env": {}})
    resource_deps = ResourceDeps()
    resource_deps.add_resource(a)

    result = resource_deps.solve()
    # result_names = [r.name for r in result]

    assert len(result) == 1


def test_no_deps_2():
    a = Resource({"resource_name": "a", "env": {}})
    b = Resource({"resource_name": "b", "env": {}})
    resource_deps = ResourceDeps()
    resource_deps.add_resource(a)
    resource_deps.add_resource(b)

    result = resource_deps.solve()
    result_names = [r.resource_name for r in result]

    assert result_names == ["a", "b"]


def test_deps_1():
    a = Resource(
        {
            "resource_name": "a",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
            },
        }
    )
    b = Resource({"resource_name": "b", "env": {}})
    resource_deps = ResourceDeps()
    resource_deps.add_resource(a)
    resource_deps.add_resource(b)

    result = resource_deps.solve()
    result_names = [r.resource_name for r in result]

    assert result_names == ["b", "a"]


def test_deps_2():
    a = Resource(
        {
            "resource_name": "a",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
            },
        }
    )
    b = Resource({"resource_name": "b", "env": {}})
    c = Resource(
        {
            "resource_name": "c",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
            },
        }
    )
    resource_deps = ResourceDeps()
    resource_deps.add_resource(a)
    resource_deps.add_resource(b)
    resource_deps.add_resource(c)

    result = resource_deps.solve()
    result_names = [r.resource_name for r in result]

    assert result_names == ["b", "a", "c"]


def test_deps_3():
    a = Resource(
        {
            "resource_name": "a",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
                "v2": {"from": "d", "key": "xxx"},
            },
        }
    )
    b = Resource({"resource_name": "b", "env": {}})
    c = Resource(
        {
            "resource_name": "c",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
            },
        }
    )
    d = Resource(
        {
            "resource_name": "d",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
            },
        }
    )
    resource_deps = ResourceDeps()
    resource_deps.add_resource(a)
    resource_deps.add_resource(b)
    resource_deps.add_resource(c)
    resource_deps.add_resource(d)

    result = resource_deps.solve()
    result_names = [r.resource_name for r in result]

    assert result_names == ["b", "c", "d", "a"]


def test_circular_1():
    a = Resource(
        {
            "resource_name": "a",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
            },
        }
    )
    b = Resource(
        {
            "resource_name": "b",
            "env": {
                "v2": {"from": "a", "key": "xxx"},
            },
        }
    )
    resource_deps = ResourceDeps()
    resource_deps.add_resource(a)
    resource_deps.add_resource(b)

    with pytest.raises(SystemExit):
        resource_deps.solve()


def test_circular_empty():
    a = Resource(
        {
            "resource_name": "a",
            "env": {
                "v1": {"from": "b", "key": "xxx"},
            },
        }
    )
    b = Resource(
        {
            "resource_name": "b",
            "env": {
                "v2": {"from": "unknown", "key": "xxx"},
            },
        }
    )
    resource_deps = ResourceDeps()
    resource_deps.add_resource(a)
    resource_deps.add_resource(b)

    with pytest.raises(SystemExit):
        resource_deps.solve()
