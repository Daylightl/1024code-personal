import re
import requests
import json
import time
from collections import deque
from typing import List, Dict, Tuple


class RateLimiter:
    """速率限制器 - 使用滑动窗口算法确保1秒内不超过5次请求"""

    def __init__(self, max_calls: int = 5, time_window: float = 1.0):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()

    def wait_if_needed(self):
        """如果需要则等待，确保不超过速率限制"""
        now = time.time()

        # 移除时间窗口外的旧调用记录
        while self.calls and self.calls[0] <= now - self.time_window:
            self.calls.popleft()

        # 如果达到限制，等待直到最旧的调用超出时间窗口
        if len(self.calls) >= self.max_calls:
            sleep_time = self.calls[0] + self.time_window - now
            if sleep_time > 0:
                print(f"速率限制：等待 {sleep_time:.2f} 秒...")
                time.sleep(sleep_time)
                # 清理过期记录
                now = time.time()
                while self.calls and self.calls[0] <= now - self.time_window:
                    self.calls.popleft()

        # 记录本次调用
        self.calls.append(time.time())


class XHSNoteScraper:
    """小红书笔记抓取器"""

    def __init__(self, api_key: str, max_requests_per_second: int = 5):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self.rate_limiter = RateLimiter(max_calls=max_requests_per_second)
        self.pattern = re.compile(r'/(?:item|explore)/([a-zA-Z0-9]+)[/?]?')
        self.url_v3 = "http://api.moreapi.cn/api/xhs/note_detail_v3"
        self.url_kol = "http://api.moreapi.cn/api/xhs_kol/note_detail"
        # 请求超时设置（避免hang住）
        self.timeout = 10

    def extract_note_id(self, link: str) -> str:
        """从链接中提取note_id"""
        match = self.pattern.search(link)
        return match.group(1) if match else ""

    def fetch_with_share_text(self, link: str) -> Tuple[bool, Dict]:
        """使用share_text方式获取笔记详情"""
        try:
            self.rate_limiter.wait_if_needed()
            payload = json.dumps({"share_text": link})
            response = requests.post(
                self.url_v3,
                headers=self.headers,
                data=payload,
                allow_redirects=True,
                timeout=self.timeout
            )

            if response.status_code != 200:
                return False, {}

            json_data = response.json() or {}
            data = json_data.get("data", {})
            note_data = data.get("note_data", {})

            if not note_data.get("note_id"):
                return False, {}

            return True, {
                "note_id": note_data.get("note_id", ""),
                "title": note_data.get("title", ""),
                "content": note_data.get("desc", "")
            }
        except Exception as e:
            print(f"share_text方式失败: {str(e)}")
            return False, {}

    def fetch_with_note_id(self, note_id: str) -> Tuple[bool, Dict]:
        """使用note_id方式获取笔记详情"""
        try:
            self.rate_limiter.wait_if_needed()
            payload = json.dumps({"note_id": note_id})
            response = requests.post(
                self.url_kol,
                headers=self.headers,
                data=payload,
                allow_redirects=True,
                timeout=self.timeout
            )

            if response.status_code != 200:
                return False, {}

            json_data = response.json() or {}
            data = json_data.get("data", {}).get("data", {})

            if not data.get("noteId"):
                return False, {}

            return True, {
                "note_id": data.get("noteId", ""),
                "title": data.get("title", ""),
                "content": data.get("content", "")
            }
        except Exception as e:
            print(f"note_id方式失败: {str(e)}")
            return False, {}

    def fetch_note(self, link: str) -> Dict:
        """
        智能获取笔记详情
        策略：先尝试从链接提取note_id，如果成功则优先使用note_id接口
        如果失败，再尝试share_text接口
        """
        note_id = self.extract_note_id(link)

        # 策略1: 如果能提取note_id，优先使用note_id接口（通常更稳定）
        if note_id:
            success, result = self.fetch_with_note_id(note_id)
            if success:
                return result

        # 策略2: 尝试share_text接口
        success, result = self.fetch_with_share_text(link)
        if success:
            return result

        # 策略3: 如果策略1中提取了note_id但失败，且策略2也失败，再次尝试note_id
        if note_id:
            success, result = self.fetch_with_note_id(note_id)
            if success:
                return result

        # 所有策略都失败
        return {
            "note_id": "获取失败",
            "title": "获取失败",
            "content": "获取失败"
        }

    def process_links(self, links: List[str], batch_size: int = 10) -> List[List[str]]:
        """
        批量处理链接

        Args:
            links: 链接列表
            batch_size: 批次大小，每处理一批输出一次进度

        Returns:
            Excel格式的数据列表
        """
        excel_data = [['笔记链接', '笔记ID', '标题', '内容']]
        total = len(links)

        print(f"开始处理 {total} 个链接...")

        for idx, link in enumerate(links, 1):
            try:
                # 获取笔记详情
                result = self.fetch_note(link)

                # 添加到结果
                excel_data.append([
                    str(link),
                    str(result.get("note_id", "获取失败")),
                    str(result.get("title", "获取失败")),
                    str(result.get("content", "获取失败"))
                ])

                # 每处理batch_size个或最后一个，输出进度
                if idx % batch_size == 0 or idx == total:
                    progress = (idx / total) * 100
                    print(f"进度: {idx}/{total} ({progress:.1f}%) - 最新: {result.get('title', '获取失败')[:20]}...")

            except Exception as e:
                print(f"处理链接 {link} 时出错: {str(e)}")
                excel_data.append([
                    str(link),
                    "系统错误",
                    "系统错误",
                    str(e)
                ])

        print(f"处理完成！成功获取 {total} 个笔记信息")
        return excel_data


def main(links):
    """
    主函数 - Dify兼容接口

    Args:
        links: 单个链接字符串或链接列表

    Returns:
        包含result字段的字典，result为JSON字符串格式的表格数据
    """
    # 参数处理
    if not isinstance(links, list):
        links = [links] if links else []

    if not links:
        return {"result": "请输入链接"}

    # 去重和清理
    links = list(dict.fromkeys(links))  # 保持顺序的去重
    links = [link.strip() for link in links if link and link.strip()]

    if not links:
        return {"result": "没有有效的链接"}

    try:
        # 创建爬虫实例（替换为你的API Key）
        scraper = XHSNoteScraper(
            api_key="apikeyxxx",
            max_requests_per_second=5  # 严格控制每秒最多5次请求
        )

        # 处理链接
        excel_data = scraper.process_links(links, batch_size=5)

        # 返回JSON格式结果
        return {"result": json.dumps(excel_data, ensure_ascii=False)}

    except Exception as e:
        error_msg = f"处理出错: {str(e)}"
        print(error_msg)
        return {"result": error_msg}


# 测试代码
if __name__ == "__main__":
    # 测试单个链接
    test_links = [
        "https://www.xiaohongshu.com/explore/63f5e5e5000000001f00e6a0",
        "https://www.xiaohongshu.com/explore/63f5e5e5000000001f00e6a1",
    ]

    result = main(test_links)
    print("\n最终结果:")
    print(result)
