"""
Writes the whole database to a JSON file that `restore_backup` can load.

    python manage.py create_backup

Archived seats, zones, floors and rooms are included: past reservations point
to them. Primary keys are kept, so links such as /reservations/12 still work.

Left out because Django rebuilds them or they are worthless after a move:
content types, permissions, sessions and issued login tokens.
"""
import json
import os
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

EXCLUDED = ['contenttypes', 'auth.permission', 'sessions', 'token_blacklist']


class Command(BaseCommand):
    help = 'Back up the database to backend/backup.json.'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='?', default='backup.json')
        parser.add_argument(
            '--replace', action='store_true',
            help='Replace an existing file, keeping it as <name>.previous.json.')

    def handle(self, *args, path, replace, **options):
        target = Path(path)
        if not target.is_absolute():
            target = settings.BASE_DIR / target
        if target.exists() and not replace:
            raise CommandError(
                f'{target} already exists. Move it somewhere safe, or use --replace.')

        temporary = target.with_name(f'{target.name}.tmp')
        try:
            # One transaction, so the file is a consistent snapshot. UTF-8 is
            # explicit because Windows would otherwise use its legacy encoding.
            with transaction.atomic(), temporary.open('w', encoding='utf-8', newline='\n') as out:
                call_command(
                    'dumpdata', exclude=EXCLUDED, use_natural_foreign_keys=True,
                    use_base_manager=True, indent=2, stdout=out,
                )
            with temporary.open(encoding='utf-8') as saved:
                records = json.load(saved)
            if target.exists():
                os.replace(target, target.with_name(f'{target.stem}.previous.json'))
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)

        for label, count in sorted(Counter(r['model'] for r in records).items()):
            self.stdout.write(f'  {label}: {count}')
        self.stdout.write(self.style.SUCCESS(f'{len(records)} records saved to {target}'))
        self.stdout.write(
            'Uploaded photos are not in this file. Back up the media folder separately.')
