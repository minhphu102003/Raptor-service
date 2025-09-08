### Chạy dev & prod

### Development

```bash
uv run fastapi dev app/main.py

```

### Run mcp
```
python run_mcp_server.py --mode http --host 127.0.0.1 --port 3333

python run_mcp_server.py --mode stdio

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

```
uv run --env-file .env alembic upgrade head
```

### Run precommit

```
uv run pre-commit run --all-files
```

### Run commit with package

```
uv run cz commit
```
