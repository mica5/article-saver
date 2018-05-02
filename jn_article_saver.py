import datetime
from dateutil import parser
import subprocess

from ipywidgets import widgets
from IPython.display import display, HTML

from config_article_saver import db_connstr, falcon_port

def parse_datetime_str(s):
    return parser.parse(
        subprocess.check_output(
            "date -d '{}'".format(s),
            shell=True
        ).decode().strip(),
        ignoretz=True
    )

def create_and_display_article_saver():
    wide_layout = widgets.Layout(width='100%')

    # create buttons
    print("Save article:")
    url_text_input = widgets.Text(description="Url", layout=wide_layout)
    display(url_text_input)

    notes_text_input = widgets.Text(description='Notes', layout=wide_layout)
    display(notes_text_input)

    datetime_text_input = widgets.Text(description="Datetime")
    display(datetime_text_input)

    print("HTML (if we couldn't grab the page)")
    html_text_input = widgets.Textarea(description="Html")
    display(html_text_input)

    def get_title(content):
        from bs4 import BeautifulSoup
        bs = BeautifulSoup(content, 'html.parser')
        return bs.title.string

    def get_connection():
        import psycopg2
        conn = psycopg2.connect(db_connstr)
        return conn

    def load_page_content_html(url):
        # load the content of the page
        import requests
        response = requests.get(url)
        content = response.content.decode()
        return content

    def save_article(url, html=None, dt=None, title=None, notes=None):
        conn = get_connection()
        cursor = conn.cursor()

        content = html or load_page_content_html(url)

        if title is None:
            title = get_title(content)

        if dt is None:
            dt = datetime.datetime.now()

        insert_sql = """INSERT INTO
            articles (
                datetime, title, notes, url, content
            )
            values (
                %(datetime)s,
                %(title)s,
                %(notes)s,
                %(url)s,
                %(content)s
            )
        """
        cursor.execute(
            insert_sql,
            {
                'datetime': dt,
                'title': title,
                'notes': notes,
                'url': url,
                'content': content,
            }
        )
        conn.commit()
        conn.close()

        return

    def handle_input():
        # grab the inputs from the user
        timestr = datetime_text_input.value.strip()
        # parse time or set empty time to None
        timefrom = parse_datetime_str(timestr) if timestr else None

        notestr = notes_text_input.value.strip()
        url = url_text_input.value.strip()
        html = html_text_input.value.strip()

        save_article(url, html=html, dt=timefrom, title=None, notes=notestr)

        # on success, clear out all the fields
        datetime_text_input.value = ''
        notes_text_input.value = ''
        url_text_input.value = ''
        html_text_input.value = ''

    # set up handlers
    log_event_handler = lambda x: handle_input()
    datetime_text_input.on_submit(log_event_handler)
    notes_text_input.on_submit(log_event_handler)
    url_text_input.on_submit(log_event_handler)


def construct_url(row):
    url = row.url
    if '#' in url:
        anchor = '#' + url[::-1].split('#', 1)[0][::-1]
    else:
        anchor = ''
    return '<a href="http://localhost:{falcon_port}/article?id={aid}{anchor}" target="_blank">{title}</a>'.format(
        aid=row.aid,
        title=row.title,
        falcon_port=falcon_port,
        anchor=anchor,
    )


def display_events_search_from_db():
    import psycopg2
    import pandas as pd
    from ipywidgets import interact_manual
    import datetime

    pd.options.display.max_colwidth = 0

    # make db connection
    conn = psycopg2.connect(db_connstr)

    columns = [
        'aid',
        'datetime',
        'title',
        'notes',
        'url',
        'content',
    ]
    # make the handler
    def run_search(search_term):
        search_terms = search_term.strip().split()

        # if the search term is empty, return empty
        if not search_terms:
            return pd.DataFrame(columns=columns).set_index('aid')

        # write the query
        ands = list()
        params = dict()
        for i, search_term in enumerate(search_terms):
            # so user can search using common regex \b
            # instead of postgres's \y
            search_term = search_term.replace('\\b', '\\y')

            key = 'and{}'.format(i)
            params[key] = search_term

            # this checks: if the user's search term caused
            # the constructed string to change (because it matched),
            # then it matches for this search.
            # TODO this can probably be improved...
            ands.append("""regexp_replace(
                aid::text || ' ' || title::text || ' ' || notes::text || ' ' || url::text || ' ' || content::text,
                %({key})s, '', 'i')
                <> (aid::text || ' ' || title::text || ' ' || notes::text || ' ' || url::text || ' ' || content::text)""".format(key=key))

        query = """SELECT *\n    FROM articles\n    WHERE\n        {ands}""".format(
            ands=('\n        AND ').join(ands)
        )

        # query the db
        df = pd.read_sql(query, conn, params=params)
        df = df.sort_values('datetime', ascending=False)

        now = datetime.datetime.now()
        df['time_ago'] = df.datetime.apply(lambda x: now - x)

        df['title'] = df.apply(construct_url, axis=1)

        # return the result df
        return HTML(df.drop(['content'], axis=1).to_html(escape=False))

    # display the button
    return interact_manual(lambda search: run_search(search), search='')


