"""
性能对比测试脚本
对比原版和优化版的性能差异
"""

import time
import json
from typing import List, Dict


def simulate_original_version(links: List[str]) -> Dict:
    """
    模拟原版代码的执行逻辑
    注意：这只是模拟，不会真正调用API
    """
    print("\n" + "=" * 60)
    print("原版代码执行模拟")
    print("=" * 60)

    start_time = time.time()
    api_calls = 0
    success_count = 0

    for idx, link in enumerate(links, 1):
        # 模拟第一次API调用
        time.sleep(0.1)  # 模拟网络延迟
        api_calls += 1

        # 假设30%的情况下第一次调用失败，需要第二次调用
        if idx % 3 == 0:
            time.sleep(0.1)  # 模拟第二次API调用
            api_calls += 1

        success_count += 1

        # 原版每个链接后sleep(1)
        time.sleep(1)

    elapsed_time = time.time() - start_time

    result = {
        "version": "原版",
        "total_links": len(links),
        "success_count": success_count,
        "api_calls": api_calls,
        "elapsed_time": elapsed_time,
        "avg_time_per_link": elapsed_time / len(links),
    }

    print(f"处理完成: {success_count}/{len(links)} 成功")
    print(f"API调用次数: {api_calls}")
    print(f"总耗时: {elapsed_time:.2f}秒")
    print(f"平均每个链接: {result['avg_time_per_link']:.2f}秒")

    return result


def simulate_optimized_version(links: List[str]) -> Dict:
    """
    模拟优化版代码的执行逻辑
    注意：这只是模拟，不会真正调用API
    """
    print("\n" + "=" * 60)
    print("优化版代码执行模拟")
    print("=" * 60)

    start_time = time.time()
    api_calls = 0
    success_count = 0

    # 速率限制：每秒最多5次请求
    min_interval = 1.0 / 5  # 0.2秒
    last_call_time = 0

    for idx, link in enumerate(links, 1):
        # 速率控制
        now = time.time()
        elapsed_since_last = now - last_call_time
        if elapsed_since_last < min_interval:
            sleep_time = min_interval - elapsed_since_last
            time.sleep(sleep_time)

        # 模拟智能API调用（先判断，减少不必要的调用）
        time.sleep(0.1)  # 模拟网络延迟
        api_calls += 1
        last_call_time = time.time()

        # 假设只有20%的情况需要第二次调用（因为优化了策略）
        if idx % 5 == 0:
            now = time.time()
            elapsed_since_last = now - last_call_time
            if elapsed_since_last < min_interval:
                sleep_time = min_interval - elapsed_since_last
                time.sleep(sleep_time)

            time.sleep(0.1)
            api_calls += 1
            last_call_time = time.time()

        success_count += 1

        # 进度反馈（每5个输出一次）
        if idx % 5 == 0 or idx == len(links):
            progress = (idx / len(links)) * 100
            print(f"进度: {idx}/{len(links)} ({progress:.1f}%)")

    elapsed_time = time.time() - start_time

    result = {
        "version": "优化版",
        "total_links": len(links),
        "success_count": success_count,
        "api_calls": api_calls,
        "elapsed_time": elapsed_time,
        "avg_time_per_link": elapsed_time / len(links),
    }

    print(f"处理完成: {success_count}/{len(links)} 成功")
    print(f"API调用次数: {api_calls}")
    print(f"总耗时: {elapsed_time:.2f}秒")
    print(f"平均每个链接: {result['avg_time_per_link']:.2f}秒")

    return result


def compare_results(original: Dict, optimized: Dict):
    """对比两个版本的结果"""
    print("\n" + "=" * 60)
    print("性能对比报告")
    print("=" * 60)

    # 计算改进百分比
    time_improvement = ((original["elapsed_time"] - optimized["elapsed_time"])
                        / original["elapsed_time"] * 100)
    api_improvement = ((original["api_calls"] - optimized["api_calls"])
                       / original["api_calls"] * 100)

    print(f"\n链接数量: {original['total_links']}")
    print(f"\n{'指标':<20} {'原版':>15} {'优化版':>15} {'改进':>15}")
    print("-" * 70)

    print(f"{'总耗时(秒)':<20} {original['elapsed_time']:>15.2f} "
          f"{optimized['elapsed_time']:>15.2f} "
          f"{time_improvement:>14.1f}%")

    print(f"{'API调用次数':<20} {original['api_calls']:>15} "
          f"{optimized['api_calls']:>15} "
          f"{api_improvement:>14.1f}%")

    print(f"{'平均耗时(秒/链接)':<20} {original['avg_time_per_link']:>15.2f} "
          f"{optimized['avg_time_per_link']:>15.2f} "
          f"{((original['avg_time_per_link'] - optimized['avg_time_per_link']) / original['avg_time_per_link'] * 100):>14.1f}%")

    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)

    if time_improvement > 0:
        print(f"✅ 速度提升: {time_improvement:.1f}%")
    else:
        print(f"⚠️  速度下降: {abs(time_improvement):.1f}%")

    if api_improvement > 0:
        print(f"✅ API调用减少: {api_improvement:.1f}%")
    else:
        print(f"⚠️  API调用增加: {abs(api_improvement):.1f}%")

    print(f"\n估算处理100个链接的耗时:")
    print(f"  原版: {original['avg_time_per_link'] * 100:.1f}秒 ({original['avg_time_per_link'] * 100 / 60:.1f}分钟)")
    print(f"  优化版: {optimized['avg_time_per_link'] * 100:.1f}秒 ({optimized['avg_time_per_link'] * 100 / 60:.1f}分钟)")
    print(f"  节省: {(original['avg_time_per_link'] - optimized['avg_time_per_link']) * 100:.1f}秒")


def run_comparison_test(num_links: int = 15):
    """
    运行对比测试

    Args:
        num_links: 测试的链接数量
    """
    print(f"\n开始性能对比测试 (模拟{num_links}个链接)")
    print(f"注意: 这是模拟测试，不会真正调用API\n")

    # 生成测试链接
    test_links = [
        f"https://www.xiaohongshu.com/explore/test{i:03d}"
        for i in range(num_links)
    ]

    # 测试原版
    original_result = simulate_original_version(test_links)

    # 短暂暂停
    time.sleep(1)

    # 测试优化版
    optimized_result = simulate_optimized_version(test_links)

    # 对比结果
    compare_results(original_result, optimized_result)


def estimate_processing_time(num_links: int):
    """
    估算处理指定数量链接所需的时间

    Args:
        num_links: 链接数量
    """
    print(f"\n估算处理 {num_links} 个链接的时间:")
    print("-" * 60)

    # 原版估算
    # 假设: 每个链接sleep(1) + 平均1.5次API调用 * 0.1秒延迟
    original_time = num_links * (1 + 1.5 * 0.1)
    print(f"原版预计耗时: {original_time:.1f}秒 ({original_time/60:.1f}分钟)")

    # 优化版估算
    # 假设: 平均1.2次API调用 * (0.2秒速率限制 + 0.1秒延迟)
    optimized_time = num_links * 1.2 * 0.3
    print(f"优化版预计耗时: {optimized_time:.1f}秒 ({optimized_time/60:.1f}分钟)")

    improvement = (original_time - optimized_time) / original_time * 100
    print(f"预计提升: {improvement:.1f}%")

    # Dify超时检查
    print(f"\nDify环境检查:")
    dify_timeout = 50  # Dify假设的超时时间
    if optimized_time > dify_timeout:
        print(f"⚠️  警告: 预计耗时({optimized_time:.1f}秒)超过Dify超时限制({dify_timeout}秒)")
        max_safe_links = int(dify_timeout / (1.2 * 0.3))
        print(f"   建议: 单次处理不超过 {max_safe_links} 个链接")
    else:
        print(f"✅ 安全: 预计耗时在Dify超时限制内")


if __name__ == "__main__":
    # 测试1: 15个链接的对比
    run_comparison_test(num_links=15)

    print("\n\n")

    # 测试2: 不同数量链接的估算
    for num in [10, 20, 50, 100]:
        estimate_processing_time(num)
        print()
