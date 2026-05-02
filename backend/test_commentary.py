#!/usr/bin/env python3
"""
注疏引证功能测试脚本
"""

from app.services.commentary_service import commentary_service

# 测试注疏文本（模拟《顺正理论述文记》的片段）
test_commentary_text = """
释《顺正理论》卷第十二。论云：诸法生时，皆有生相。此中云何名为生相？
谓能令法从未来世入现在世。如是说者，义不应然。何以故？
论曰：若法未生，云何可说有生相耶？此义难知，今当解释。
经云：一切有为法，皆从因缘生。是故诸法生相，即是缘起之相。
本论云：色法生时，必依四大种。此明色法之生相也。
颂曰：诸行无常，是生灭法。生灭灭已，寂灭为乐。
如论说：生相者，谓法从无至有之相状也。此释甚明。
论云：过去未来现在三世，皆有实法。此说三世实有也。
"""

# 测试底本文本（《顺正理论》卷12片段）
test_base_text = """
诸法生时，皆有生相。谓能令法从未来世入现在世。
若法未生，云何可说有生相耶？
一切有为法，皆从因缘生。
色法生时，必依四大种。
诸行无常，是生灭法。生灭灭已，寂灭为乐。
生相者，谓法从无至有之相状也。
过去未来现在三世，皆有实法。
"""

def test_extract_citations():
    """测试引文提取"""
    print("=" * 60)
    print("测试1：引文提取功能")
    print("=" * 60)

    citations = commentary_service.extract_citations(test_commentary_text)

    print(f"\n✅ 提取结果：共提取 {len(citations)} 条引文\n")

    for i, citation in enumerate(citations, 1):
        print(f"【引文 {i}】")
        print(f"  标记词：{citation.marker}")
        print(f"  引文内容：{citation.extracted_text}")
        print(f"  位置：{citation.start_pos} - {citation.end_pos}")
        print(f"  上下文前：...{citation.context_before}")
        print(f"  上下文后：{citation.context_after}...")
        print()

    return citations


def test_match_citation():
    """测试引文匹配"""
    print("=" * 60)
    print("测试2：引文匹配功能")
    print("=" * 60)

    # 先提取引文
    citations = commentary_service.extract_citations(test_commentary_text)

    if not citations:
        print("❌ 没有提取到引文，无法测试匹配")
        return

    # 测试几个位置的匹配
    test_positions = [0, 50, 100]  # 测试不同位置

    for position in test_positions:
        if position >= len(test_base_text):
            continue

        print(f"\n测试位置 {position}:")
        print(f"  窗口文本：{test_base_text[max(0, position-10):min(len(test_base_text), position+10)]}")

        matched_count = 0
        for citation in citations:
            match_result = commentary_service.match_citation_to_position(
                citation_text=citation.extracted_text,
                base_text=test_base_text,
                position=position,
                window_size=10,
                threshold=0.75
            )

            if match_result:
                matched_count += 1
                print(f"  ✅ 匹配到引文：{citation.marker}")
                print(f"     相似度：{match_result['similarity']:.2%}")
                print(f"     置信度：{match_result['confidence']}")
                print(f"     引文：{citation.extracted_text[:30]}...")

        if matched_count == 0:
            print(f"  ⚠️  此位置没有匹配的引文")


def test_similarity():
    """测试相似度计算"""
    print("\n" + "=" * 60)
    print("测试3：相似度计算")
    print("=" * 60)

    from app.services.collation_service import collation_service

    test_pairs = [
        ("诸法生时，皆有生相", "诸法生时，皆有生相"),  # 完全相同
        ("诸法生时，皆有生相", "诸法生时皆有生相"),    # 去除标点
        ("诸法生时，皆有生相", "诸法生时，有生相"),    # 少一字
        ("诸法生时，皆有生相", "完全不同的文字"),      # 完全不同
    ]

    print()
    for text1, text2 in test_pairs:
        similarity = collation_service._compute_similarity(text1, text2)
        print(f"文本1: {text1}")
        print(f"文本2: {text2}")
        print(f"相似度: {similarity:.2%}")
        print()


if __name__ == "__main__":
    print("\n" + "🔬 注疏引证功能测试" + "\n")

    try:
        # 测试1：引文提取
        citations = test_extract_citations()

        # 测试2：引文匹配
        if citations:
            test_match_citation()

        # 测试3：相似度计算
        test_similarity()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
