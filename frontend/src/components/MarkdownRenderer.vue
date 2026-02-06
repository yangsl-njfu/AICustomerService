<template>
  <div class="markdown-body" v-html="renderedContent"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'

const props = defineProps<{
  content: string
}>()

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (__) {}
    }
    return hljs.highlightAuto(str).value
  }
})

const renderedContent = computed(() => {
  if (!props.content) return ''
  return md.render(props.content)
})
</script>

<style scoped>
.markdown-body {
  line-height: 1.5;
  font-size: 14px;
  color: var(--text);
}

.markdown-body :deep(h1) {
  font-size: 1.2em;
  font-weight: 600;
  margin: 0.15em 0 0.05em 0;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.08em;
}

.markdown-body :deep(h2) {
  font-size: 1.1em;
  font-weight: 600;
  margin: 0.12em 0 0.05em 0;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.08em;
}

.markdown-body :deep(h3) {
  font-size: 1em;
  font-weight: 600;
  margin: 0.08em 0 0.03em 0;
}

.markdown-body :deep(h4) {
  font-size: 0.95em;
  font-weight: 600;
  margin: 0.08em 0 0.03em 0;
}

/* 标题后的元素间距 */
.markdown-body :deep(h1 + *),
.markdown-body :deep(h2 + *),
.markdown-body :deep(h3 + *),
.markdown-body :deep(h4 + *) {
  margin-top: 0.02em;
}

.markdown-body :deep(p) {
  margin: 0.02em 0;
  line-height: 1.4;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0;
  padding-left: 1.2em;
}

.markdown-body :deep(li) {
  margin: 0;
  line-height: 1.5;
}

.markdown-body :deep(li + li) {
  margin-top: 0;
}

.markdown-body :deep(li > p) {
  margin: 0;
}

/* 列表项内的所有元素 */
.markdown-body :deep(li > *) {
  margin: 0;
}

/* 列表项内的标题 */
.markdown-body :deep(li > h1),
.markdown-body :deep(li > h2),
.markdown-body :deep(li > h3),
.markdown-body :deep(li > h4) {
  margin: 0;
  font-size: 1em;
  font-weight: 600;
  border: none;
  padding: 0;
}

/* 嵌套列表 */
.markdown-body :deep(li > ul),
.markdown-body :deep(li > ol) {
  margin: 0.05em 0 0 0;
}

/* 段落后的列表 */
.markdown-body :deep(p + ul),
.markdown-body :deep(p + ol) {
  margin-top: 0.02em;
}

/* 列表后的段落 */
.markdown-body :deep(ul + p),
.markdown-body :deep(ol + p) {
  margin-top: 0.02em;
}

.markdown-body :deep(strong) {
  font-weight: 600;
  color: var(--text);
}

.markdown-body :deep(code) {
  background-color: rgba(148, 163, 184, 0.18);
  padding: 0.1em 0.3em;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.82em;
}

.markdown-body :deep(pre) {
  background-color: var(--surface-3);
  padding: 0.6em;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.2em 0;
  border: 1px solid var(--border);
}

.markdown-body :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-body :deep(blockquote) {
  border-left: 2px solid var(--border);
  padding-left: 0.6em;
  margin: 0.2em 0;
  color: var(--muted);
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--border);
  margin: 0.3em 0;
}

.markdown-body :deep(a) {
  color: var(--accent);
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.15em 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--border);
  padding: 0.2em 0.4em;
  text-align: left;
}

.markdown-body :deep(th) {
  background-color: var(--surface-2);
  font-weight: 600;
}
</style>
