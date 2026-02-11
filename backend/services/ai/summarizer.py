"""
对话摘要压缩器 - 将较早的对话历史压缩为摘要文本，保留关键信息

Requirements:
- 3.1: 对话历史轮数超过阈值时自动触发摘要
- 3.2: 将阈值之前的历史消息压缩为结构化摘要，保留关键信息
- 3.3: 用摘要替换被压缩的历史消息，保留阈值之后的最近对话原文
- 3.5: 摘要后总 token 数不超过配置上限
- 3.6: 摘要失败时回退到截断策略
"""
import logging
from langchain_core.prompts import ChatPromptTemplate
from config import settings

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """请将以下对话历史压缩为一段简洁的摘要。
保留以下关键信息：
- 用户的主要意图和需求
- 提及的具体商品名称、订单号
- 已解决的问题和结论
- 用户的偏好信息

已有摘要：
{existing_summary}

请输出更新后的摘要，不超过 500 字。"""),
    ("human", "对话历史：\n{history_text}")
])


def estimate_tokens(text: str) -> int:
    """Estimate token count for text.

    Uses a simple heuristic: roughly 1 token per 2 characters for Chinese text.
    This is a conservative estimate that works reasonably well for mixed
    Chinese/English content.
    """
    if not text:
        return 0
    return max(1, len(text) // 2)


def estimate_history_tokens(history: list) -> int:
    """Estimate total token count for a list of history messages.

    Each history entry is expected to be a dict with 'user' and 'assistant' keys.
    """
    total = 0
    for msg in history:
        user_text = msg.get("user", "")
        assistant_text = msg.get("assistant", "")
        total += estimate_tokens(user_text) + estimate_tokens(assistant_text)
    return total


def _format_history_for_summary(history: list) -> str:
    """Format history messages into a readable text block for the LLM prompt."""
    lines = []
    for msg in history:
        user_text = msg.get("user", "")
        assistant_text = msg.get("assistant", "")
        if user_text:
            lines.append(f"用户: {user_text}")
        if assistant_text:
            lines.append(f"助手: {assistant_text}")
    return "\n".join(lines)


class ConversationSummarizer:
    """对话摘要压缩器

    Compresses older conversation history into a summary text while keeping
    recent messages intact. Uses an LLM to generate intelligent summaries
    and falls back to simple truncation on failure.
    """

    def __init__(self, llm):
        self.llm = llm
        self.trigger_threshold = settings.SUMMARY_TRIGGER_THRESHOLD  # default 10
        self.max_tokens = settings.CONTEXT_MAX_TOKENS  # default 3000

    def should_summarize(self, history: list) -> bool:
        """Check if summarization should be triggered.

        Returns True when the number of history messages exceeds the
        configured trigger threshold.

        Requirement 3.1: Trigger when len(history) > SUMMARY_TRIGGER_THRESHOLD
        """
        return len(history) > self.trigger_threshold

    async def summarize(self, history: list, existing_summary: str = "") -> dict:
        """Generate a summary of older conversation history.

        Splits history at the trigger threshold:
        - Messages before the threshold are compressed into a summary
        - Messages after the threshold are kept as remaining_history

        After summarization, checks if total tokens (summary + remaining_history)
        exceed CONTEXT_MAX_TOKENS. If so, truncates remaining_history further.

        Args:
            history: Full conversation history list
            existing_summary: Previously generated summary to incorporate

        Returns:
            dict with keys:
                - "summary": The generated summary text
                - "remaining_history": List of recent messages to keep

        Requirement 3.2: Compress messages before threshold into summary
        Requirement 3.3: Keep messages after threshold as remaining_history
        Requirement 3.5: Ensure total tokens don't exceed CONTEXT_MAX_TOKENS
        """
        # Split history: messages to summarize vs messages to keep
        messages_to_summarize = history[:-self.trigger_threshold] if len(history) > self.trigger_threshold else []
        remaining_history = history[-self.trigger_threshold:]

        if not messages_to_summarize:
            # Nothing to summarize - return as-is
            return {
                "summary": existing_summary,
                "remaining_history": remaining_history,
            }

        # Format the messages to summarize into text for the LLM
        history_text = _format_history_for_summary(messages_to_summarize)

        # Call LLM to generate summary
        messages = SUMMARY_PROMPT.format_messages(
            existing_summary=existing_summary or "（无）",
            history_text=history_text,
        )
        response = await self.llm.ainvoke(messages)
        summary = response.content.strip()

        logger.info(
            f"📝 摘要生成完成: 压缩了 {len(messages_to_summarize)} 条消息, "
            f"保留 {len(remaining_history)} 条最近消息"
        )

        # Check token limits and truncate remaining_history if needed
        remaining_history = self._enforce_token_limit(summary, remaining_history)

        return {
            "summary": summary,
            "remaining_history": remaining_history,
        }

    def _enforce_token_limit(self, summary: str, remaining_history: list) -> list:
        """Ensure total tokens (summary + remaining_history) don't exceed max_tokens.

        If the total exceeds the limit, progressively removes the oldest messages
        from remaining_history until the constraint is satisfied.

        Requirement 3.5: Total tokens must not exceed CONTEXT_MAX_TOKENS
        """
        summary_tokens = estimate_tokens(summary)

        while remaining_history:
            history_tokens = estimate_history_tokens(remaining_history)
            total_tokens = summary_tokens + history_tokens

            if total_tokens <= self.max_tokens:
                break

            # Remove the oldest message from remaining_history
            remaining_history = remaining_history[1:]
            logger.debug(
                f"Token 超限，截断最早消息。当前: {len(remaining_history)} 条, "
                f"估算 token: {summary_tokens + estimate_history_tokens(remaining_history)}"
            )

        return remaining_history

    def fallback_truncate(self, history: list) -> dict:
        """Fallback truncation strategy when summarization fails.

        Simply keeps the most recent messages (up to trigger_threshold count)
        and discards older messages without generating a summary.

        Requirement 3.6: Fallback to truncation on summarization failure
        """
        return {
            "summary": "",
            "remaining_history": history[-self.trigger_threshold:],
        }
