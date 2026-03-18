"""AI 工作流共享常量。"""
from __future__ import annotations


INTENT_QA = "问答"
INTENT_TICKET = "工单"
INTENT_RECOMMEND = "推荐"
INTENT_PRODUCT_INQUIRY = "商品咨询"
INTENT_PURCHASE_GUIDE = "购买指导"
INTENT_ORDER_QUERY = "订单查询"
INTENT_DOCUMENT_ANALYSIS = "文档分析"
INTENT_AFTERSALES = "售后服务"

DEFAULT_INTENT_LABELS = [
    INTENT_QA,
    INTENT_TICKET,
    INTENT_RECOMMEND,
    INTENT_PRODUCT_INQUIRY,
    INTENT_PURCHASE_GUIDE,
    INTENT_ORDER_QUERY,
    INTENT_DOCUMENT_ANALYSIS,
    INTENT_AFTERSALES,
]

DEFAULT_INTENT_HANDLER_MAP = {
    INTENT_QA: "qa_flow",
    INTENT_TICKET: "ticket_flow",
    INTENT_PRODUCT_INQUIRY: "product_inquiry",
    INTENT_PURCHASE_GUIDE: "purchase_guide",
    INTENT_ORDER_QUERY: "order_query",
    INTENT_DOCUMENT_ANALYSIS: "document_analysis",
    INTENT_AFTERSALES: "aftersales_flow",
    INTENT_RECOMMEND: "topic_advisor",
}

DEFAULT_INTENT_RULES = {
    INTENT_RECOMMEND: [
        "推荐",
        "帮我选",
        "选题",
        "毕设题目",
        "适合我",
        "不知道选什么",
        "推荐一个适合",
        "什么难度",
        "我是大四",
        "我是计算机",
        "有什么推荐",
        "猜我喜欢",
        "根据我的浏览",
    ],
    INTENT_AFTERSALES: [
        "退款",
        "退货",
        "换货",
        "售后",
        "退换",
        "申请退款",
        "我要退",
        "不想要了",
    ],
    INTENT_ORDER_QUERY: [
        "订单",
        "物流",
        "发货",
        "到了吗",
        "快递",
        "什么时候发",
        "查订单",
        "订单号",
    ],
    INTENT_PURCHASE_GUIDE: [
        "怎么购买",
        "如何购买",
        "支付",
        "付款",
        "下单",
        "价格多少",
        "多少钱",
        "购买流程",
    ],
    INTENT_TICKET: [
        "投诉",
        "报错",
        "bug",
        "故障",
        "打不开",
        "不能用",
    ],
    INTENT_PRODUCT_INQUIRY: [
        "技术栈",
        "用什么",
        "哪个技术",
        "这个项目",
        "详情",
        "功能",
        "包含什么",
    ],
    INTENT_QA: [
        "你好",
        "hello",
        "hi",
        "你们是",
        "平台",
        "做什么",
        "介绍",
        "是什么",
    ],
}

DIALOGUE_ACT_NEW_REQUEST = "new_request"
DIALOGUE_ACT_CONFIRM = "confirm"
DIALOGUE_ACT_REJECT = "reject"
DIALOGUE_ACT_PROVIDE_SLOT = "provide_slot"
DIALOGUE_ACT_SELECT_ITEM = "select_item"
DIALOGUE_ACT_CORRECT = "correct"
DIALOGUE_ACT_SWITCH_TOPIC = "switch_topic"
DIALOGUE_ACT_RESUME_TASK = "resume_task"
DIALOGUE_ACT_UNCLEAR = "unclear"

CONTINUATION_DIALOGUE_ACTS = {
    DIALOGUE_ACT_CONFIRM,
    DIALOGUE_ACT_REJECT,
    DIALOGUE_ACT_PROVIDE_SLOT,
    DIALOGUE_ACT_SELECT_ITEM,
    DIALOGUE_ACT_CORRECT,
    DIALOGUE_ACT_RESUME_TASK,
}

ENTRY_CLASSIFIER_GLOBAL = "global_intent"
ENTRY_CLASSIFIER_INFLOW = "inflow"

INFLOW_VALID_CURRENT_INPUT = "valid_current_input"
INFLOW_RELATED_QUESTION = "related_question"
INFLOW_RELATED_BLOCKER = "related_blocker"
INFLOW_CORRECTION = "correction"
INFLOW_SWITCH_FLOW = "switch_flow"
INFLOW_CANCEL_FLOW = "cancel_flow"
INFLOW_HANDOFF = "handoff"
INFLOW_IRRELEVANT = "irrelevant"
INFLOW_UNKNOWN = "unknown"

INFLOW_TYPES = {
    INFLOW_VALID_CURRENT_INPUT,
    INFLOW_RELATED_QUESTION,
    INFLOW_RELATED_BLOCKER,
    INFLOW_CORRECTION,
    INFLOW_SWITCH_FLOW,
    INFLOW_CANCEL_FLOW,
    INFLOW_HANDOFF,
    INFLOW_IRRELEVANT,
    INFLOW_UNKNOWN,
}

RESPONSE_MODE_CONTINUE_CURRENT_TASK = "continue_current_task"
RESPONSE_MODE_HELP_CURRENT_TASK = "help_current_task"
RESPONSE_MODE_CLARIFY_BEFORE_RESUME = "clarify_before_resume"
RESPONSE_MODE_SWITCH_TASK = "switch_task"
RESPONSE_MODE_CANCEL_CURRENT_TASK = "cancel_current_task"
RESPONSE_MODE_HANDOFF = "handoff"

CONTROL_RESPONSE_MODES = {
    RESPONSE_MODE_HELP_CURRENT_TASK,
    RESPONSE_MODE_CLARIFY_BEFORE_RESUME,
    RESPONSE_MODE_CANCEL_CURRENT_TASK,
}

RESUME_MODE_RESUME_EXACT = "resume_exact"
RESUME_MODE_RESUME_FROM_SAFE_STEP = "resume_from_safe_step"
RESUME_MODE_RESTART_FLOW = "restart_flow"
