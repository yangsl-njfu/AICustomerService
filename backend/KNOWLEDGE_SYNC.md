# 知识库同步说明

## 概述

知识库同步功能将商品信息和平台规则同步到 Chroma 向量数据库，用于 AI 客服的智能推荐和咨询。

## 功能特性

### 1. 商品信息同步
- 自动将已发布的商品信息添加到向量数据库
- 包含商品标题、描述、技术栈、价格、评分等信息
- 支持商品更新时自动同步
- 支持商品删除时自动清理

### 2. 平台规则同步
- 购买流程说明
- 支付方式介绍
- 退款政策
- 卖家指南
- 常见问题解答（FAQ）

## 使用方法

### 手动同步

运行同步脚本：

```bash
cd backend
python sync_knowledge.py
```

这将：
1. 同步所有平台规则到知识库
2. 同步所有已发布的商品到商品目录

### 自动同步

商品信息会在以下情况自动同步：

1. **商品发布时**：当商品状态更新为 `published` 时自动同步
2. **商品更新时**：已发布商品更新后自动重新同步
3. **商品删除时**：自动从知识库删除

## 文件说明

### `services/product_knowledge_sync.py`
商品知识库同步服务，提供以下方法：

- `sync_product_to_knowledge(db, product_id)` - 同步单个商品
- `sync_all_products(db)` - 同步所有商品
- `remove_product_from_knowledge(product_id)` - 删除商品
- `update_product_in_knowledge(db, product_id)` - 更新商品

### `sync_knowledge.py`
知识库同步脚本，用于批量同步：

- 同步平台规则
- 同步所有商品
- 显示统计信息

## AI 客服集成

同步后的数据会被 AI 客服使用：

### 商品推荐节点
- 根据用户需求（专业、技术栈、预算）检索匹配商品
- 从 `product_catalog` 集合检索
- 生成个性化推荐理由

### 商品咨询节点
- 回答用户关于具体商品的问题
- 解释技术栈、难度、价格等信息
- 从 `product_catalog` 集合检索

### 购买指导节点
- 提供购买流程指导
- 解释支付方式和退款政策
- 从 `knowledge_base` 集合检索平台规则

### 订单查询节点
- 查询用户订单状态
- 提供订单处理建议
- 结合数据库查询和知识库检索

## 数据结构

### 商品文档格式
```python
{
    "id": "product_{product_id}",
    "content": "商品名称、描述、技术栈等文本内容",
    "metadata": {
        "product_id": "商品ID",
        "title": "商品标题",
        "price": 价格（浮点数）,
        "difficulty": "难度",
        "rating": 评分,
        "sales_count": 销量,
        "tech_stack": "技术栈JSON",
        "category_id": "分类ID",
        "seller_id": "卖家ID",
        "source": "product_catalog"
    }
}
```

### 平台规则文档格式
```python
{
    "id": "rule_{category}",
    "content": "规则详细内容",
    "metadata": {
        "type": "platform_rule",
        "category": "规则类别",
        "source": "platform_docs"
    }
}
```

## 注意事项

1. **首次使用**：需要先运行 `sync_knowledge.py` 进行初始化同步
2. **Chroma 依赖**：确保已安装 `chromadb` 并正确配置
3. **性能考虑**：大量商品同步可能需要一些时间
4. **定期同步**：建议定期运行同步脚本以确保数据最新

## 故障排查

### 知识库不可用
- 检查 `chromadb` 是否已安装
- 检查 `CHROMA_PERSIST_DIRECTORY` 配置
- 检查文件系统权限

### 同步失败
- 检查数据库连接
- 检查商品数据完整性
- 查看错误日志

### AI 检索无结果
- 确认知识库已同步
- 检查集合名称是否正确
- 验证 OpenAI API 配置
