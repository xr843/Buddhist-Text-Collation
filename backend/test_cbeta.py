#!/usr/bin/env python3
"""
CBETA服务测试脚本
测试搜索和XML解析功能
"""
import asyncio
from app.services.cbeta_service import CBETAService


async def test_search():
    """测试搜索功能"""
    print("=" * 60)
    print("测试1: 搜索经文")
    print("=" * 60)

    keywords = ["金刚", "心经", "T0235"]

    for keyword in keywords:
        print(f"\n搜索关键词: {keyword}")
        results = await CBETAService.search_sutra(keyword, limit=5)
        print(f"找到 {len(results)} 条结果:")
        for sutra in results:
            print(f"  - {sutra['id']}: {sutra['title']} ({sutra['dynasty']} {sutra['translator']})")


async def test_fetch_and_parse():
    """测试获取和解析XML"""
    print("\n" + "=" * 60)
    print("测试2: 获取并解析经文XML")
    print("=" * 60)

    sutra_id = "T1558_001"  # 阿毘達磨俱舍論（卷1）

    print(f"\n正在获取 {sutra_id} 的XML...")
    xml_content = await CBETAService.fetch_sutra_xml(sutra_id)

    if xml_content:
        print(f"✅ 成功获取XML (长度: {len(xml_content)} 字符)")

        print("\n正在解析XML...")
        parsed_data = CBETAService.parse_cbeta_xml(xml_content)

        print(f"✅ 解析成功:")
        print(f"  标题: {parsed_data.get('title', 'N/A')}")
        print(f"  作者: {parsed_data.get('author', 'N/A')}")
        print(f"  文本长度: {len(parsed_data.get('text', ''))} 字")
        print(f"  校勘记数量: {len(parsed_data.get('collations', []))}")

        if parsed_data.get('collations'):
            print("\n  前3条校勘记:")
            for i, collation in enumerate(parsed_data['collations'][:3], 1):
                print(f"    {i}. 位置{collation['position']}: {collation['lemma']} (共{len(collation['readings'])}个异文)")
    else:
        print(f"❌ 无法获取 {sutra_id} 的XML")
        print("  注意: 这可能是因为:")
        print("  1. 网络问题")
        print("  2. GitHub仓库路径变更")
        print("  3. 该经号不存在")


async def test_import():
    """测试完整导入流程"""
    print("\n" + "=" * 60)
    print("测试3: 完整导入流程")
    print("=" * 60)

    sutra_id = "T1558_001"

    print(f"\n正在导入 {sutra_id}...")
    data = await CBETAService.import_from_cbeta(sutra_id)

    if data:
        print(f"✅ 导入成功:")
        print(f"  经号: {data.get('sutra_id')}")
        print(f"  标题: {data.get('title')}")
        print(f"  文本长度: {len(data.get('text', ''))} 字")
        print(f"  校勘记: {len(data.get('collations', []))} 条")
    else:
        print(f"❌ 导入失败")


async def test_contribution_report():
    """测试勘误报告生成"""
    print("\n" + "=" * 60)
    print("测试4: 生成CBETA勘误报告")
    print("=" * 60)

    new_findings = [
        {
            'position': 123,
            'base_char': '法',
            'variant_char': '去',
            'source': '高丽藏',
            'category': 'error'
        },
        {
            'position': 456,
            'base_char': '如是',
            'variant_char': '如斯',
            'source': '赵城金藏',
            'category': 'variant'
        }
    ]

    report = CBETAService.generate_cbeta_contribution_report(
        new_findings=new_findings,
        sutra_id="T0235",
        contributor_name="测试研究者"
    )

    print("\n生成的报告:")
    print("-" * 60)
    print(report)
    print("-" * 60)


async def main():
    """主测试函数"""
    print("\n🧪 CBETA服务集成测试")
    print("=" * 60)

    try:
        await test_search()
        await test_fetch_and_parse()
        await test_import()
        await test_contribution_report()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
