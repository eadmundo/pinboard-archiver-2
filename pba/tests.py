import unittest
import tasks
import vcr
import fudge
from rawes.elastic_exception import ElasticException


class TestTasks(unittest.TestCase):

    @vcr.use_cassette('fixtures/pinboard/posts_update.yaml',
                      filter_query_parameters=['auth_token'])
    def test_get_last_update_date(self):
        self.assertEqual(
            tasks.get_last_bookmark_update_date().isoformat(),
            '2015-06-08T20:46:44+00:00'
        )

    @vcr.use_cassette('fixtures/elasticsearch/posts_update.yaml')
    def test_get_last_bookmark_archive_date(self):
        self.assertEqual(
            tasks.get_last_bookmark_archive_date().isoformat(),
            '2015-05-28T15:36:55+00:00'
        )

    @vcr.use_cassette('fixtures/elasticsearch/existing_bookmark.yaml')
    def test_existing_get_bookmark_by_hash(self):
        bookmark_hash = '633b94156b1b857631a57da512746326'
        doc = tasks.get_bookmark_by_hash(bookmark_hash)
        self.assertTrue(doc.found)
        self.assertEqual(doc.id, bookmark_hash)
        self.assertEqual(doc.href, "http://www.example.com/bookmark")

    @vcr.use_cassette('fixtures/elasticsearch/missing_bookmark.yaml')
    def test_missing_get_bookmark_by_hash(self):
        doc = tasks.get_bookmark_by_hash('78f80a45914699c060ba44dbdf36f4c9')
        self.assertFalse(doc.found)

    @vcr.use_cassette('fixtures/elasticsearch/error_getting_bookmark.yaml')
    @fudge.patch('tasks.settings')
    def test_error_get_bookmark_by_hash(self, fake_settings):
        (fake_settings.has_attr(PINBOARD_USERNAME='fake_user'))
        with self.assertRaises(ElasticException) as ex:
            tasks.get_bookmark_by_hash('78f80a45914699c060ba44dbdf36f4c9')
        self.assertEqual(ex.exception.status_code, 404)

if __name__ == '__main__':
    unittest.main()
