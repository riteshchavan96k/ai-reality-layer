from backend.app.main import app


def test_reality_state_route_exists():
    routes = {(route.path, tuple(route.methods or ())) for route in app.routes}
    assert ("/api/v1/reality-state", ("POST",)) in routes


def test_reality_state_route_is_distinct_from_solve():
    paths = [route.path for route in app.routes]
    assert "/api/v1/solve" in paths
    assert "/api/v1/reality-state" in paths
    assert paths.index("/api/v1/solve") != paths.index("/api/v1/reality-state")
