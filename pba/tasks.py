import os
from celery import Celery
import requests
from dateutil import parser
from lib.search import Search, ElasticFieldMapper

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from django.conf import settings

app = Celery('pba')

app.config_from_object(settings)


def get_last_bookmark_update_date():
    update_url = '{}posts/update?{}'.format(
        settings.PINBOARD_API_URL,
        settings.PINBOARD_QSTR
    )
    r = requests.get(update_url)
    return parser.parse(r.json()['update_time'])


def get_last_bookmark_archive_date():
    """
    do an Elasticsearch query for the most recent
    bookmark archive date
    return it in the same format as get_last_bookmark_update_date
    for comparison purposes
    """
    s = Search('{}_bookmarks'.format(settings.PINBOARD_USERNAME), {
        "from": 0,
        "size": 1,
        "query": {
            "match_all": {}
        },
        "fields": [
            "time"
        ],
        "sort": {
            "time": {
                "order": "desc"
            }
        }
    }, mappers={
        'time': ElasticFieldMapper.date
    })
    ero = s.search()
    first = next(ero.hits, None)
    return first.time if first is not None else first


def get_bookmark_by_hash(bookmark_hash):
    s = Search('{}_bookmarks'.format(
        settings.PINBOARD_USERNAME
    ))
    return s.get(bookmark_hash, 'bookmark', ['href'])


@app.task
def archive_bookmark(bookmark):
    """
    bookmark is a pinboard api bookmark response
    * see if we have it already indexed by fetching the
    document with that hash from ES - really we're doing this
    to check the url
    * if it's not been indexed or the url has changed,
    fetch the page using wget
        - run goose extractor for the text
        - store the archive files
    * upsert it with doc_as_upsert and detect_noop
    """
    pass


@app.task
def get_posts(start=0, fromdt=None, results=10):
    """
    get some of a users posts from the pinboard api
    we should be calling
    posts/all with start & fromdt & results
    and then calling get_posts again for the next batch
    this may have been called and there are no more bookmarks
    in which case do nothing.
    otherwise we want to loop through and archive the bookmarks
    """
    pass


@app.task
def get_new_bookmarks():
    """
    check to see if we have any new bookmarks,
    get them if so, by making a call to
    get_posts
    """
    if get_last_bookmark_archive_date < get_last_bookmark_update_date:
        get_posts.delay(
            start=0,
            fromdt='<result of get_last_bookmark_archive_date>')
