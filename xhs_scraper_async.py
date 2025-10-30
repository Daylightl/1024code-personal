import re
import json
import time
import asyncio
import aiohttp
from collections import deque
from typing import List, Dict, Tuple


class AsyncRateLimiter:
    """异步速率限制器 - 支持并发场景"""

    def __init__(self, max_calls: int = 5, time_window: float = 1.0):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """获取许可，如果需要则等待"""
        async with self._lock:
            now = time.time()

            # 移除过期记录
            while self.calls and self.calls[0] <= now - self.time_window:
                self.calls.popleft()

            # 如果达到限制，等待
            if len(self.calls) >= self.max_calls:
                sleep_time = self.calls[0] + self.time_window - now
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    # 再次清理
                    now = time.time()
                    while self.calls and self.calls[0] <= now - self.time_window:
                        self.calls.popleft()

            # 记录本次调用
            self.calls.append(time.time())


class AsyncXHSNoteScraper:
    """小红书笔记抓取器 - 异步并发版本"""

    def __init__(self, api_key: str, max_requests_per_second: int = 5, concurrent_limit: int = 10):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self.rate_limiter = AsyncRateLimiter(max_calls=max_requests_per_second)
        self.pattern = re.compile(r'/(?:item|explore)/([a-zA-Z0-9]+)[/?]?')
        self.url_v3 = "http://api.moreapi.cn/api/xhs/note_detail_v3"
        self.url_kol = "http://api.moreapi.cn/api/xhs_kol/note_detail"
        self.timeout = aiohttp.ClientTimeout(total=10)
        # 并发限制：同时最多处理多少个链接
        self.semaphore = asyncio.Semaphore(concurrent_limit)

    def extract_note_id(self, link: str) -> str:
        """从链接中提取note_id"""
        match = self.pattern.search(link)
        return match.group(1) if match else ""

    async def _make_request(self, session: aiohttp.ClientSession, url: str, payload: dict) -> Tuple[bool, dict]:
        """发起HTTP请求"""
        try:
            await self.rate_limiter.acquire()  # 速率限制
            async with session.post(url, json=payload, headers=self.headers, timeout=self.timeout) as response:
                if response.status != 200:
                    return False, {}
                data = await response.json()
                return True, data
        except Exception as e:
            print(f"请求失败: {str(e)}")
            return False, {}

    async def fetch_with_share_text(self, session: aiohttp.ClientSession, link: str) -> Tuple[bool, Dict]:
        """使用share_text方式获取笔记详情"""
        payload = {"share_text": link}
        success, json_data = await self._make_request(session, self.url_v3, payload)

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

    async def fetch_with_note_id(self, session: aiohttp.ClientSession, note_id: str) -> Tuple[bool, Dict]:
        """使用note_id方式获取笔记详情"""
        payload = {"note_id": note_id}
        success, json_data = await self._make_request(session, self.url_kol, payload)

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

    async def fetch_single_note(self, session: aiohttp.ClientSession, link: str, index: int, total: int) -> Dict:
        """
        获取单个笔记（带并发控制）

        Args:
            session: aiohttp会话
            link: 笔记链接
            index: 当前索引（用于进度显示）
            total: 总数量
        """
        async with self.semaphore:  # 并发控制
            try:
                note_id = self.extract_note_id(link)

                # 策略1: 优先使用note_id
                if note_id:
                    success, result = await self.fetch_with_note_id(session, note_id)
                    if success:
                        return {"link": link, "data": result}

                # 策略2: 尝试share_text
                success, result = await self.fetch_with_share_text(session, link)
                if success:
                    return {"link": link, "data": result}

                # 策略3: 再次尝试note_id
                if note_id:
                    success, result = await self.fetch_with_note_id(session, note_id)
                    if success:
                        return {"link": link, "data": result}

                # 所有策略都失败
                return {
                    "link": link,
                    "data": {
                        "note_id": "获取失败",
                        "title": "获取失败",
                        "content": "获取失败"
                    }
                }

            except Exception as e:
                print(f"处理链接 {link} 时出错: {str(e)}")
                return {
                    "link": link,
                    "data": {
                        "note_id": "系统错误",
                        "title": "系统错误",
                        "content": str(e)
                    }
                }

    async def process_links_async(self, links: List[str]) -> List[List[str]]:
        """
        异步并发处理所有链接

        Args:
            links: 链接列表

        Returns:
            Excel格式的数据列表
        """
        total = len(links)
        print(f"开始异步处理 {total} 个链接...")
        print(f"配置: 速率限制={self.rate_limiter.max_calls}/秒, 并发数={self.semaphore._value}")

        start_time = time.time()

        # 创建HTTP会话
        async with aiohttp.ClientSession() as session:
            # 创建所有任务
            tasks = [
                self.fetch_single_note(session, link, idx, total)
                for idx, link in enumerate(links, 1)
            ]

            # 并发执行所有任务，并显示进度
            results = []
            completed = 0

            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)
                completed += 1

                # 每完成10个或完成全部，输出进度
                if completed % 10 == 0 or completed == total:
                    elapsed = time.time() - start_time
                    progress = (completed / total) * 100
                    rate = completed / elapsed if elapsed > 0 else 0
                    eta = (total - completed) / rate if rate > 0 else 0
                    print(f"进度: {completed}/{total} ({progress:.1f}%) | "
                          f"耗时: {elapsed:.1f}秒 | 速率: {rate:.1f}个/秒 | "
                          f"预计剩余: {eta:.1f}秒")

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
    主函数 - Dify兼容接口（异步版本）

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
        # 创建异步爬虫实例
        scraper = AsyncXHSNoteScraper(
            api_key="apikeyxxx",  # 替换为你的API Key
            max_requests_per_second=5,  # 每秒最多5次请求
            concurrent_limit=10  # 同时处理10个链接
        )

        # 运行异步处理
        excel_data = asyncio.run(scraper.process_links_async(links))

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
    print("异步并发版本测试")
    print("=" * 60)

    result = main(test_links)
    print("\n最终结果:")
    data = json.loads(result["result"])
    print(f"获取到 {len(data)-1} 条笔记")
