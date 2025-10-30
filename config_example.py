"""
小红书笔记抓取器 - 配置示例
根据不同场景选择合适的配置
"""

# ============================================================
# 场景1: 保守配置（推荐用于Dify，最稳定）
# ============================================================
CONSERVATIVE_CONFIG = {
    "api_key": "apikeyxxx",
    "max_requests_per_second": 4,  # 留1次余量，更安全
    "timeout": 15,                  # 超时时间较长
    "batch_size": 3,                # 小批次，频繁输出进度
    "max_links_per_call": 10,       # 单次最多处理10个链接
}

# 使用示例：
# scraper = XHSNoteScraper(
#     api_key=CONSERVATIVE_CONFIG["api_key"],
#     max_requests_per_second=CONSERVATIVE_CONFIG["max_requests_per_second"]
# )
# scraper.timeout = CONSERVATIVE_CONFIG["timeout"]
# excel_data = scraper.process_links(links[:10], batch_size=3)


# ============================================================
# 场景2: 标准配置（推荐用于本地运行）
# ============================================================
STANDARD_CONFIG = {
    "api_key": "apikeyxxx",
    "max_requests_per_second": 5,  # 标准速率限制
    "timeout": 10,                  # 标准超时
    "batch_size": 5,                # 中等批次
    "max_links_per_call": 20,       # 单次最多处理20个链接
}


# ============================================================
# 场景3: 激进配置（仅在API限制宽松时使用）
# ============================================================
AGGRESSIVE_CONFIG = {
    "api_key": "apikeyxxx",
    "max_requests_per_second": 8,  # 更高频率（需确认API支持）
    "timeout": 8,                   # 较短超时
    "batch_size": 10,               # 大批次
    "max_links_per_call": 50,       # 单次最多处理50个链接
}


# ============================================================
# 场景4: 调试配置（用于问题排查）
# ============================================================
DEBUG_CONFIG = {
    "api_key": "apikeyxxx",
    "max_requests_per_second": 2,  # 很慢，便于观察
    "timeout": 30,                  # 很长超时
    "batch_size": 1,                # 每个链接都输出
    "max_links_per_call": 5,        # 少量链接测试
    "verbose": True,                # 详细日志
}


# ============================================================
# Dify环境专用配置
# ============================================================
DIFY_CONFIG = {
    # 基础配置
    "api_key": "apikeyxxx",
    "max_requests_per_second": 4,
    "timeout": 12,
    "batch_size": 5,

    # Dify特殊限制
    "max_execution_time": 50,      # Dify总超时限制（秒）
    "max_links_per_call": 15,      # 根据超时计算的最大链接数

    # 计算公式：
    # max_links = (max_execution_time - 5) / (1 / max_requests_per_second + 1)
    # = (50 - 5) / (0.25 + 1) = 36
    # 保守估计取15
}


# ============================================================
# 配置选择器
# ============================================================
def get_config(environment="dify", profile="conservative"):
    """
    获取推荐配置

    Args:
        environment: 运行环境 ("dify" | "local" | "server")
        profile: 配置档案 ("conservative" | "standard" | "aggressive" | "debug")

    Returns:
        配置字典
    """
    configs = {
        "conservative": CONSERVATIVE_CONFIG,
        "standard": STANDARD_CONFIG,
        "aggressive": AGGRESSIVE_CONFIG,
        "debug": DEBUG_CONFIG,
    }

    if environment == "dify":
        return DIFY_CONFIG
    else:
        return configs.get(profile, STANDARD_CONFIG)


# ============================================================
# 使用示例
# ============================================================
if __name__ == "__main__":
    # 示例1: Dify环境
    config = get_config(environment="dify")
    print("Dify配置:", config)

    # 示例2: 本地调试
    config = get_config(environment="local", profile="debug")
    print("调试配置:", config)

    # 示例3: 服务器高性能
    config = get_config(environment="server", profile="aggressive")
    print("激进配置:", config)


# ============================================================
# 快速配置函数（可直接用于main函数）
# ============================================================
def create_scraper_for_dify(api_key="apikeyxxx"):
    """为Dify环境创建优化的爬虫实例"""
    from xhs_scraper_optimized import XHSNoteScraper

    scraper = XHSNoteScraper(
        api_key=api_key,
        max_requests_per_second=DIFY_CONFIG["max_requests_per_second"]
    )
    scraper.timeout = DIFY_CONFIG["timeout"]
    return scraper


def process_links_for_dify(scraper, links):
    """
    为Dify环境处理链接（带自动分批）

    Args:
        scraper: XHSNoteScraper实例
        links: 链接列表

    Returns:
        Excel格式数据
    """
    max_links = DIFY_CONFIG["max_links_per_call"]

    # 如果链接数过多，只处理前max_links个
    if len(links) > max_links:
        print(f"警告: 链接数({len(links)})超过限制，只处理前{max_links}个")
        links = links[:max_links]

    return scraper.process_links(
        links,
        batch_size=DIFY_CONFIG["batch_size"]
    )


# ============================================================
# Dify优化版main函数
# ============================================================
def main_optimized_for_dify(links):
    """
    Dify环境优化版main函数
    - 自动配置参数
    - 自动处理批次
    - 自动超时保护
    """
    import json

    # 参数处理
    if not isinstance(links, list):
        links = [links] if links else []

    if not links:
        return {"result": "请输入链接"}

    # 去重和清理
    links = list(dict.fromkeys(links))
    links = [link.strip() for link in links if link and link.strip()]

    if not links:
        return {"result": "没有有效的链接"}

    try:
        # 创建Dify优化的爬虫实例
        scraper = create_scraper_for_dify(api_key="apikeyxxx")

        # 处理链接（自动分批）
        excel_data = process_links_for_dify(scraper, links)

        # 返回结果
        return {"result": json.dumps(excel_data, ensure_ascii=False)}

    except Exception as e:
        error_msg = f"处理出错: {str(e)}"
        print(error_msg)
        return {"result": error_msg}
