"""Legacy entry point — kept for backwards compatibility.

Seed logic now lives in `backend/seeds/`. Prefer:

    python -m seeds.run_all     # all seeds
    python -m seeds.users       # users only
    python -m seeds.semesters   # semesters only
"""
from seeds.run_all import main

if __name__ == "__main__":
    main()
