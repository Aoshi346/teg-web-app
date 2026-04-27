"""Run every seed module in the right order. Safe to re-run."""
from . import _bootstrap

_bootstrap.setup()

from .users import seed_users  # noqa: E402
from .semesters import seed_semesters  # noqa: E402


def main() -> None:
    seed_users()
    seed_semesters()
    print("\nDone. Login with admin@example.com / 123")


if __name__ == "__main__":
    main()
