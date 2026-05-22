# 宝宝提醒 · Baby Reminder

每天定时给孕妈发一条贴心消息（关怀 + 胎儿状态 + 今日提醒 + 饮食推荐），通过**企业微信**推送到她的微信。

- ✅ 私人定制，不商业化
- ✅ 零 LLM 依赖，所有内容来自本地内容库（4-42 周 × 5 条）
- ✅ 预产期等敏感信息**全程客户端加密**（浏览器内完成，不上传任何服务器）
- ✅ 完全云端跑，电脑关机也不影响（GitHub Actions cron）
- ✅ 孕妈通过**网页表单**自助填写信息，不需要装任何东西

---

## 整体流程

```
你（部署者）：注册个人企微 + 配 GitHub Secrets + 给她一个网页链接
        ↓
她（孕妈）：打开链接 → 填 3 项 → 下载 profile.enc → 微信发给你
        ↓
你：把 profile.enc 提交到仓库
        ↓
GitHub Actions 每小时跑一次，命中她设的时间就推送到她的微信
```

---

## 第 1 步：注册一个个人企业微信

⚠️ **不要用公司的企业微信**——你拿不到管理员权限，也存在合规风险。注册个人企业微信免费、5 分钟。

1. 浏览器打开 https://work.weixin.qq.com/ → 「立即注册」
2. 选择「企业」（个人也能选这个），公司名随便写如"宝宝提醒小作坊"
3. 用**你的个人微信**扫码作为创建者
4. 选「无需认证」（个人项目用足够，免费）
5. 注册成功后，下载企业微信 App 登录
6. 「通讯录」里**邀请孕妈加入**——她在自己的企业微信里**绑定她的微信号**（设置→消息接收方式→在微信中接收企业微信消息）

## 第 2 步：建一个自建应用，拿到凭证

1. 浏览器登录 https://work.weixin.qq.com/wework_admin/
2. 「应用管理」→ 「自建」→ 「创建应用」→ 名字"宝宝提醒"，可见范围**只勾选孕妈**
3. 创建后在应用详情页记下：**AgentId**、**Secret**（点"查看"扫码获取）
4. 「我的企业」→ 最底部「企业信息」找到 **企业 ID（CorpID）**

至此 4 个凭证：
```
WECOM_CORP_ID    = wwxxxxxxxxxxxxxxxx
WECOM_AGENT_ID   = 1000002
WECOM_SECRET     = AbCdEfGhIjKlMnOp...
WECOM_TOUSER     = @all     ← 因为应用可见范围只有她，@all 即可，不用找 UserID
```

## 第 3 步：生成档案密钥

在你电脑上用任意 Python 跑一行：

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

会输出一段 44 字符的字符串，记下来，比如：
```
xK_3jPkM9aBcDeFg-HiJkLmNoPqRsTuVwXyZ12345678=
```

这就是 `BABY_PROFILE_KEY`。**这一段非常关键，泄露了别人就能解密档案**。

## 第 4 步：把网页发布到 GitHub Pages

1. 在 GitHub 创建一个 **private** 仓库（建议命名 `baby-reminder`）
2. 把整个项目 push 上去
3. 仓库 Settings → Pages → Source 选 `main` 分支 → `/web` 文件夹 → Save
4. 等 1-2 分钟，会得到一个 URL，类似 `https://你的-username.github.io/baby-reminder/`

> ⚠️ 私有仓库要开 Pages 需要 GitHub Pro 账号（$4/月）；
> **如果你不想付费**，可以把 `web/` 文件夹单独放到一个 public 仓库（里面只有 HTML，没有任何敏感信息）。
> 或者用 **Cloudflare Pages**（免费、可绑 private 仓库），把 `web` 子目录托管上去。

## 第 5 步：发链接给孕妈

把刚才生成的 `BABY_PROFILE_KEY` 拼接到 URL 后面作为参数，得到她的专属链接：

```
https://你的-username.github.io/baby-reminder/?k=xK_3jPkM9aBcDeFg-HiJkLmNoPqRsTuVwXyZ12345678=
```

把这个**完整链接**通过微信发给她。她需要做的：

1. 在手机/电脑浏览器打开链接
2. 选择"我知道预产期"或"我只知道孕周"，填写
3. 选择每天想收到消息的时间
4. 输入想被怎么称呼（可选）
5. 点「生成专属配置」→ 点「下载 profile.enc」
6. 把下载的 `profile.enc` 文件用微信发给你

她全程**不用安装任何东西、不用懂任何技术**。所有加密都在她的浏览器本地完成，密钥也是从 URL 参数读的，**没有数据上传到任何服务器**。

## 第 6 步：把 profile.enc 提交到仓库

收到她发来的 `profile.enc` 之后：

```bash
# 把文件放到项目根目录
cp ~/Downloads/profile.enc E:/codebuddy/宝宝提醒/

# 提交
cd E:/codebuddy/宝宝提醒
git add profile.enc
git commit -m "add profile"
git push
```

> 这个文件**已经加密**，提交到 GitHub 是安全的。

## 第 7 步：配 GitHub Secrets

仓库 Settings → Secrets and variables → Actions → New repository secret，依次添加：

| Name | Value |
|---|---|
| `BABY_PROFILE_KEY` | 第 3 步生成的密钥 |
| `WECOM_CORP_ID` | 第 2 步的 CorpID |
| `WECOM_AGENT_ID` | 第 2 步的 AgentId |
| `WECOM_SECRET` | 第 2 步的 Secret |
| `WECOM_TOUSER` | `@all` |

## 第 8 步：手动触发一次验证

- 仓库 Actions 标签 → 找到 "Daily Baby Reminder"
- 点「Run workflow」→ 把 `force` 改为 `true` → 点 Run
- 1 分钟内她的微信应该会收到一条消息～

✨ **完工！之后它会每小时自动检查一次，命中她选的时间就推送。**

---

## 项目结构

```
宝宝提醒/
├── content/messages.json         # 4-42 周 × 5 条内容库
├── src/
│   ├── onboarding.py             # 命令行版 onboarding（备用，本地调试用）
│   ├── profile_store.py          # Fernet 加密档案
│   ├── content_picker.py         # 抽取今日消息
│   └── wecom.py                  # 企微推送
├── web/
│   └── index.html                # 网页表单（GitHub Pages 托管）
├── main.py                       # 每日推送主入口
├── check_time.py                 # 时间网关
├── .github/workflows/daily.yml   # GitHub Actions cron
├── requirements.txt
└── profile.enc                   # 加密档案（孕妈生成、你提交）
```

## 命令行版 onboarding（备用）

如果你自己想本地测试，不想走网页流程，可以用命令行：

```bash
pip install -r requirements.txt
export BABY_PROFILE_KEY="你的密钥"   # Windows PowerShell: $env:BABY_PROFILE_KEY="..."
python -m src.onboarding
```

## 修改预产期/推送时间

让她**重新打开链接填一次**，下载新的 `profile.enc`，你替换仓库里的旧文件并 push 即可。

## 修改内容文案

直接编辑 `content/messages.json`，commit & push。

## 隐私说明

- 网页加密**全部在浏览器本地完成**（用 Web Crypto API），不上传任何服务器
- `profile.enc` 用 Fernet（AES-128-CBC + HMAC-SHA256）对称加密
- 密钥只存在两个地方：你的 GitHub Secrets、URL 参数（链接发完她可以删）
- 即使有人拿到 `profile.enc`，没有密钥也读不出预产期等任何信息

## 常见问题

**Q: 收不到消息？**
A: 让她在企微 App 里检查"消息接收方式"是否开启了"在微信中接收"。Actions 日志看 errcode 是否为 0。

**Q: GitHub Pages 不能托管 private 仓库？**
A: 把 `web/` 单独放一个 public 仓库（里面只有 HTML，零敏感信息），或者用 Cloudflare Pages。

**Q: GitHub Actions cron 不准时？**
A: GitHub 高峰期可能延迟 5-15 分钟，私人用够了。要绝对精确换云函数。

**Q: 想加新功能（如周末特别版/节气问候）？**
A: 改 `src/content_picker.py` 的 `pick_today_message`。
