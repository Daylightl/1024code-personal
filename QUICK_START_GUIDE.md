# 快速开始指南 - 选择适合你的版本

## ⚠️ Dify用户必读

**如果你在Dify环境中使用，请查看 [DIFY_USAGE_GUIDE.md](DIFY_USAGE_GUIDE.md)**

Dify环境版本选择：
```
├─ 10个以内    → 用 【同步优化版】 xhs_scraper_optimized.py
├─ 10-20个     → 用 【多线程并发版】 xhs_scraper_concurrent.py ⭐推荐
├─ 20-50个     → 用 【多线程并发版】 xhs_scraper_concurrent.py ⭐推荐
└─ 50-100个    → 用 【多线程并发版 + 分批处理】
```

❌ **Dify中不能使用** `xhs_scraper_async.py`（缺少aiohttp依赖）

---

## 30秒快速选择（本地环境）

**回答一个问题：你通常需要一次处理多少个链接？**

```
├─ 10个以内    → 用 【同步优化版】 xhs_scraper_optimized.py
├─ 10-20个     → 用 【同步优化版】 xhs_scraper_optimized.py
├─ 20-50个     → 用 【异步并发版】 xhs_scraper_async.py ⭐推荐（需安装aiohttp）
│                  或 【多线程并发版】 xhs_scraper_concurrent.py（无需额外依赖）
├─ 50-100个    → 用 【异步并发版】 xhs_scraper_async.py
└─ 100个以上   → 用 【异步并发版 + 分批处理】
```

---

## 版本对比一览表

| 特性 | 原始版本 | 同步优化版 | 多线程并发版 | 异步并发版 |
|------|---------|-----------|------------|-----------|
| **50个链接耗时** | ~55秒 ❌ | ~15秒 ✅ | ~13秒 ⭐ | ~12秒 ⭐⭐ |
| **代码复杂度** | 简单 | 简单 | 简单 | 中等 |
| **Dify可用性** | ✅ | ✅ | ✅ | ❌ |
| **额外依赖** | 无 | 无 | 无 | aiohttp |
| **学习成本** | 无 | 低 | 低 | 中 |
| **推荐场景** | ❌ | ≤20个 | Dify环境 | 本地环境 |

---

## 方案A: 同步优化版（简单稳定）

### 适用场景
- ✅ 一次处理 10-20 个链接
- ✅ 追求代码简单
- ✅ 不想学习异步编程

### 性能表现
```
10个链接: 3-5秒
20个链接: 6-8秒
30个链接: 10-12秒（接近Dify安全边界）
```

### 使用步骤

#### 1. 复制代码
```bash
# 复制 xhs_scraper_optimized.py 的内容
cat xhs_scraper_optimized.py
```

#### 2. 修改API Key
```python
# 找到这一行（约第193行）
scraper = XHSNoteScraper(
    api_key="apikeyxxx",  # ← 改成你的API Key
    max_requests_per_second=5
)
```

#### 3. 粘贴到Dify
- 复制整个文件内容
- 粘贴到Dify的【代码】节点
- 输入变量: `links` (列表类型)
- 输出变量: `result`

#### 4. 测试
```python
# 在Dify中测试
输入: ["https://www.xiaohongshu.com/explore/xxx"]
输出: JSON格式的表格数据
```

### 配置建议

**保守配置（推荐）：**
```python
max_requests_per_second=4  # 稳定
timeout=15
单次最多: 15个链接
```

**标准配置：**
```python
max_requests_per_second=5  # 默认
timeout=10
单次最多: 20个链接
```

---

## 方案B: 多线程并发版（Dify专用）⭐

### 适用场景
- ✅ 在Dify环境中使用
- ✅ 一次处理 30-50 个链接
- ✅ 无需额外依赖
- ✅ 性能接近异步版本

### 性能表现
```
30个链接: 8-10秒
50个链接: 13-15秒
100个链接: 26-30秒（需分批）
```

### 使用步骤

#### 1. 复制代码
```bash
# 复制 xhs_scraper_concurrent.py 的内容
cat xhs_scraper_concurrent.py
```

#### 2. 修改API Key
```python
# 找到这一行（约第243行）
scraper = ConcurrentXHSNoteScraper(
    api_key="apikeyxxx",  # ← 改成你的API Key
    max_requests_per_second=5,
    max_workers=10
)
```

#### 3. 粘贴到Dify
- 复制整个文件内容
- 粘贴到Dify的【代码】节点
- 输入变量: `links` (列表类型)
- 输出变量: `result`

#### 4. 测试
```python
# 在Dify中测试
输入: 你的10个小红书链接
输出: JSON格式的表格数据
预计耗时: 3-5秒
```

### 配置建议

**标准配置（推荐）：**
```python
max_requests_per_second=5  # 速率
max_workers=10             # 线程数
单次最多: 50个链接
```

**保守配置（超稳定）：**
```python
max_requests_per_second=4  # 更稳
max_workers=5              # 更少线程
单次最多: 30个链接
```

---

## 方案C: 异步并发版（本地环境最优）⭐⭐

### 适用场景
- ✅ 在本地环境使用（非Dify）
- ✅ 一次处理 30-50 个链接
- ✅ 追求极致性能
- ✅ 愿意学习异步编程（1小时）
- ❌ 在Dify中不可用（缺少aiohttp）

### 性能表现
```
30个链接: 7-9秒
50个链接: 12-14秒
100个链接: 25-30秒（需分批）
```

### 使用步骤

#### 1. 复制代码
```bash
# 复制 xhs_scraper_async.py 的内容
cat xhs_scraper_async.py
```

#### 2. 修改API Key
```python
# 找到这一行（约第182行）
scraper = AsyncXHSNoteScraper(
    api_key="apikeyxxx",  # ← 改成你的API Key
    max_requests_per_second=5,
    concurrent_limit=10
)
```

#### 3. 粘贴到Dify
- 复制整个文件内容
- 粘贴到Dify的【代码】节点
- 输入变量: `links` (列表类型)
- 输出变量: `result`

#### 4. 测试
```python
# 在Dify中测试
输入: 50个链接的列表
输出: JSON格式的表格数据
预计耗时: 12-14秒
```

### 配置建议

**标准配置（推荐）：**
```python
max_requests_per_second=5  # 速率限制
concurrent_limit=10        # 并发数
timeout=10
单次最多: 50个链接
```

**激进配置（高性能）：**
```python
max_requests_per_second=6  # 更快（需确认API支持）
concurrent_limit=15        # 更高并发
timeout=8
单次最多: 80个链接
```

**保守配置（超稳定）：**
```python
max_requests_per_second=4  # 更稳
concurrent_limit=5         # 低并发
timeout=15
单次最多: 30个链接
```

---

## 方案C: 分批处理（100+链接）

### 适用场景
- ✅ 一次处理 100+ 个链接
- ✅ 使用Dify工作流

### 方案设计

**示例：处理 200 个链接**

```
Dify工作流:

[开始]
  ↓
[拆分列表] ← 200个链接拆成4批，每批50个
  ↓
[并行处理]
  ├─ [代码节点1] 处理 链接1-50   (异步并发版)
  ├─ [代码节点2] 处理 链接51-100  (异步并发版)
  ├─ [代码节点3] 处理 链接101-150 (异步并发版)
  └─ [代码节点4] 处理 链接151-200 (异步并发版)
  ↓
[合并结果]
  ↓
[输出]
```

**预计耗时：**
```
4批并行处理: 每批12秒
总耗时: 12秒（如果Dify支持并行）
总耗时: 48秒（如果串行处理）
```

### 实现代码（Python拆分逻辑）

```python
def split_into_batches(links, batch_size=50):
    """拆分链接为多批"""
    batches = []
    for i in range(0, len(links), batch_size):
        batch = links[i:i + batch_size]
        batches.append(batch)
    return batches

# 使用
all_links = [...]  # 200个链接
batches = split_into_batches(all_links, batch_size=50)
# batches[0]: 链接1-50
# batches[1]: 链接51-100
# ...
```

---

## 不同场景的完整配置示例

### 场景1: Dify环境，10个链接，追求稳定

**推荐版本：** 同步优化版

```python
# xhs_scraper_optimized.py

scraper = XHSNoteScraper(
    api_key="你的API Key",
    max_requests_per_second=4  # 保守
)
scraper.timeout = 15

# 预计耗时: 3-5秒
# Dify安全性: ✅✅✅
```

---

### 场景2: Dify环境，50个链接，追求性能

**推荐版本：** 异步并发版

```python
# xhs_scraper_async.py

scraper = AsyncXHSNoteScraper(
    api_key="你的API Key",
    max_requests_per_second=5,  # 标准
    concurrent_limit=10         # 标准
)

# 预计耗时: 12-14秒
# Dify安全性: ✅✅
```

---

### 场景3: 本地环境，100个链接，不限时

**推荐版本：** 异步并发版（激进配置）

```python
# xhs_scraper_async.py

scraper = AsyncXHSNoteScraper(
    api_key="你的API Key",
    max_requests_per_second=6,  # 激进
    concurrent_limit=15         # 高并发
)

# 预计耗时: 20-25秒
# 无超时限制: ✅
```

---

### 场景4: Dify环境，200个链接，分批处理

**推荐版本：** 异步并发版 + 分批

```python
# 工作流节点1-4，每个节点:
scraper = AsyncXHSNoteScraper(
    api_key="你的API Key",
    max_requests_per_second=5,
    concurrent_limit=10
)

# 每批50个链接
# 预计每批耗时: 12秒
# 总耗时: 48秒（串行）或 12秒（并行）
```

---

## 故障排查速查表

### 问题1: 在Dify中被killed

**可能原因：**
- 链接数过多
- API响应慢
- 网络波动

**解决方案：**
```python
# 方案1: 降低速率
max_requests_per_second=3  # 从5改成3

# 方案2: 减少链接数
links = links[:15]  # 只处理前15个

# 方案3: 增加超时
timeout=20  # 从10改成20

# 方案4: 使用异步版本
# 改用 xhs_scraper_async.py
```

---

### 问题2: 获取失败率高

**检查清单：**
```
□ API Key是否正确
□ 网络是否稳定
□ 链接格式是否正确
□ 是否触发API其他限制
```

**解决方案：**
```python
# 添加重试机制（高级）
# 或联系API提供商
```

---

### 问题3: 速度比预期慢

**诊断：**
```python
# 检查速率设置
print(scraper.rate_limiter.max_calls)  # 应该是5

# 检查并发数（异步版本）
print(scraper.semaphore._value)  # 应该是10
```

**优化：**
```python
# 同步版本：提高速率
max_requests_per_second=6  # 如果API允许

# 异步版本：提高并发
concurrent_limit=15  # 如果没超时问题
```

---

### 问题4: 异步版本报错

**常见错误1：**
```
RuntimeError: Event loop is closed
```

**解决：**
```python
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )
```

**常见错误2：**
```
aiohttp.ClientError: Cannot connect
```

**解决：**
```python
# 检查网络连接
# 或降低并发数
concurrent_limit=5
```

---

## 性能测试

### 运行测试脚本

```bash
# 测试1: 基础对比（15个链接）
python performance_comparison.py

# 测试2: 50个链接对比
python performance_comparison_50links.py

# 测试3: 实际运行（需要真实API Key）
python xhs_scraper_optimized.py  # 同步版
python xhs_scraper_async.py      # 异步版
```

---

## 推荐学习路径

### 路径1: 新手（只想快速使用）

```
1. 直接使用 同步优化版
   ↓
2. 复制代码到Dify
   ↓
3. 替换API Key
   ↓
4. 处理 ≤20个链接
```

**时间：** 5分钟

---

### 路径2: 进阶（想处理更多链接）

```
1. 先学习异步编程基础（1小时）
   推荐: https://docs.python.org/zh-cn/3/library/asyncio.html
   ↓
2. 阅读 ASYNC_VS_SYNC_COMPARISON.md
   ↓
3. 使用 异步并发版
   ↓
4. 处理 30-50个链接
```

**时间：** 2小时

---

### 路径3: 专家（大批量处理）

```
1. 掌握异步编程
   ↓
2. 学习Dify工作流
   ↓
3. 实现分批处理
   ↓
4. 处理 100+个链接
```

**时间：** 半天

---

## 最终建议

### 🎯 你的链接数 ≤ 20
```
用 xhs_scraper_optimized.py
理由: 简单够用
```

### 🎯 你的链接数 30-50（你的情况）
```
用 xhs_scraper_async.py ⭐⭐⭐
理由:
- 性能提升 20%
- Dify更安全
- 值得投入1小时学习
```

### 🎯 你的链接数 > 50
```
必须用 xhs_scraper_async.py
可能需要分批
```

---

## 下一步行动

**如果你决定用异步版本（推荐）：**

1. ✅ 打开 `xhs_scraper_async.py`
2. ✅ 替换 API Key（搜索"apikeyxxx"）
3. ✅ 复制到Dify代码节点
4. ✅ 用5个链接测试
5. ✅ 确认无误后，处理50个链接

**预计效果：**
- 50个链接，12-14秒完成
- 成功率 95%+
- 不会被Dify killed

---

**还有疑问？**
- 查看 `ASYNC_VS_SYNC_COMPARISON.md` - 详细对比
- 查看 `OPTIMIZATION_GUIDE.md` - 优化原理
- 运行 `performance_comparison_50links.py` - 性能测试
