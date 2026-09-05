"""Pytest wiring for the exploit suite.

Default mode ("demo"): each test proves the exploit lands on the vulnerable
app AND is repelled by the hardened app -- 10 greens.

Lab mode: ``pytest --target=vulnerable`` asserts the *hardened contract*
against the vulnerable build (10 reds); ``--target=hardened`` re-runs the
same contract (10 greens). That is the exploit-then-fix gauntlet.
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--target",
        action="store",
        default="demo",
        choices=["demo", "vulnerable", "hardened"],
        help="demo: prove exploit+fix; vulnerable/hardened: assert contract",
    )


@pytest.fixture()
def target(request: pytest.FixtureRequest) -> str:
    return str(request.config.getoption("--target"))
