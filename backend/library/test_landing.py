"""The public landing page and its management in Library Settings."""
import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from config.test_utils import PortalTestCase
from library.models import LandingItem, LibraryPersonnel, LibraryProfile

MEDIA = tempfile.mkdtemp(prefix='landing-test-media-')


def png(name='photo.png', size=(40, 40)):
    buffer = io.BytesIO()
    Image.new('RGB', size, (16, 52, 121)).save(buffer, 'PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT=MEDIA)
class LandingPageTests(PortalTestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def test_initial_content_is_the_library_information_board(self):
        profile = LibraryProfile.load()
        self.assertEqual(profile.name, 'DLL Library')
        self.assertEqual(profile.institution, 'Dalubhasaan ng Lungsod ng Lucena')
        self.assertEqual(LandingItem.objects.filter(section='service').count(), 5)
        self.assertEqual(LandingItem.objects.filter(section='card').count(), 4)
        self.assertEqual(LandingItem.objects.filter(section='rule').count(), 6)
        self.assertEqual(LibraryPersonnel.objects.count(), 5)

    def test_anyone_can_read_the_landing_page_without_signing_in(self):
        response = self.client.get('/api/library/public/')
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data['profile']['name'], 'DLL Library')
        self.assertEqual(data['services'][0]['title'],
                         'Answering requests for information/resources')
        self.assertEqual(data['rules'][0]['title'], 'No Library Card No Entry')
        self.assertEqual(data['personnel'][0]['position'], 'Librarian')
        self.assertEqual(len(data['hours']), 7)
        self.assertEqual(data['time_zone'], 'Asia/Manila')

    def test_a_stale_token_does_not_break_the_public_page(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer not-a-real-token')
        self.assertEqual(self.client.get('/api/library/public/').status_code, 200)

    def test_landing_page_shows_the_same_hours_that_reservations_use(self):
        self.login_as(self.admin)
        hours = self.client.get('/api/library/hours/').data
        hours[0]['opens_at'], hours[0]['closes_at'] = '07:00', '19:00'
        self.assertEqual(self.client.put('/api/library/hours/', hours).status_code, 200)
        self.client.force_authenticate(user=None)
        monday = self.client.get('/api/library/public/').data['hours'][0]
        self.assertEqual((monday['opens_at'], monday['closes_at']), ('07:00', '19:00'))

    def test_admin_edits_information_and_lists(self):
        self.login_as(self.admin)
        saved = self.client.patch('/api/library/profile/', {
            'tagline': 'Redefines Possibilities', 'email': 'library@example.edu'})
        self.assertEqual(saved.status_code, 200, saved.data)
        created = self.client.post('/api/library/landing-items/', {
            'section': 'service', 'title': 'Thesis consultation', 'description': 'By appointment.'})
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data['order'], 5)  # after the five existing services
        item_id = created.data['id']
        self.assertEqual(self.client.patch(
            f'/api/library/landing-items/{item_id}/', {'title': 'Thesis help'}).status_code, 200)

        public = self.client.get('/api/library/public/').data
        self.assertEqual(public['profile']['email'], 'library@example.edu')
        self.assertEqual(public['services'][-1]['title'], 'Thesis help')
        self.assertEqual(public['services'][-1]['description'], 'By appointment.')

        self.assertEqual(self.client.delete(f'/api/library/landing-items/{item_id}/').status_code, 204)
        self.assertEqual(len(self.client.get('/api/library/public/').data['services']), 5)

    def test_reorder(self):
        self.login_as(self.admin)
        rules = self.client.get('/api/library/landing-items/', {'section': 'rule'}).data
        ids = [rule['id'] for rule in rules][::-1]
        response = self.client.post('/api/library/landing-items/reorder/', {'ids': ids})
        self.assertEqual(response.status_code, 200)
        public_rules = self.client.get('/api/library/public/').data['rules']
        self.assertEqual(public_rules[0]['title'], 'Use the library for academic purposes')

    def test_validation(self):
        self.login_as(self.admin)
        self.assertEqual(self.client.post(
            '/api/library/landing-items/', {'section': 'other', 'title': 'x'}).status_code, 400)
        self.assertEqual(self.client.post(
            '/api/library/landing-items/', {'section': 'rule', 'title': ''}).status_code, 400)
        self.assertEqual(self.client.patch(
            '/api/library/profile/', {'email': 'not-an-email'}).status_code, 400)

    def test_personnel_photo_upload_replace_and_remove(self):
        self.login_as(self.admin)
        created = self.client.post('/api/library/personnel/', {
            'name': 'Ms. Test', 'position': 'Library Staff', 'photo': png()}, format='multipart')
        self.assertEqual(created.status_code, 201, created.data)
        self.assertTrue(created.data['photo'].startswith('/media/personnel/'))
        person = f'/api/library/personnel/{created.data["id"]}/'
        replaced = self.client.patch(person, {'photo': png('new.png')}, format='multipart')
        self.assertIn('new', replaced.data['photo'])
        removed = self.client.patch(person, {'photo': None}, format='json')
        self.assertIsNone(removed.data['photo'])

    def test_landing_photo_upload_and_bad_files(self):
        self.login_as(self.admin)
        ok = self.client.post('/api/library/photos/', {
            'image': png(), 'caption': 'Reading area'}, format='multipart')
        self.assertEqual(ok.status_code, 201, ok.data)
        self.assertEqual(self.client.get('/api/library/public/').data['photos'][0]['caption'],
                         'Reading area')
        not_an_image = SimpleUploadedFile('notes.png', b'hello', content_type='image/png')
        self.assertEqual(self.client.post(
            '/api/library/photos/', {'image': not_an_image}, format='multipart').status_code, 400)
        wrong_type = SimpleUploadedFile('script.svg', b'<svg/>', content_type='image/svg+xml')
        self.assertEqual(self.client.post(
            '/api/library/photos/', {'image': wrong_type}, format='multipart').status_code, 400)

    def test_only_the_admin_can_change_anything(self):
        writes = [
            ('patch', '/api/library/profile/', {'name': 'Hacked'}),
            ('post', '/api/library/landing-items/', {'section': 'rule', 'title': 'x'}),
            ('post', '/api/library/personnel/', {'name': 'x', 'position': 'y'}),
            ('post', '/api/library/landing-items/reorder/', {'ids': [1]}),
            ('delete', f'/api/library/landing-items/{LandingItem.objects.first().pk}/', None),
        ]
        for user in (self.student, self.assistant, self.librarian):
            self.login_as(user)
            for method, url, body in writes:
                response = getattr(self.client, method)(url, body)
                self.assertEqual(response.status_code, 403, (user.role, url))
        self.client.force_authenticate(user=None)
        for method, url, body in writes:
            self.assertEqual(getattr(self.client, method)(url, body).status_code, 401, url)
        self.assertEqual(LibraryProfile.load().name, 'DLL Library')
        self.assertEqual(LandingItem.objects.count(), 15)
