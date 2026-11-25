"""
Replaces program abbreviations and short forms (BSIT, BS Accountancy, ...) with
the full official program name. Values that do not clearly match one of the
school's programs are left exactly as they are.
"""
from django.db import migrations

from users.student_info import official_program


def use_official_names(apps, schema_editor):
    User = apps.get_model('users', 'User')
    for user in User.objects.exclude(program=''):
        official = official_program(user.program)
        if official and official != user.program:
            user.program = official
            user.save(update_fields=['program'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_student_details'),
    ]

    operations = [
        # Going back leaves the full names in place; nothing is lost.
        migrations.RunPython(use_official_names, migrations.RunPython.noop),
    ]
