from quadral_cluster.domain.socionics import Quadra, SocType
from quadral_cluster.services.matchmaking import build_quadra_cluster


def _u(i, t):
    return {"id": i, "socionics_type": t}


def test_quadra_delta_success():
    pool = [
        _u(1, SocType.IEE),
        _u(2, SocType.SLI),
        _u(3, SocType.EII),
        _u(4, SocType.LSE),
        _u(5, SocType.IEE),
    ]
    res = build_quadra_cluster(pool, Quadra.DELTA)
    assert res["ok"] is True
    assert set(res["members"]) <= {1, 2, 3, 4, 5}
    assert len(res["members"]) == 4


def test_quadra_missing_type_fails():
    pool = [
        _u(1, SocType.IEE),
        _u(2, SocType.SLI),
        _u(3, SocType.EII),
    ]
    res = build_quadra_cluster(pool, Quadra.DELTA)
    assert res["ok"] is False
    assert "LSE" in set(res["missing"])
