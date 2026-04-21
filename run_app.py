import argparse
import os
from pathlib import Path


def configure_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "brandregistry.settings")
    os.environ.setdefault("DESKTOP_LOCAL_MODE", "1")
    os.environ.setdefault("DJANGO_DEBUG", "0")

    import django

    django.setup()


def parse_args():
    parser = argparse.ArgumentParser(description="Start the Brand Registry desktop backend.")
    parser.add_argument(
        "--host",
        default=os.getenv("APP_HOST", "127.0.0.1"),
        help="The host interface for the local desktop server.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("APP_PORT", "8000")),
        help="The port for the local desktop server.",
    )
    return parser.parse_args()


def ensure_database_is_ready():
    from django.conf import settings
    from django.core.management import call_command
    from django.db import connections
    from django.db.migrations.executor import MigrationExecutor

    db_path = Path(settings.DATABASES["default"]["NAME"])
    if not db_path.exists():
        print("Database not found. Creating and applying migrations...")
        call_command("migrate", "--noinput", verbosity=1)
        print("Database created successfully.")
        return

    connection = connections["default"]
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    has_pending_migrations = bool(executor.migration_plan(targets))

    if has_pending_migrations:
        print("Pending migrations found. Applying...")
        call_command("migrate", "--noinput", verbosity=0)
        print("Migrations applied successfully.")
    else:
        print("Database is up to date.")


def main():
    args = parse_args()
    configure_django()
    ensure_database_is_ready()

    from brandregistry.wsgi import application
    from waitress import serve

    print(f"Starting server on http://{args.host}:{args.port} ...")
    serve(application, host=args.host, port=args.port, threads=6)


if __name__ == "__main__":
    main()
