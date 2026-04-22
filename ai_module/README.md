# AI Module

## What is implemented
- Domain models for article/content/blocks.
- Suggestions model with target ids (`article/topic/page/block`).
- Text suggestions pipeline via GigaChat.
- Layout suggestions pipeline via deterministic rules.
- FastAPI endpoints for suggestions.
- File logging per subsystem with rotation.

## Install

```powershell
pip install -r ai_module/requirements.txt
```

## Run API

```powershell
uvicorn ai_module.api.main:app --reload
```

or:

```powershell
python -m ai_module.scripts.run_server --reload
```

## Endpoints
- `GET /api/v1/health`
- `POST /api/v1/suggestions/layout`
- `POST /api/v1/suggestions/text`
- `POST /api/v1/suggestions/all`

## API docs
- Swagger UI: `/swagger`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## Logs
- `ai_module/logs/app.log`
- `ai_module/logs/api.log`
- `ai_module/logs/llm.log`
- `ai_module/logs/httpx.log`

## Live GigaChat check

```powershell
python -m ai_module.scripts.check_gigachat
```
