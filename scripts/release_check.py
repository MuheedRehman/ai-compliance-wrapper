import subprocess
import sys


def run(command: list[str]) -> None:
    print(f"\n>>> {' '.join(command)}")
    result = subprocess.run(command, shell=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    print("Running Sprint 6B release gate...")
    run([sys.executable, "-m", "pytest"])
    run(["alembic", "upgrade", "head"])
    run(["alembic", "downgrade", "-1"])
    run(["alembic", "upgrade", "head"])
    print("\nRelease gate passed.")


if __name__ == "__main__":
    main()
