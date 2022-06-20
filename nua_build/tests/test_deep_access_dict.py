from nua_build.deep_access_dict import DeepAccessDict


def test_ad_empty():
    ad = DeepAccessDict()
    result = repr(ad)

    assert result == "DeepAccessDict({})"


def test_ad_base():
    d = {"a": 1}
    ad = DeepAccessDict(d)
    result = repr(ad)

    assert result == "DeepAccessDict({'a': 1})"

    assert ad.get() == d
    assert ad.get("a") == 1
    assert ad.get("x") == None


def test_ad_nb():
    d = {5: 1}
    ad = DeepAccessDict(d)

    assert ad.get(5) == 1


def test_ad_set():
    d = {"a": 1}
    ad = DeepAccessDict(d)
    ad.set("b", "val")

    assert ad.get("b") == "val"


def test_ad_delete():
    d = {"a": 1}
    ad = DeepAccessDict(d)
    ad.set("b", "val")
    ad.delete("b")

    assert ad.get("b") == None


def test_ad_len():
    d = {"a": 1}
    ad = DeepAccessDict(d)
    ad.set("b", "val")

    assert len(ad) == 2


def test_ad_in_ad():
    d = {"a": 1}
    ad = DeepAccessDict(d)
    ad2 = DeepAccessDict({"ad2": 42})
    ad.set("b", ad2)
    result = ad.get("b")

    assert isinstance(result, dict)
    assert result == {"ad2": 42}


def test_ad_multi_set():
    d = {"a": 1}
    ad = DeepAccessDict(d)
    ad.set("b", "c", "d", 4, "e", "val")

    assert ad.get("b", "c", "d", 4, "e") == "val"


def test_ad_multi_set_2():
    d = {"a": 1}
    ad = DeepAccessDict(d)
    ad.set("b", "c", "d", 4, "e", "val")
    ad.set("b", "c", "x", "y", 0)

    assert ad.get() == {"a": 1, "b": {"c": {"d": {4: {"e": "val"}}, "x": {"y": 0}}}}
    assert ad.get("b", "c", "d") == {4: {"e": "val"}}


def test_ad_multi_set_3():
    d = {"a": 1}
    ad = DeepAccessDict(d)
    ad.set("b", "c", "d", 4, "e", "val")
    ad.set("b", "c", "x", "y", 0)
    ad.set("b", "c", "other")

    assert ad.get() == {"a": 1, "b": {"c": "other"}}
    assert ad.get("b", "c") == "other"


def test_ad_multi_set_4():
    d = {"a": 1}
    ad = DeepAccessDict(d)
    ad.set("b", "c", "d", 4, "e", "val")
    d2 = {"xx": 5, "yy": 6}
    ad.set("b", "t", d2)

    assert ad.get() == {
        "a": 1,
        "b": {"c": {"d": {4: {"e": "val"}}}, "t": {"xx": 5, "yy": 6}},
    }
    assert ad.get("b", "t", "xx") == 5


def test_ad_multi_set_5():
    d = {"a": 1}
    ad = DeepAccessDict(d)
    ad.set("b", "c", "d", 4, "e", "val")
    ad.set("b", (4, 5), [3, 42])

    assert (
        ad.get()
        == {"a": 1, "b": {"c": {"d": {4: {"e": "val"}}}, (4, 5): [3, 42]}}
        != {"b": {"c": "other"}}
    )
    assert ad.get("b", (4, 5))[1] == 42


def test_ad_multi_delete_2():
    d = {"a": 1}
    ad = DeepAccessDict(d)
    ad.set("b", "c", "d", 4, "e", "val")
    ad.set("b", "c", "x", "y", 0)
    ad.delete("b", "nokey")
    ad.delete("b", "c")

    assert ad.get() == {"a": 1, "b": {}}
