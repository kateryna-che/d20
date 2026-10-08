# d20

A campaign table for tabletop role-playing groups. The game master runs
campaigns and plans game sessions; the players keep their character sheets,
answer the invitations and share notes with the table.

A [one-page HTML overview](docs/index.html) presents the project using the
site's styles. To view it locally, run `python -m http.server 8765` from the
project root and open http://127.0.0.1:8765/docs/.

![The home page of d20 in the dark theme](docs/home.webp)

The site is live at https://d20-f3y6.onrender.com/. The server is free and
falls asleep without visitors, so the first page can take about a minute.

Log in as `demo` with the password `roll-for-initiative` to look around; the
other accounts are in [Demo data](#demo-data).

## Features

- Registration, login and player profiles.
- Guests look through the campaigns without an account; the names of the
  players and the places of the sessions open after login.
- Campaigns: run one as the game master or join it as a player with one of
  your characters.
- Game sessions: date, place, agenda and summary; every player confirms or
  declines the invitation.
- Character sheets: ability scores with modifiers, hit points, inventory and
  a d20 roller with advantage and disadvantage.
- Preparation notes (NPCs, locations, quests, items) that only the members of
  the campaign can read.
- Search that answers while you type and pagination in the lists, a filter
  of the campaign notes by kind, light and dark themes.

## Getting Started

These instructions get a copy of the project running on your machine for
development and testing. See [Deployment](#deployment) for the notes on a
live server.

### Prerequisites

- [Python](https://www.python.org/downloads/) 3.14: `.python-version` pins
  3.14.3.
- [Git](https://git-scm.com/downloads) to clone the repository.

Development needs nothing else: the database is an SQLite file. PostgreSQL
is needed only by the [production settings](#settings).

Check the version of Python before you start:

```shell
python --version
```

### Installing

Clone the repository and go to its folder:

```shell
git clone https://github.com/kateryna-che/d20.git
cd d20
```

Create a virtual environment and activate it:

```shell
python -m venv .venv
.venv\Scripts\activate        # source .venv/bin/activate on macOS and Linux
```

Install the requirements. `requirements-dev.txt` takes the packages of the
production server from `requirements.txt` and adds the tools that check the
code to them:

```shell
pip install -r requirements-dev.txt
```

Create the database. `manage.py` works with the development settings, which
need no environment variables: the database is the `db.sqlite3` file.

```shell
python manage.py migrate
```

The database starts empty. Load the [demo data](#demo-data) to see the site
with ready campaigns, sessions and characters:

```shell
python manage.py loaddata demo
```

For an empty site skip the fixture and create an account of your own:

```shell
python manage.py createsuperuser
```

Start the development server:

```shell
python manage.py runserver
```

The site opens at http://127.0.0.1:8000/. Log in as `demo` with the password
`roll-for-initiative`: the home page shows the next session, the numbers of
your campaigns, sessions and characters, and the sessions that wait for your
answer.

## Running the tests

```shell
python manage.py test
```

The tests run on a test database of their own, so the data in `db.sqlite3`
stays as it is.

### Application tests

The 33 tests are in `d20/tests/`, a module for every layer of the
application:

| Module           | What it checks                                           |
|------------------|----------------------------------------------------------|
| `test_models.py` | names and addresses of the objects, the campaigns of a   |
|                  | user, and the rules of a membership: the game master     |
|                  | cannot be a player of the campaign, the character must   |
|                  | belong to the player                                     |
| `test_forms.py`  | the registration and search forms; the membership form   |
|                  | offers a player only their own characters                |
| `test_views.py`  | the pages: login is required, registration, the numbers  |
|                  | of the home page, the list, search, creation, editing    |
|                  | and deletion of campaigns, joining and leaving one, the  |
|                  | list and creation of characters, the answer to a session |
|                  | invitation                                               |
| `test_admin.py`  | the bio of a player on the user page of the admin site   |

The tests of the views are the closest to end-to-end ones: they send requests
with the test client of Django and check the redirect, the template, the
context and the rows in the database. They guard the access rules. For
example, a game master who edits the campaign of another game master gets the
404 page, and the campaign stays the same.

Run one module or one test by its path:

```shell
python manage.py test d20.tests.test_views
python manage.py test d20.tests.test_views.PrivateCampaignTests.test_join_and_leave_campaign
```

### Coding style tests

Four tools check the code, each its own part of it. `pyproject.toml` holds
their settings and keeps the migrations out of the first three.

[Black](https://black.readthedocs.io/) formats the Python code, so the whole
project has one style. Check the style without changing the files:

```shell
black --check .
```

`black .` reformats the files.

[Ruff](https://docs.astral.sh/ruff/) finds what a formatter does not see:
unused imports and names, imports out of order, code that tends to hide a
bug:

```shell
ruff check .
```

`ruff check --fix .` repairs what it can by itself.

[mypy](https://mypy-lang.org/) with
[django-stubs](https://github.com/typeddjango/django-stubs) checks the type
annotations in strict mode:

```shell
mypy .
```

[djLint](https://djlint.com/) checks the templates:

```shell
djlint templates --lint
```

## Demo data

The `demo` fixture, `d20/fixtures/demo.json`, fills an empty database with a
busy table: 11 players, 9 campaigns, 46 game sessions, 27 character sheets
and 32 notes.

```shell
python manage.py migrate
python manage.py loaddata demo
```

Load it instead of `createsuperuser`: the fixture brings its own accounts and
overwrites the rows that have the same primary keys. Every account has the
password `roll-for-initiative`.

| Login        | What it shows                                                |
|--------------|--------------------------------------------------------------|
| `demo`       | the main account: runs three campaigns, plays in three more, |
|              | has ten characters and sessions that wait for an answer      |
| `lena`       | the game master of a campaign where `demo` is a player       |
| `tess`       | a player of "Skyship Smugglers", which `demo` sees from the  |
|              | outside: no notes, only the button to join                   |
| `dicegoblin` | a player without a name, a bio or a character                |
| `robin`      | a new account: every list is empty                           |
| `admin`      | the superuser of the admin site at `/admin/`                 |

The other players are `marco`, `oleh`, `priya`, `sam` and `yuki`.

The dates of the fixture are fixed: the scheduled sessions run from October
2026 to April 2027.

The production database takes the same fixture. The command needs the
environment variables of the [production settings](#settings):

```shell
python manage.py loaddata demo --settings=d20_dev.settings.prod
```

On a public server change the password of `admin` right after that:

```shell
python manage.py changepassword admin --settings=d20_dev.settings.prod
```

The fixture is the output of `dumpdata` and is written again the same way
when the models change:

```shell
python manage.py dumpdata d20 --indent 2 --output d20/fixtures/demo.json
```

On Windows `dumpdata --output` writes the file in the encoding of the system
locale, so the texts of the fixture are plain ASCII. Set `PYTHONUTF8=1` before
other characters go into it.

## Deployment

A live server works with the production settings and a PostgreSQL database.

### Settings

The settings are a package with a module for every environment:

| Module                  | Used by                 | Database   |
|-------------------------|-------------------------|------------|
| `d20_dev.settings.dev`  | `manage.py` by default  | SQLite     |
| `d20_dev.settings.prod` | `wsgi.py` and `asgi.py` | PostgreSQL |

Another module is chosen with the `DJANGO_SETTINGS_MODULE` environment
variable or with the `--settings` option of `manage.py`:

```shell
python manage.py migrate --settings=d20_dev.settings.prod
```

The production settings read the variables below from the environment. For
local use copy `.env.sample` to `.env` and fill it in; the file is loaded
when the settings are imported.

| Variable            | Value                                       |
|---------------------|---------------------------------------------|
| `POSTGRES_DB`       | name of the database                        |
| `POSTGRES_DB_PORT`  | port of the database server, usually `5432` |
| `POSTGRES_USER`     | database user                               |
| `POSTGRES_PASSWORD` | password of the user                        |
| `POSTGRES_HOST`     | host of the database server                 |
| `DJANGO_SECRET_KEY` | long random string                          |

### Render

The project is ready for a [Render](https://render.com/) web service with a
PostgreSQL database, for example on [Neon](https://neon.tech/):

- build command: `./build.sh`, which installs the requirements, collects the
  static files and applies the migrations;
- start command:
  `gunicorn d20_dev.wsgi:application --workers 1 --threads 10`;
- environment variables: the ones from the table above.

Render sets `RENDER_EXTERNAL_HOSTNAME` itself, and the production settings
add this domain to `ALLOWED_HOSTS`.

The build does not load the [demo data](#demo-data): the fixture is loaded
once by hand.

## Built With

- [Python](https://www.python.org/) 3.14 - the language
- [Django](https://www.djangoproject.com/) 6.1 - the web framework
- [SQLite](https://www.sqlite.org/) - the database for development
- [PostgreSQL](https://www.postgresql.org/) with
  [psycopg2](https://www.psycopg.org/) - the database in production
- [WhiteNoise](https://whitenoise.readthedocs.io/) - serves the static files
- [Gunicorn](https://gunicorn.org/) - the WSGI server
- [python-dotenv](https://github.com/theskumar/python-dotenv) - loads the
  `.env` file
- [Black](https://black.readthedocs.io/) - the code formatter
- [Ruff](https://docs.astral.sh/ruff/) - the linter
- [mypy](https://mypy-lang.org/) with
  [django-stubs](https://github.com/typeddjango/django-stubs) - the type
  checker
- [djLint](https://djlint.com/) - the linter of the templates
- [htmx](https://htmx.org/) 2.0 - the search that answers while you type;
  the pages load it from a CDN

The pages are Django templates with plain CSS and JavaScript: no front-end
framework and no build step.

## Authors

- **Kateryna Cherepanova** - [kateryna-che](https://github.com/kateryna-che)

## Acknowledgments

- The structure of this README follows the
  [README template](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2)
  of Billie Thompson.
