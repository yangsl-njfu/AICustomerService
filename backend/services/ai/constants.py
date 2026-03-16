"""Shared AI workflow constants."""
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
