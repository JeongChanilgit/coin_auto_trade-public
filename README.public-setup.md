# Local configuration after privacy cleanup

Set `DJANGO_SECRET_KEY` in the process environment before running Django. Generate your own local key; never commit it. `.env.example` lists environment variable names only. This project does not automatically load `.env` files: export the variables in your shell or configure your process manager.

The committed SQLite database and generated trading/runtime data were removed for privacy. Create a new empty local database matching `coin_auto_trade/settings.py` (currently configured for MySQL), set its environment variables, then run `python manage.py migrate`. If an admin is needed, run `python manage.py createsuperuser` locally. Supply exchange credentials only when you intentionally enable trading, and keep them outside Git.

Install the dependencies appropriate to your local environment before these commands. No credentials or prior user records are supplied by this repository.
