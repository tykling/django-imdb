# django-imdb
Django app to work with IMDb Non-Commercial Datasets

## Installation
1. `pip install django-imdb`

2. Add `django-imdb` to `INSTALLED_APPS` in your project

3. Run `manage.py migrate`

4. Run `manage.py import_imdb_tsv`

Step 4 will download IMDb non-commercial datasets and import them into Django models. This will take 12-24 hours and result in more than 20gb sqlite database. Be warned.

Step 4 should be run regularly, like weekly or monthly, or whatever you like. Data is updated daily by IMDb. Read more https://developer.imdb.com/non-commercial-datasets/

## Searching
Currently the search stuff uses pocketsearch, which uses fts5, which is sqlite specific :( I hope to replace it with whoosh at some point, if I can figure out which fork to use.
