# AI Structure

## Main Runtime Chain

The backend AI pipeline is centered on `AIWorkflow` in [workflow/orchestrator.py](/e:/Project/AICustomerService/backend/ai_module/core/workflow/orchestrator.py).

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

- `workflow/orchestrator.py`: workflow assembly and entrypoints
- `runtime.py`: business pack, prompts, model/tool provisioning
- `state.py`: shared conversation contract
- `workflow/skill_router.py`: skill routing after execution planning
- `workflow/handler_registry.py`: node registration

Core package exports are lazy:

- `ai_module.core.__init__` no longer imports `runtime` and `workflow` eagerly
- `ai_module.core.nodes.__init__` no longer imports every node eagerly

This keeps targeted imports like `ai_module.core.nodes.message_entry_node` from
pulling in optional dependencies such as file or database stacks.

### Understanding

- `nodes/message_entry_node.py`: entry orchestration
- `nodes/intent_node.py`: global task intent recognition
- `nodes/turn_understanding_node.py`: active-task turn understanding

### Policy

- `nodes/response_planner_node.py`: map inflow to response mode
- `nodes/policy_node.py`: converge understanding into executable intent
- `nodes/dialogue_state_node.py`: persist/advance active task state
- `nodes/conversation_control_node.py`: non-skill conversational control replies

### Skills

- `nodes/qa_node.py`
- `nodes/topic_advisor_node.py`
- `nodes/order_query_node.py`
- `nodes/purchase_guide_node.py`
- `nodes/purchase_flow_node.py`
- `nodes/aftersales_flow_node.py`
- `nodes/ticket_node.py`
- `nodes/document_node.py`
- `nodes/clarify_node.py`
- `nodes/product_inquiry_node.py`

### Memory

- `nodes/context_node.py`
- `nodes/save_context_node.py`
- `memory_builder.py`
- `summarizer.py`

## Notes

- Two legacy nodes were removed because they were not referenced by the workflow, handler registry, router, tests, or node exports:
  - `nodes/personalized_recommend_node.py`
  - `nodes/product_recommendation_node.py`
- Skill nodes are now registered lazily through `HandlerRegistry`. Importing
  `ai_module.core.workflow` no longer instantiates order/document/aftersales
  handlers up front.
- `qa_node.py` and `document_node.py` now lazy-load `FileService` so optional
  file-storage dependencies are not required at module import time.
- The next cleanup target is test infrastructure: a few node tests still use
  manual `importlib` bootstrapping instead of normal package imports.

