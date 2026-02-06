"""
知识库同步脚本
用于将商品信息和平台规则同步到 Chroma 向量数据库
"""
import asyncio
from database.connection import get_db_context
from services.product_knowledge_sync import product_knowledge_sync
from services.knowledge_retriever import knowledge_retriever


async def sync_platform_rules():
    """同步平台规则到知识库"""
    if not knowledge_retriever.available:
        print("知识库不可用，跳过同步")
        return
    
    # 平台规则文档
    rules_documents = [
        {
            "id": "rule_purchase_flow",
            "content": """购买流程说明：
1. 浏览商品：在首页或商品列表页浏览毕业设计作品
2. 查看详情：点击商品卡片查看详细信息，包括技术栈、难度、评价等
3. 加入购物车：点击"加入购物车"按钮，或直接"立即购买"
4. 确认订单：在购物车页面确认商品和价格，点击"去结算"
5. 填写信息：确认订单信息（系统会自动填充用户信息）
6. 选择支付：选择支付方式（支付宝或微信支付）
7. 完成支付：跳转到支付页面完成支付
8. 等待交付：支付成功后，卖家会在1-3个工作日内交付商品文件
9. 确认收货：下载并检查文件，确认无误后点击"确认收货"
10. 评价商品：确认收货后可以对商品进行评价

注意事项：
- 购买前请仔细阅读商品描述和技术栈要求
- 确保商品符合您的毕业设计需求
- 如有疑问，可以通过AI客服咨询""",
            "metadata": {
                "type": "platform_rule",
                "category": "purchase_flow",
                "source": "platform_docs"
            }
        },
        {
            "id": "rule_payment_methods",
            "content": """支付方式说明：

支持的支付方式：
1. 支付宝支付
   - 扫码支付
   - 账户余额支付
   - 花呗分期（部分商品支持）

2. 微信支付
   - 扫码支付
   - 零钱支付
   - 银行卡支付

支付安全：
- 所有支付均通过第三方支付平台处理
- 平台不存储您的支付密码和银行卡信息
- 支付过程采用SSL加密传输

支付问题：
- 如果支付失败，请检查账户余额或网络连接
- 支付成功但订单未更新，请等待5分钟后刷新页面
- 如仍有问题，请联系客服处理""",
            "metadata": {
                "type": "platform_rule",
                "category": "payment",
                "source": "platform_docs"
            }
        },
        {
            "id": "rule_refund_policy",
            "content": """退款政策说明：

退款条件：
1. 商品未交付前可以随时取消订单，全额退款
2. 商品交付后，如有以下情况可申请退款：
   - 商品与描述严重不符
   - 文件无法打开或损坏
   - 代码无法运行或存在重大缺陷
   - 缺少承诺的交付内容

退款流程：
1. 在订单详情页点击"申请退款"
2. 选择退款原因并上传证明材料
3. 等待卖家响应（48小时内）
4. 如果卖家同意，退款会在3-5个工作日内到账
5. 如果卖家拒绝，可以申请平台介入

退款时效：
- 未交付订单：立即退款
- 已交付订单：审核通过后3-5个工作日到账
- 退款原路返回到支付账户

注意事项：
- 恶意退款会影响账户信用
- 退款前请先与卖家沟通
- 保留好相关证据（截图、聊天记录等）""",
            "metadata": {
                "type": "platform_rule",
                "category": "refund",
                "source": "platform_docs"
            }
        },
        {
            "id": "rule_seller_guide",
            "content": """卖家指南：

如何发布商品：
1. 进入卖家中心
2. 点击"发布商品"
3. 填写商品信息：
   - 标题：简洁明了，包含关键词
   - 描述：详细说明项目功能、技术栈、适用场景
   - 价格：合理定价，参考同类商品
   - 技术栈：准确标注使用的技术
   - 难度：如实标注项目难度
   - 交付内容：明确列出交付的文件和服务
4. 上传图片和文件
5. 提交审核

商品审核：
- 审核时间：1-2个工作日
- 审核标准：内容真实、描述准确、无违规内容
- 审核不通过会说明原因，可修改后重新提交

订单处理：
- 收到订单后请及时交付
- 交付时限：1-3个工作日
- 交付方式：上传文件到订单系统
- 及时回复买家咨询

收益结算：
- 买家确认收货后，款项会进入您的账户
- 可以随时提现到支付宝或银行卡
- 提现手续费：2%
- 到账时间：1-3个工作日""",
            "metadata": {
                "type": "platform_rule",
                "category": "seller_guide",
                "source": "platform_docs"
            }
        },
        {
            "id": "rule_faq",
            "content": """常见问题解答（FAQ）：

Q1: 购买的毕业设计可以直接使用吗？
A: 购买的作品可以作为参考和学习使用，但建议根据自己的实际情况进行修改和完善。直接使用可能存在重复率问题。

Q2: 如何选择合适的毕业设计？
A: 建议根据以下因素选择：
   - 专业方向是否匹配
   - 技术栈是否熟悉
   - 难度是否适合
   - 评价和销量
   - 价格是否合理

Q3: 商品包含哪些内容？
A: 一般包括：
   - 完整源代码
   - 数据库文件
   - 项目文档（需求、设计、测试等）
   - 部署说明
   - 答辩PPT（部分商品）
   具体内容请查看商品详情页的"交付内容"

Q4: 如何联系卖家？
A: 可以通过以下方式：
   - 在商品详情页留言
   - 购买后在订单页面联系
   - 通过AI客服转接

Q5: 文件下载后无法打开怎么办？
A: 请先检查：
   - 文件是否下载完整
   - 是否有对应的软件打开
   - 文件格式是否正确
   如仍无法解决，请联系卖家或客服

Q6: 可以要求卖家修改代码吗？
A: 这取决于商品说明：
   - 部分商品包含售后服务
   - 可以与卖家协商
   - 额外修改可能需要加价

Q7: 如何保证商品质量？
A: 平台有以下保障措施：
   - 商品审核机制
   - 用户评价系统
   - 退款保障
   - 卖家信用评级""",
            "metadata": {
                "type": "platform_rule",
                "category": "faq",
                "source": "platform_docs"
            }
        }
    ]
    
    # 添加到知识库
    try:
        await knowledge_retriever.add_documents(rules_documents, "knowledge_base")
        print(f"✓ 成功同步 {len(rules_documents)} 条平台规则到知识库")
    except Exception as e:
        print(f"✗ 同步平台规则失败：{e}")


async def sync_products():
    """同步商品到知识库"""
    async with get_db_context() as db:
        result = await product_knowledge_sync.sync_all_products(db)
        
        if result["success"]:
            print(f"✓ 商品同步完成：")
            print(f"  - 总数：{result['total']}")
            print(f"  - 成功：{result['success_count']}")
            print(f"  - 失败：{result['failed_count']}")
        else:
            print(f"✗ 商品同步失败：{result.get('message', '未知错误')}")


async def main():
    """主函数"""
    print("=" * 50)
    print("知识库同步工具")
    print("=" * 50)
    
    if not knowledge_retriever.available:
        print("✗ Chroma 向量数据库不可用")
        print("  请确保已安装 chromadb 并正确配置")
        return
    
    print("\n1. 同步平台规则...")
    await sync_platform_rules()
    
    print("\n2. 同步商品信息...")
    await sync_products()
    
    print("\n" + "=" * 50)
    print("同步完成！")
    print("=" * 50)
    
    # 显示统计信息
    kb_stats = knowledge_retriever.get_collection_stats("knowledge_base")
    product_stats = knowledge_retriever.get_collection_stats("product_catalog")
    
    print(f"\n知识库统计：")
    print(f"  - 知识库文档数：{kb_stats['count']}")
    print(f"  - 商品目录文档数：{product_stats['count']}")


if __name__ == "__main__":
    asyncio.run(main())
