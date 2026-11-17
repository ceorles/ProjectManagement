from django.db import migrations

# Taken word for word from the DLL Library information board. The Admin can
# change all of it in Library Settings.
PROFILE = {
    'name': 'DLL Library',
    'tagline': 'Redefines Possibilities',
    'introduction': (
        'Our Library aims to provide comprehensive resources and services in support of '
        "the institution's research, teaching, and learning needs."
    ),
    'institution': 'Dalubhasaan ng Lungsod ng Lucena',
    'address': 'Former Lucena City Hall Annex Bldg., Brgy. Isabang, Lucena City',
    'phone': '(042) 797-1671 (Tel. and Fax)',
    'facebook_page': '@DLL-Library',
}
SERVICES = [
    'Answering requests for information/resources',
    'Book Circulation',
    'Current Awareness',
    'Online Library Services',
    'Outside Researchers Service',
]
CARD = [
    'Fill out the library issuance form',
    'Bring 1x1 ID picture',
    'Validate your LC every semester',
    'If lost or fully damaged, you have to pay a replacement fee',
]
RULES = [
    'No Library Card No Entry',
    'No loud noises or disturbances',
    'No food or drinks allowed inside',
    'Return books on time',
    'Keep the library clean and tidy',
    'Use the library for academic purposes',
]
PERSONNEL = [
    ('Ms. Mjie', 'Librarian'),
    ('Ms. Clyde', 'Librarian'),
    ('Ms. Cora', 'Library Staff'),
    ('Ms. Les', 'Library Staff'),
    ('Mr. Brayan', 'Library Staff'),
]


def create(apps, schema_editor):
    LibraryProfile = apps.get_model('library', 'LibraryProfile')
    LandingItem = apps.get_model('library', 'LandingItem')
    LibraryPersonnel = apps.get_model('library', 'LibraryPersonnel')

    if not LibraryProfile.objects.filter(pk=1).exists():
        LibraryProfile.objects.create(pk=1, **PROFILE)
    if not LandingItem.objects.exists():
        for section, titles in (('service', SERVICES), ('card', CARD), ('rule', RULES)):
            LandingItem.objects.bulk_create([
                LandingItem(section=section, title=title, order=index)
                for index, title in enumerate(titles)
            ])
    if not LibraryPersonnel.objects.exists():
        LibraryPersonnel.objects.bulk_create([
            LibraryPersonnel(name=name, position=position, order=index)
            for index, (name, position) in enumerate(PERSONNEL)
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0005_landing_page_content'),
    ]

    operations = [
        migrations.RunPython(create, migrations.RunPython.noop),
    ]
