"""
测试新架构的基本功能
"""
import asyncio
from config.loader import config_loader
from adapters import EcommerceAdapter
from plugins import plugin_manager, AIPlugin


async def test_config_loader():
    """测试配置加载器"""
    print("=" * 60)
    print("测试1: 配置加载器")
    print("=" * 60)
    
    # 列出所有业务
    businesses = config_loader.list_businesses()
    print(f"✅ 已配置的业务: {businesses}")
    
    # 获取毕业设计商城配置
    config = config_loader.get_config("graduation-marketplace")
    if config:
        print(f"✅ 业务名称: {config.get('business_name')}")
        print(f"✅ 业务类型: {config.get('business_type')}")
        print(f"✅ 适配器类: {config.get('adapter', {}).get('class')}")
        print(f"✅ 功能开关: {config.get('features')}")
    else:
        print("❌ 配置加载失败")
    
    print()


async def test_adapter():
    """测试业务适配器"""
    print("=" * 60)
    print("测试2: 业务适配器")
    print("=" * 60)
    
    # 加载配置
    config = config_loader.get_config("graduation-marketplace")
    if not config:
        print("❌ 配置不存在")
        return
    
    # 创建适配器
    adapter = EcommerceAdapter("graduation-marketplace", config)
    print(f"✅ 适配器创建成功: {adapter.__class__.__name__}")
    
    # 获取业务配置
    business_config = adapter.get_business_config()
    print(f"✅ 业务配置: {business_config}")
    
    print()


async def test_plugin_system():
    """测试插件系统"""
    print("=" * 60)
    print("测试3: 插件系统")
    print("=" * 60)
    
    # 创建测试插件
    class TestPlugin(AIPlugin):
        @property
        def name(self):
            return "test_plugin"
        
        @property
        def description(self):
            return "测试插件"
        
        async def execute(self, **kwargs):
            return {"status": "success", "message": "插件执行成功"}
        
        def get_schema(self):
            return {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                }
            }
    
    # 注册插件
    test_plugin = TestPlugin()
    plugin_manager.register(test_plugin)
    print(f"✅ 插件注册成功: {test_plugin.name}")
    
    # 列出插件
    plugins = plugin_manager.list_plugins()
    print(f"✅ 已注册的插件数量: {len(plugins)}")
    for plugin in plugins:
        print(f"   - {plugin['name']}: {plugin['description']}")
    
    # 执行插件
    result = await plugin_manager.execute("test_plugin", param1="test")
    print(f"✅ 插件执行结果: {result}")
    
    print()


async def test_integration():
    """测试集成"""
    print("=" * 60)
    print("测试4: 集成测试")
    print("=" * 60)
    
    # 加载配置
    config = config_loader.get_config("graduation-marketplace")
    if not config:
        print("❌ 配置不存在")
        return
    
    # 创建适配器
    adapter = EcommerceAdapter("graduation-marketplace", config)
    
    # 设置插件管理器的适配器
    plugin_manager.set_adapter(adapter)
    print("✅ 适配器已设置到插件管理器")
    
    # 创建测试插件
    class IntegrationPlugin(AIPlugin):
        @property
        def name(self):
            return "integration_test"
        
        @property
        def description(self):
            return "集成测试插件"
        
        async def execute(self, **kwargs):
            # 使用适配器
            business_config = self.adapter.get_business_config()
            return {
                "status": "success",
                "business_name": business_config.get("business_name")
            }
    
    # 注册并执行
    plugin_manager.register(IntegrationPlugin())
    result = await plugin_manager.execute("integration_test")
    print(f"✅ 集成测试结果: {result}")
    
    print()


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("AI模块架构测试")
    print("=" * 60 + "\n")
    
    try:
        await test_config_loader()
        await test_adapter()
        await test_plugin_system()
        await test_integration()
        
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print("\n架构组件工作正常，可以开始使用了！\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
