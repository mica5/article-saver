from contextlib import contextmanager

import psycopg2
import falcon

from config_article_saver import db_connstr

class ArticleResource:

    @staticmethod
    @contextmanager
    def db_cursor():
        conn = psycopg2.connect(db_connstr)
        cursor = conn.cursor()
        yield cursor
        conn.close()

    @classmethod
    def get_article(cls, aid):
        with cls.db_cursor() as cursor:
            cursor.execute('select * from articles where aid=%(aid)s', {'aid': aid})
            headers = [c.name for c in cursor.description]
            article = {h: a for h, a in zip(headers, cursor.fetchone())}
        return article

    def on_get(self, req, resp):
        """Handles GET requests
        """
        aid = req.params.get('id', None)
        if aid is None:
            return

        article = self.get_article(aid)

        resp.content_type = falcon.MEDIA_HTML
        resp.body = article['content']

api = falcon.API()
api.add_route('/article', ArticleResource())
