# d20

A campaign table for tabletop role-playing groups. The game master runs
campaigns and plans game sessions; the players keep their character sheets,
answer the invitations and share notes with the table.

The site is live at https://d20-f3y6.onrender.com/. The server is free and
falls asleep without visitors, so the first page can take about a minute.

## Features

- Registration, login and player profiles.
- Campaigns: run one as the game master or join it as a player with one of
  your characters.
- Game sessions: date, place, agenda and summary; every player confirms or
  declines the invitation.
- Character sheets: ability scores with modifiers, hit points, inventory and
  a d20 roller with advantage and disadvantage.
- Preparation notes (NPCs, locations, quests, items) that only the members of
  the campaign can read.
- Search and pagination in the lists, light and dark themes.

## Technologies

- Python 3.14, Django 6.1
- SQLite for development, PostgreSQL in production
- WhiteNoise for static files, Gunicorn as the WSGI server

## Running locally

```shell
git clone https://github.com/kateryna-che/d20.git
cd d20
python -m venv .venv
.venv\Scripts\activate        # source .venv/bin/activate on macOS and Linux
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The site opens at http://127.0.0.1:8000/. `manage.py` works with the
development settings, which need no environment variables: the database is
the `db.sqlite3` file.

Run the tests with `python manage.py test`.

## Settings

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

## Deployment

The project is ready for a [Render](https://render.com/) web service with a
PostgreSQL database, for example on [Neon](https://neon.tech/):

- build command: `./build.sh`, which installs the requirements, collects the
  static files and applies the migrations;
- start command:
  `gunicorn d20_dev.wsgi:application --workers 1 --threads 10`;
- environment variables: the ones from the table above.

Render sets `RENDER_EXTERNAL_HOSTNAME` itself, and the production settings
add this domain to `ALLOWED_HOSTS`.
