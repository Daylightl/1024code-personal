# API调用失败诊断指南

## 🔍 问题分析

你的输出显示：**所有10个链接都返回"获取失败"**

```json
["链接", "获取失败", "获取失败", "获取失败"]
```

这种情况下，通常是以下原因之一：

---

## ✅ 诊断清单

### 1. 检查API Key是否正确配置 ⭐⭐⭐（最可能）

**问题：** 代码中的API Key可能还是默认值 `"apikeyxxx"`

**检查方法：**
```python
# 在代码中搜索这一行（约第243行）
scraper = ConcurrentXHSNoteScraper(
    api_key="apikeyxxx",  # ← 这里应该是你的真实API Key
    ...
)
```

**解决方法：**
```python
# 改成你从 moreapi.cn 获取的真实API Key
scraper = ConcurrentXHSNoteScraper(
    api_key="sk-xxxxxxxxxxxxxxxxxxxxx",  # ← 替换成真实的
    max_requests_per_second=5,
    max_workers=10
)
```

---

### 2. 检查API Key是否有效

**验证方法：**

使用curl命令测试（在终端运行）：
```bash
curl -X POST http://api.moreapi.cn/api/xhs/note_detail_v3 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 你的API_Key" \
  -d '{"share_text": "https://www.xiaohongshu.com/explore/68119b4700000000210192b0"}'
```

**预期结果：**
- ✅ 如果返回JSON数据 → API Key有效
- ❌ 如果返回401/403错误 → API Key无效或过期

---

### 3. 检查API接口是否可访问

**问题：** API服务可能暂时不可用

**测试方法：**
```bash
# 测试API是否能访问
curl http://api.moreapi.cn/api/xhs/note_detail_v3
```

---

### 4. 检查网络连接

**问题：** Dify环境可能无法访问外网API

**可能原因：**
- Dify部署环境有网络限制
- 需要配置代理
- API域名被墙

---

### 5. 检查API响应格式是否改变

**问题：** API提供商可能更新了接口

---

## 🛠️ 调试版本代码

我创建了一个带详细日志的调试版本，帮你看到具体的错误信息：

### 调试版本特点

✅ 打印详细的API请求信息
✅ 显示API响应状态码
✅ 输出完整的错误信息
✅ 记录每个步骤的执行情况

### 使用方法

1. 复制下面的调试版本代码
2. 替换你在Dify中的代码
3. 再次运行，查看详细日志
4. 根据日志找出问题原因

---

## 💊 快速修复步骤

### 步骤1: 确认API Key

```python
# 1. 登录 https://api.moreapi.cn
# 2. 查看你的API Key
# 3. 复制完整的Key（类似 sk-xxxxxx 格式）
# 4. 替换代码中的 "apikeyxxx"
```

### 步骤2: 使用调试版本

见下一个文件：`xhs_scraper_debug.py`

### 步骤3: 查看日志输出

运行调试版本后，你会看到类似这样的输出：
```
=== 调试信息 ===
API Key前缀: sk-***
请求URL: http://api.moreapi.cn/api/xhs/note_detail_v3
响应状态码: 401
响应内容: {"error": "Invalid API key"}
===
```

### 步骤4: 根据日志修复

常见错误及解决方案：

| 错误信息 | 原因 | 解决方法 |
|---------|------|---------|
| `Invalid API key` | API Key错误 | 检查并替换正确的Key |
| `API key expired` | API Key过期 | 重新获取新的Key |
| `Rate limit exceeded` | 请求过快 | 降低速率或等待 |
| `Connection timeout` | 网络问题 | 检查网络连接 |
| `404 Not Found` | 接口地址错误 | 联系API提供商 |

---

## 📊 故障排查流程图

```
开始
  ↓
检查API Key是否替换？
  ├─ 否 → 替换为真实API Key → 重新运行
  └─ 是 → 继续
       ↓
  使用调试版本查看详细错误
       ↓
  根据错误信息修复：
       ↓
  ├─ 401/403 → API Key问题 → 重新获取Key
  ├─ 429 → 速率限制 → 降低请求频率
  ├─ 500 → API服务问题 → 联系服务商
  └─ 网络超时 → 网络问题 → 检查网络/代理
```

---

## 🔧 常见问题及解决方案

### Q1: 我确定API Key是对的，但还是失败

**可能原因：**
1. API Key格式问题（有多余空格）
2. API账户余额不足
3. API有其他限制（IP白名单等）

**解决方法：**
```python
# 确保Key前后没有空格
api_key = "sk-xxxxx".strip()

# 检查API账户余额
# 登录 API 提供商网站查看
```

---

### Q2: 在本地运行成功，在Dify中失败

**可能原因：**
- Dify环境网络限制
- Dify环境没有配置代理

**解决方法：**
1. 检查Dify环境是否能访问外网
2. 配置HTTP代理（如需要）
3. 联系Dify管理员

---

### Q3: 部分链接成功，部分失败

**这是正常的！** 可能原因：
- 某些笔记已删除
- 某些笔记设置了隐私
- 链接格式不正确

**解决方法：**
- 检查失败的链接是否能在浏览器中打开
- 过滤掉失败的链接

---

## 📝 下一步

1. **立即检查：** API Key是否正确替换
2. **使用调试版本：** 查看 `xhs_scraper_debug.py`
3. **查看日志：** 找出具体错误原因
4. **修复问题：** 根据错误信息修复

---

## 💡 提示

如果你看到详细的错误日志，可以把日志内容发给我，我会帮你分析具体原因！

**常见的错误日志格式：**
```
请求失败: HTTP 401 - {"error": "Invalid API key"}
请求失败: HTTP 429 - {"error": "Rate limit exceeded"}
请求失败: Connection timeout after 10s
```
