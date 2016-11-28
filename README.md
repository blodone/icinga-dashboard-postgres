# icinga-dashboard-postgres
Icinga Dashboard for Flask using PostgreSQL

Minimal lightweight icinga Dashboard

#prepare system
```
apt-get install libpq-dev libzbar-dev python-dev python3-dev libssl-dev
```

*create and edit flask_config/local.py*

```
DEBUG = False

DATABASE_USER = ''
DATABASE_PASSWORD = ''
DATABASE_HOST = 'localhost'
DATABASE_PORT = 5432
DATABASE_NAME = 'icingaidoutils'
```
