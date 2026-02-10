"""CLI entrypoint for repokit-only commands."""
from __future__ import annotations

import argparse
import sys

ALIASES = {
    "deps": "deps-update",
    "readme": "readme-update",
    "templates": "templates-reset",
    "ex-code": "examples-code",
    "ex-test": "examples-test",
}


def _dispatch(func, argv: list[str], prog: str) -> None:
    old_argv = sys.argv
    try:
        sys.argv = [prog, *argv]
        func()
    finally:
        sys.argv = old_argv


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="repokit", description="repokit core commands"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    commands = [
        "copy",
        "deps-update",
        "readme-update",
        "templates-reset",
        "examples-code",
        "examples-test",
        "git-config",
        "ci-control",
        "lint",
        "agent",
        # Short aliases
        "deps",
        "readme",
        "templates",
        "ex-code",
        "ex-test",
    ]
    for name in commands:
        p = sub.add_parser(name)
        p.add_argument("args", nargs=argparse.REMAINDER)

    ns = parser.parse_args()
    cmd = ALIASES.get(ns.command, ns.command)

    if cmd == "copy":
        from . import scp

        _dispatch(scp.main, ns.args, "repokit copy")
    elif cmd == "deps-update":
        from . import deps

        _dispatch(deps.main, ns.args, "repokit deps-update")
    elif cmd == "readme-update":
        from .readme import template as readme_template

        _dispatch(readme_template.main, ns.args, "repokit readme-update")
    elif cmd == "templates-reset":
        from .templates import code as templates_code

        _dispatch(templates_code.main, ns.args, "repokit templates-reset")
    elif cmd == "examples-code":
        from .templates import example as templates_example

        _dispatch(templates_example.main, ns.args, "repokit examples-code")
    elif cmd == "examples-test":
        from .templates import tests as templates_tests

        _dispatch(templates_tests.main, ns.args, "repokit examples-test")
    elif cmd == "git-config":
        from . import repos

        _dispatch(repos.main, ns.args, "repokit git-config")
    elif cmd == "ci-control":
        from . import ci

        _dispatch(ci.ci_control, ns.args, "repokit ci-control")
    elif cmd == "lint":
        from . import linting

        _dispatch(linting.main, ns.args, "repokit lint")
    elif cmd == "agent":
        from . import agent

        _dispatch(agent.main, ns.args, "repokit agent")


if __name__ == "__main__":
    main()