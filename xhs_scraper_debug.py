import re
import requests
import json
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import threading


class ThreadSafeRateLimiter:
    """线程安全的速率限制器"""

    def __init__(self, max_calls: int = 5, time_window: float = 1.0):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
        self._lock = threading.Lock()

    def wait_if_needed(self):
        with self._lock:
            now = time.time()
            while self.calls and self.calls[0] <= now - self.time_window:
                self.calls.popleft()

            if len(self.calls) >= self.max_calls:
                sleep_time = self.calls[0] + self.time_window - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    now = time.time()
                    while self.calls and self.calls[0] <= now - self.time_window:
                        self.calls.popleft()

            self.calls.append(time.time())


class DebugXHSNoteScraper:
    """
    小红书笔记抓取器 - 调试版本

    特点：
    - 详细的日志输出
    - 打印每个API请求和响应
    - 显示错误详情
    - 帮助诊断问题
    """

    def __init__(self, api_key: str, max_requests_per_second: int = 5, max_workers: int = 10):
        self.api_key = api_key
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

        # 调试信息
        print("\n" + "="*60)
        print("🔍 调试模式启动")
        print("="*60)
        print(f"API Key前缀: {api_key[:10]}***")
        print(f"API Key长度: {len(api_key)}")
        print(f"速率限制: {max_requests_per_second} 次/秒")
        print(f"线程数: {max_workers}")
        print(f"请求超时: {self.timeout}秒")
        print("="*60 + "\n")

    def extract_note_id(self, link: str) -> str:
        """从链接中提取note_id"""
        match = self.pattern.search(link)
        note_id = match.group(1) if match else ""
        print(f"📝 提取note_id: {link[:50]}... → {note_id if note_id else '未提取到'}")
        return note_id

    def _make_request(self, url: str, payload: dict, request_type: str) -> Tuple[bool, dict, str]:
        """
        发起HTTP请求（带详细调试信息）

        Returns:
            (成功标志, 响应数据, 错误信息)
        """
        try:
            print(f"\n🌐 发起请求 [{request_type}]")
            print(f"   URL: {url}")
            print(f"   Payload: {json.dumps(payload, ensure_ascii=False)[:100]}...")

            self.rate_limiter.wait_if_needed()

            start_time = time.time()
            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(payload),
                allow_redirects=True,
                timeout=self.timeout
            )
            elapsed = time.time() - start_time

            print(f"   ⏱️  耗时: {elapsed:.2f}秒")
            print(f"   📊 状态码: {response.status_code}")

            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json()
                    print(f"   ❌ 错误详情: {json.dumps(error_detail, ensure_ascii=False)}")
                    error_msg += f" - {error_detail}"
                except:
                    error_text = response.text[:200]
                    print(f"   ❌ 响应内容: {error_text}")
                    error_msg += f" - {error_text}"

                return False, {}, error_msg

            try:
                data = response.json()
                print(f"   ✅ 响应成功")

                # 打印响应结构（简化）
                if isinstance(data, dict):
                    print(f"   📦 响应字段: {list(data.keys())}")

                return True, data, ""

            except json.JSONDecodeError as e:
                error_msg = f"JSON解析失败: {str(e)}"
                print(f"   ❌ {error_msg}")
                print(f"   原始响应: {response.text[:200]}")
                return False, {}, error_msg

        except requests.exceptions.Timeout:
            error_msg = f"请求超时（{self.timeout}秒）"
            print(f"   ⏰ {error_msg}")
            return False, {}, error_msg

        except requests.exceptions.ConnectionError as e:
            error_msg = f"连接失败: {str(e)[:100]}"
            print(f"   🔌 {error_msg}")
            return False, {}, error_msg

        except Exception as e:
            error_msg = f"未知错误: {str(e)[:100]}"
            print(f"   ❓ {error_msg}")
            return False, {}, error_msg

    def fetch_with_share_text(self, link: str) -> Tuple[bool, Dict, str]:
        """使用share_text方式获取笔记详情"""
        payload = {"share_text": link}
        success, json_data, error = self._make_request(self.url_v3, payload, "share_text")

        if not success:
            return False, {}, error

        data = json_data.get("data", {})
        note_data = data.get("note_data", {})

        if not note_data.get("note_id"):
            error = "响应中没有note_id字段"
            print(f"   ⚠️  {error}")
            print(f"   响应data字段: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            return False, {}, error

        result = {
            "note_id": note_data.get("note_id", ""),
            "title": note_data.get("title", ""),
            "content": note_data.get("desc", "")
        }

        print(f"   ✅ 成功获取: {result.get('title', '')[:30]}...")
        return True, result, ""

    def fetch_with_note_id(self, note_id: str) -> Tuple[bool, Dict, str]:
        """使用note_id方式获取笔记详情"""
        payload = {"note_id": note_id}
        success, json_data, error = self._make_request(self.url_kol, payload, "note_id")

        if not success:
            return False, {}, error

        data = json_data.get("data", {}).get("data", {})

        if not data.get("noteId"):
            error = "响应中没有noteId字段"
            print(f"   ⚠️  {error}")
            return False, {}, error

        result = {
            "note_id": data.get("noteId", ""),
            "title": data.get("title", ""),
            "content": data.get("content", "")
        }

        print(f"   ✅ 成功获取: {result.get('title', '')[:30]}...")
        return True, result, ""

    def fetch_single_note(self, link: str, index: int, total: int) -> Dict:
        """获取单个笔记"""
        print(f"\n{'='*60}")
        print(f"📌 处理链接 {index}/{total}")
        print(f"   {link[:80]}...")
        print(f"{'='*60}")

        try:
            note_id = self.extract_note_id(link)

            errors = []

            # 策略1: 优先使用note_id
            if note_id:
                print(f"\n🎯 策略1: 使用note_id接口")
                success, result, error = self.fetch_with_note_id(note_id)
                if success:
                    return {"link": link, "data": result, "index": index}
                errors.append(f"note_id接口: {error}")

            # 策略2: 尝试share_text
            print(f"\n🎯 策略2: 使用share_text接口")
            success, result, error = self.fetch_with_share_text(link)
            if success:
                return {"link": link, "data": result, "index": index}
            errors.append(f"share_text接口: {error}")

            # 策略3: 再次尝试note_id
            if note_id:
                print(f"\n🎯 策略3: 重试note_id接口")
                success, result, error = self.fetch_with_note_id(note_id)
                if success:
                    return {"link": link, "data": result, "index": index}
                errors.append(f"note_id重试: {error}")

            # 所有策略都失败
            all_errors = " | ".join(errors)
            print(f"\n❌ 所有策略都失败")
            print(f"   错误汇总: {all_errors}")

            return {
                "link": link,
                "data": {
                    "note_id": "获取失败",
                    "title": "获取失败",
                    "content": f"所有API调用都失败: {all_errors}"
                },
                "index": index
            }

        except Exception as e:
            error_msg = f"系统错误: {str(e)}"
            print(f"\n💥 {error_msg}")
            import traceback
            traceback.print_exc()

            return {
                "link": link,
                "data": {
                    "note_id": "系统错误",
                    "title": "系统错误",
                    "content": error_msg
                },
                "index": index
            }

    def process_links_concurrent(self, links: List[str]) -> List[List[str]]:
        """多线程并发处理所有链接"""
        total = len(links)
        print(f"\n{'='*60}")
        print(f"🚀 开始处理 {total} 个链接")
        print(f"{'='*60}\n")

        start_time = time.time()
        results = []
        completed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_link = {
                executor.submit(self.fetch_single_note, link, idx, total): link
                for idx, link in enumerate(links, 1)
            }

            for future in as_completed(future_to_link):
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1

                    if completed % 5 == 0 or completed == total:
                        elapsed = time.time() - start_time
                        progress = (completed / total) * 100
                        print(f"\n{'='*60}")
                        print(f"📊 进度: {completed}/{total} ({progress:.1f}%)")
                        print(f"⏱️  已耗时: {elapsed:.1f}秒")
                        print(f"{'='*60}")

                except Exception as e:
                    print(f"\n❌ 处理任务时出错: {str(e)}")
                    completed += 1

        results.sort(key=lambda x: x.get("index", 0))

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

        print(f"\n{'='*60}")
        print(f"✅ 处理完成！")
        print(f"{'='*60}")
        print(f"总耗时: {elapsed_time:.2f}秒")
        print(f"平均速率: {total/elapsed_time:.2f}个/秒")
        print(f"成功/总数: {sum(1 for r in results if r['data'].get('note_id') not in ['获取失败', '系统错误'])}/{total}")
        print(f"{'='*60}\n")

        return excel_data


def main(links):
    """
    主函数 - 调试版本
    """
    if not isinstance(links, list):
        links = [links] if links else []

    if not links:
        return {"result": "请输入链接"}

    links = list(dict.fromkeys(links))
    links = [link.strip() for link in links if link and link.strip()]

    if not links:
        return {"result": "没有有效的链接"}

    try:
        # ⚠️ 重要：替换为你的真实API Key
        api_key = "apikeyxxx"

        if api_key == "apikeyxxx":
            print("\n" + "="*60)
            print("⚠️  警告：API Key未设置！")
            print("="*60)
            print("请将代码中的 'apikeyxxx' 替换为你的真实API Key")
            print("API Key应该类似: sk-xxxxxxxxxxxxxxx")
            print("="*60 + "\n")

        scraper = DebugXHSNoteScraper(
            api_key=api_key,
            max_requests_per_second=5,
            max_workers=10
        )

        excel_data = scraper.process_links_concurrent(links)

        return {"result": json.dumps(excel_data, ensure_ascii=False)}

    except Exception as e:
        error_msg = f"处理出错: {str(e)}"
        print(f"\n💥 {error_msg}")
        import traceback
        traceback.print_exc()
        return {"result": error_msg}


if __name__ == "__main__":
    test_links = [
        "https://www.xiaohongshu.com/explore/68119b4700000000210192b0?xsec_token=MBDh3mkBIsI6TBUajevzWBcXjoD4LCpC-EBQ4RKVlUAyo=&xsec_source=pc_pgyexport",
    ]

    result = main(test_links)
    print("\n最终结果:")
    print(result)
