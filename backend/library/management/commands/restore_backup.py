"""
Loads a file made by `create_backup` into a new, migrated database, once.

    python manage.py restore_backup backup.json

It refuses to run on a database that already has accounts, so it cannot
overwrite live data or be applied twice. Everything happens in one transaction:
if anything is wrong, the database is left exactly as it was.
"""
import json
from collections import Counter
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.migrations.executor import MigrationExecutor


class Command(BaseCommand):
    help = 'Restore backup.json into an empty, migrated database (one time only).'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='?', default='backup.json')
        parser.add_argument('--yes', action='store_true', help='Do not ask for confirmation.')

    def handle(self, *args, path, yes, **options):
        source = Path(path)
        if not source.is_absolute():
            source = settings.BASE_DIR / source
        if not source.exists():
            raise CommandError(f'{source} was not found.')
        try:
            with source.open(encoding='utf-8') as file:
                expected = Counter(record['model'] for record in json.load(file))
        except (ValueError, KeyError, TypeError) as exc:
            raise CommandError(f'{source} is not a valid backup file: {exc}') from exc

        executor = MigrationExecutor(connection)
        if executor.migration_plan(executor.loader.graph.leaf_nodes()):
            raise CommandError('Run `python manage.py migrate` first.')

        User = get_user_model()
        if User.objects.exists():
            raise CommandError(
                f'Nothing was changed: this database already has {User.objects.count()} '
                'accounts, so the backup was restored already or the database is in use.')

        where = connection.settings_dict.get('HOST') or connection.settings_dict['NAME']
        self.stdout.write(f'Database: {where}')
        self.stdout.write(f'Backup:   {source} ({sum(expected.values())} records)')
        if not yes and input('Type RESTORE to continue: ').strip() != 'RESTORE':
            raise CommandError('Cancelled. Nothing was changed.')

        models = [apps.get_model(label) for label in expected]
        with transaction.atomic():
            # Migrations add default hours, rules and landing content. The
            # backup holds the library's real versions of those records.
            for model in models:
                model._base_manager.all()._raw_delete(connection.alias)
            call_command('loaddata', str(source), verbosity=0)

            for model in models:
                found = model._base_manager.count()
                wanted = expected[model._meta.label_lower]
                if found != wanted:
                    raise CommandError(
                        f'{model._meta.label}: expected {wanted} records, found {found}. '
                        'Nothing was changed.')

        for label, count in sorted(expected.items()):
            self.stdout.write(f'  {label}: {count}')
        self.stdout.write(self.style.SUCCESS('Restore complete.'))
