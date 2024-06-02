```
homebase_calendar_sync --help
usage: homebase_calendar_sync [-h] [--reset-auth] [--reset-db] [--reset-all]

Homebase/Google Calendar Sync CLI

options:
  -h, --help    show this help message and exit
  --reset-auth  reset the authentication cache
  --reset-db    reset the events database
  --reset-all   reset auth config and events database
```


`pip install homebase_calendar_sync`

`touch .env`

***.env***
```sh
CC_HOMEBASE_USERNAME = ""
CC_HOMEBASE_PASSWORD = ""
CC_HOMEBASE_EMPLOYEE_FIRSTNAME = ""
CC_HOMEBASE_EMPLOYEE_LASTNAME = ""
CC_HOMEBASE_START_DATE = "today"
CC_HOMEBASE_END_DATE = "today"
CC_HOMEBASE_DAYS_LOOKAHEAD = "14"
CC_HOMEBASE_LOOKAHEAD = "True"
```


```tree -l -I 'node_modules' -I 'venv' -I '__pycache__' -I '*.egg-info' -I "dist" -I 'build'
.
├── README.md
├── events.db
├── requirements.dev.txt
├── requirements.txt
├── setup.py
└── src
    └── homebase_calendar_sync
        ├── __init__.py
        ├── __main__.py
        ├── config.py
        ├── db
        │   ├── __init__.py
        │   ├── __main__.py
        │   └── models.py
        ├── google_client
        │   ├── __init__.py
        │   ├── __main__.py
        │   ├── auth.py
        │   ├── drive_types.py
        │   └── google_client.py
        └── homebase_calendar_sync.py
```