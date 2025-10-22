import re
import requests
import json
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import threading


class ThreadSafeRateLimiter:
    """线程安全的速率限制器 - 使用滑动窗口算法"""

    def __init__(self, max_calls: int = 5, time_window: float = 1.0):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
        self._lock = threading.Lock()

    def wait_if_needed(self):
        """如果需要则等待，确保不超过速率限制（线程安全）"""
        with self._lock:
            now = time.time()

            # 移除时间窗口外的旧调用记录
            while self.calls and self.calls[0] <= now - self.time_window:
                self.calls.popleft()

            # 如果达到限制，等待直到最旧的调用超出时间窗口
            if len(self.calls) >= self.max_calls:
                sleep_time = self.calls[0] + self.time_window - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    # 清理过期记录
                    now = time.time()
                    while self.calls and self.calls[0] <= now - self.time_window:
                        self.calls.popleft()

            # 记录本次调用
            self.calls.append(time.time())


class ConcurrentXHSNoteScraper:
    """
    小红书笔记抓取器 - 多线程并发版本

    特点：
    - 使用标准库 concurrent.futures，无需额外依赖
    - 线程池并发处理，充分利用IO等待时间
    - 线程安全的速率限制
    - 适合Dify环境使用
    """

    def __init__(self, api_key: str, max_requests_per_second: int = 5, max_workers: int = 10):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self.rate_limiter = ThreadSafeRateLimiter(max_calls=max_requests_per_second)
        self.pattern = re.compile(r'/(?:item|explore)/([a-zA-Z0-9]+)[/?]?')
        self.url_v3 = "http://api.moreapi.cn/api/xhs/note_detail_v3"
        self.url_kol = "http://api.moreapi.cn/api/xhs_kol/note_detail"
        self.timeout = 10
        self.max_workers = max_workers
        self._progress_lock = threading.Lock()

    def extract_note_id(self, link: str) -> str:
        """从链接中提取note_id"""
        match = self.pattern.search(link)
        return match.group(1) if match else ""

    def _make_request(self, url: str, payload: dict) -> Tuple[bool, dict]:
        """发起HTTP请求（带速率限制）"""
        try:
            self.rate_limiter.wait_if_needed()  # 速率限制
            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(payload),
                allow_redirects=True,
                timeout=self.timeout
            )

            if response.status_code != 200:
                return False, {}

            data = response.json()
            return True, data
        except Exception as e:
            print(f"请求失败: {str(e)}")
            return False, {}

    def fetch_with_share_text(self, link: str) -> Tuple[bool, Dict]:
        """使用share_text方式获取笔记详情"""
        payload = {"share_text": link}
        success, json_data = self._make_request(self.url_v3, payload)

        if not success:
            return False, {}

        data = json_data.get("data", {})
        note_data = data.get("note_data", {})

        if not note_data.get("note_id"):
            return False, {}

        return True, {
            "note_id": note_data.get("note_id", ""),
            "title": note_data.get("title", ""),
            "content": note_data.get("desc", "")
        }

    def fetch_with_note_id(self, note_id: str) -> Tuple[bool, Dict]:
        """使用note_id方式获取笔记详情"""
        payload = {"note_id": note_id}
        success, json_data = self._make_request(self.url_kol, payload)

        if not success:
            return False, {}

        data = json_data.get("data", {}).get("data", {})

        if not data.get("noteId"):
            return False, {}

        return True, {
            "note_id": data.get("noteId", ""),
            "title": data.get("title", ""),
            "content": data.get("content", "")
        }

    def fetch_single_note(self, link: str, index: int, total: int) -> Dict:
        """
        获取单个笔记（在线程池中执行）

        Args:
            link: 笔记链接
            index: 当前索引
            total: 总数量

        Returns:
            包含link和data的字典
        """
        try:
            note_id = self.extract_note_id(link)

            # 策略1: 优先使用note_id
            if note_id:
                success, result = self.fetch_with_note_id(note_id)
                if success:
                    return {"link": link, "data": result, "index": index}

            # 策略2: 尝试share_text
            success, result = self.fetch_with_share_text(link)
            if success:
                return {"link": link, "data": result, "index": index}

            # 策略3: 再次尝试note_id
            if note_id:
                success, result = self.fetch_with_note_id(note_id)
                if success:
                    return {"link": link, "data": result, "index": index}

            # 所有策略都失败
            return {
                "link": link,
                "data": {
                    "note_id": "获取失败",
                    "title": "获取失败",
                    "content": "获取失败"
                },
                "index": index
            }

        except Exception as e:
            print(f"处理链接 {link} 时出错: {str(e)}")
            return {
                "link": link,
                "data": {
                    "note_id": "系统错误",
                    "title": "系统错误",
                    "content": str(e)
                },
                "index": index
            }

    def process_links_concurrent(self, links: List[str]) -> List[List[str]]:
        """
        多线程并发处理所有链接

        Args:
            links: 链接列表

        Returns:
            Excel格式的数据列表
        """
        total = len(links)
        print(f"开始并发处理 {total} 个链接...")
        print(f"配置: 速率限制={self.rate_limiter.max_calls}/秒, 线程数={self.max_workers}")

        start_time = time.time()
        results = []
        completed = 0

        # 使用线程池执行任务
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_link = {
                executor.submit(self.fetch_single_note, link, idx, total): link
                for idx, link in enumerate(links, 1)
            }

            # 收集结果（按完成顺序）
            for future in as_completed(future_to_link):
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1

                    # 每完成10个或完成全部，输出进度
                    if completed % 10 == 0 or completed == total:
                        with self._progress_lock:
                            elapsed = time.time() - start_time
                            progress = (completed / total) * 100
                            rate = completed / elapsed if elapsed > 0 else 0
                            eta = (total - completed) / rate if rate > 0 else 0
                            print(f"进度: {completed}/{total} ({progress:.1f}%) | "
                                  f"耗时: {elapsed:.1f}秒 | 速率: {rate:.1f}个/秒 | "
                                  f"预计剩余: {eta:.1f}秒")

                except Exception as e:
                    print(f"处理任务时出错: {str(e)}")
                    completed += 1

        # 按原始顺序排序结果
        results.sort(key=lambda x: x.get("index", 0))

        # 构建结果表格
        excel_data = [['笔记链接', '笔记ID', '标题', '内容']]

        for result in results:
            link = result["link"]
            data = result["data"]
            excel_data.append([
                str(link),
                str(data.get("note_id", "获取失败")),
                str(data.get("title", "获取失败")),
                str(data.get("content", "获取失败"))
            ])

        elapsed_time = time.time() - start_time
        print(f"\n处理完成！")
        print(f"总耗时: {elapsed_time:.2f}秒")
        print(f"平均速率: {total/elapsed_time:.2f}个/秒")
        print(f"成功获取 {total} 个笔记信息")

        return excel_data


def main(links):
    """
    主函数 - Dify兼容接口（多线程并发版本）

    特点：
    - 只使用标准库（无需aiohttp）
    - 多线程并发处理
    - 线程安全的速率限制
    - 适合处理30-50个链接

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
    links = list(dict.fromkeys(links))
    links = [link.strip() for link in links if link and link.strip()]

    if not links:
        return {"result": "没有有效的链接"}

    try:
        # 创建多线程并发爬虫实例
        scraper = ConcurrentXHSNoteScraper(
            api_key="apikeyxxx",  # 替换为你的API Key
            max_requests_per_second=5,  # 每秒最多5次请求
            max_workers=10  # 线程池大小：10个工作线程
        )

        # 并发处理链接
        excel_data = scraper.process_links_concurrent(links)

        # 返回JSON格式结果
        return {"result": json.dumps(excel_data, ensure_ascii=False)}

    except Exception as e:
        error_msg = f"处理出错: {str(e)}"
        print(error_msg)
        return {"result": error_msg}


# 测试代码
if __name__ == "__main__":
    # 测试50个链接
    test_links = [
        f"https://www.xiaohongshu.com/explore/test{i:03d}"
        for i in range(50)
    ]

    print("=" * 60)
    print("多线程并发版本测试（无需aiohttp）")
    print("=" * 60)

    result = main(test_links)
    print("\n最终结果:")
    data = json.loads(result["result"])
    print(f"获取到 {len(data)-1} 条笔记")
