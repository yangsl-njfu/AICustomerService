# AI Module

`ai_module` is the standalone boundary for AI capabilities.

## What It Wraps

- Runtime/workflow access
- Business-pack discovery
- Plugin metadata queries
- A minimal standalone HTTP app
- Core implementation under `backend/ai_module/core` and `backend/ai_module/plugins`

## Public Entry Points

- `ai_module.engine.ai_engine`
- `ai_module.runtime` (compatibility exports)
- `ai_module.workflow` (compatibility exports)
- `ai_module.app` (standalone FastAPI app)

## Run As Standalone Service

```bash
uvicorn ai_module.app:app --host 0.0.0.0 --port 8090 --reload
```
