# article-saver
create a database, a saver in jupyter notebook, and a falcon article viewer endpoint

# Setup

## Create the postgresql database

    create table articles (
        aid bigserial primary key
        , datetime timestamp without time zone
        , title text
        , notes text
        , url text
        ,content text
    );

## Create the config files

copy config_article_saver_sample.bash to config_article_saver.bash and update with the correct values
copy config_article_saver_sample.py to config_article_saver.py and update with the correct values

## Run the falcon server

    bash ./runserver.bash

## Run the Jupyter Notebook server

    jupyter notebook

Open the url that jupyter notebook prints into a web browser. Navigate to articles.ipynb.

Run the cells on the page to create the saver and the searcher.

Put a url in the "Url" bar. Optionally provide notes and a time (time can be anything that is accepted by the gnu date utility "-d" argument).

Search a keyword for the url you just saved, either something from the page or the title. On the result table, the "title" has been made into a url that points to your local falcon server that opens the local page.

Enjoy!
