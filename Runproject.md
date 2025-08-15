### Chạy dev & prod
Dev (auto reload):
```
uv run fastapi dev app/main.py
```

Prod (đơn giản):
```
uv run fastapi run app/main.py --port 8000
#
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```


### Run migration

```
uv run --env-file .env alembic revision -m "migration message"
```
