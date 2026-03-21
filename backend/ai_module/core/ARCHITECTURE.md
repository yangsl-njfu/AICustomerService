# AI Structure

## Main Runtime Chain

The backend AI pipeline is centered on `AIWorkflow` in [orchestration/orchestrator.py](/e:/Project/AICustomerService/backend/ai_module/core/orchestration/orchestrator.py).

Current non-stream flow:

1. `load_context`
2. `message_entry`
3. `response_planner`
4. `conversation_control` or `policy`
5. `dialogue_state`
6. `function_calling`
7. routed skill node
8. `save_context`

The `AIWorkflow` implementation is now imperative. The old `langgraph` graph
assembly was removed from the execution path so that stream and non-stream
requests share the same preparation pipeline.

## Layer Ownership

### Core

- `orchestration/orchestrator.py`: thin assembly facade
- `orchestration/orchestrator_parts/*.py`: initialization/state/prepare/execute/entrypoint responsibilities
- `runtime.py`: business pack, prompts, model/tool provisioning
- `state.py`: shared conversation contract
- `orchestration/skill_router.py`: skill routing after execution planning
- `orchestration/handler_registry.py`: node registration
- `workflows/`: pluggable business workflow packages (service-level orchestration)

Core package exports are lazy:

- `ai_module.core.__init__` no longer imports `runtime` and `workflow` eagerly
- `ai_module.core.nodes.__init__` no longer imports every node eagerly

This keeps targeted imports like `ai_module.core.nodes.understanding.message_entry_node` from
pulling in optional dependencies such as file or database stacks.

### Understanding

- `nodes/understanding/message_entry_node.py`: entry orchestration
- `nodes/understanding/intent_node.py`: global task intent recognition
- `nodes/understanding/turn_understanding_node.py`: active-task turn understanding

### Policy

- `nodes/policy/response_planner_node.py`: map inflow to response mode
- `nodes/policy/policy_node.py`: converge understanding into executable intent
- `nodes/policy/dialogue_state_node.py`: persist/advance active task state
- `nodes/policy/conversation_control_node.py`: non-skill conversational control replies

### Skills

- `nodes/skills/qa_node.py`
- `nodes/skills/topic_advisor_node.py`
- `nodes/skills/order_query_node.py`
- `nodes/skills/purchase_guide_node.py`
- `nodes/skills/purchase_flow_node.py`
- `nodes/skills/aftersales_flow_node.py`
- `nodes/skills/ticket_node.py`
- `nodes/skills/document_node.py`
- `nodes/skills/clarify_node.py`
- `nodes/skills/product_inquiry_node.py`

### Workflow Packages

- `workflows/topic_advisor/workflow.py`
- `workflows/purchase_flow/workflow.py`
- `workflows/aftersales_flow/workflow.py`
- `workflows/*/state_machine.py` (explicit transition map)
- `workflows/*/steps.py` (step implementations)

`AIWorkflow` now executes these business flows through `WorkflowRegistry`.
The underlying node implementations remain unchanged and are reused inside each
workflow package.

For `aftersales_flow`, business logic is decomposed into dedicated step nodes in:

- `nodes/aftersales/constants.py`
- `nodes/aftersales/*_node.py` (one step per file)

The workflow only handles orchestration and routing across these nodes.

### Memory

- `nodes/memory/context_node.py`
- `nodes/memory/save_context_node.py`
- `memory_builder.py`
- `summarizer.py`

## Notes

- Two legacy nodes were removed because they were not referenced by the workflow, handler registry, router, tests, or node exports:
  - `nodes/personalized_recommend_node.py`
  - `nodes/product_recommendation_node.py`
- Skill nodes are now registered lazily through `HandlerRegistry`. Importing
  `ai_module.core.orchestration` no longer instantiates order/document/aftersales
  handlers up front.
- `qa_node.py` and `document_node.py` now lazy-load `FileService` so optional
  file-storage dependencies are not required at module import time.
- The next cleanup target is test infrastructure: a few node tests still use
  manual `importlib` bootstrapping instead of normal package imports.

