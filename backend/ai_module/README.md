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

## Enterprise Module Layout

- `ai_module/application/`: orchestration and workflow facades
- `ai_module/domain/`: conversation contracts and domain node facades
- `ai_module/infrastructure/`: runtime and plugin facades
- `ai_module/core/`: existing implementation (kept for backward compatibility)

Domain node facades are grouped by responsibility:

- `domain/nodes/understanding`
- `domain/nodes/policy`
- `domain/nodes/memory`
- `domain/nodes/skills`

## Run As Standalone Service

```bash
uvicorn ai_module.app:app --host 0.0.0.0 --port 8090 --reload
```
