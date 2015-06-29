import json
import rawes
from rawes.elastic_exception import ElasticException
from django.conf import settings
from dateutil import parser


class ElasticFieldMapper(object):

    @classmethod
    def date(cls, value):
        return parser.parse(value)


class Bunch(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class ElasticResultsShards(Bunch):

    def __init__(self, **shards):
        super(ElasticResultsShards, self).__init__(**shards)


class ElasticHitMeta(Bunch):

    def __init__(self, **meta):
        super(ElasticHitMeta, self).__init__(**meta)


class ElasticHitObject(object):

    def __init__(self, hit, mappers={}):
        self.hit = hit
        self.mappers = mappers

    @property
    def meta(self):
        return ElasticHitMeta({
            'index': self.hit['_index'],
            'score': self.hit['_score'],
            'type': self.hit['_type']
        })

    @property
    def id(self):
        return self.hit['_id']

    @property
    def source(self):
        return self.hit.get('_source', None)

    @property
    def fields(self):
        return self.hit.get('fields', {})

    def __getattr__(self, name):
        try:
            values = self.fields[name]
            mapper = self.mappers.get(name, None)
            if mapper is not None:
                values = [mapper(v) for v in values]
            return values if len(values) > 1 else values[0]
        except KeyError:
            raise AttributeError(
                "'ElasticHitObject' object has no attribute '{}'".format(
                    name
                )
            )


class ElasticResultsObject(object):

    def __init__(self, results, mappers={}):
        self.results = results
        self.mappers = mappers

    @property
    def total_hits(self):
        return self.results['hits']['total']

    @property
    def max_score(self):
        return self.results['hits']['max_score']

    @property
    def timed_out(self):
        return self.results['timed_out']

    @property
    def took(self):
        return self.results['took']

    @property
    def hits(self):
        for hit in self.results['hits']['hits']:
            yield ElasticHitObject(hit, mappers=self.mappers)

    @property
    def shards(self):
        return ElasticResultsShards(**self.results['_shards'])


class ElasticDocObject(object):

    def __init__(self, doc, mappers={}):
        self.doc = doc
        self.mappers = mappers

    @property
    def id(self):
        return self.doc['_id']

    @property
    def found(self):
        return self.doc['found']

    @property
    def version(self):
        return self.doc['_version']

    @property
    def fields(self):
        return self.doc.get('fields', {})

    def __getattr__(self, name):
        try:
            values = self.fields[name]
            mapper = self.mappers.get(name, None)
            if mapper is not None:
                values = [mapper(v) for v in values]
            return values if len(values) > 1 else values[0]
        except KeyError:
            raise AttributeError(
                "'ElasticDocObject' object has no attribute '{}'".format(
                    name
                )
            )


class Search(object):

    def __init__(self, index, body={}, mappers={}):
        self.index = index
        self.body = body
        self.mappers = mappers
        self.urls = settings.ELASTICSEARCH_URLS
        self.rawes_ckwargs = getattr(settings, 'ELASTICSEARCH_KWARGS', {})

    @property
    def es(self):
        if not hasattr(self, '_es'):
            self._es = rawes.Elastic(self.urls, **self.rawes_ckwargs)
        return self._es

    def search(self):
        results = self.es.get(
            '/{}/_search'.format(self.index), data=self.body
        )
        return ElasticResultsObject(results, self.mappers)

    def get(self, doc_id, doc_type, fields=[]):
        try:
            result = self.es.get(
                '/{}/{}/{}?fields={}'.format(
                    self.index,
                    doc_type,
                    doc_id,
                    ','.join(fields)
                )
            )
        except ElasticException as e:
            if e.result.get('error', False):
                raise ElasticException(
                    message="ElasticSearch Error: {0}".format(
                        json.dumps(e.result)
                    ),
                    result=e.result, status_code=e.status_code
                )
            else:
                result = e.result
        return ElasticDocObject(result, mappers=self.mappers)
