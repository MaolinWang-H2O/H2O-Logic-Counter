# H₂O 清醒度体温计 API

> **H2O Clarity Thermometer Protocol** —— 一个用于量化「时间失控 / 逻辑浓度（Logic Concentration）」的开放标准计算协议。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 一句话定位

输入「你**预估**做某事花多久」和「你**实际**花多久」，输出一个**失控系数 R** + **4 级体温定级** + 一句**刺痛却本分的提醒**。

纯 Python 标准库、零依赖、零状态、零外部调用——一个文件即可运行，可被任何 Agent / MCP 插件 / GPTs / 后端直接调用。

---

## 从产品到协议（Protocol over Product）

这不是一个普通的小工具 API，而是一套可复用的**计算标准**：

- 当有人想量化「失控系数 R」或测算「信息卡路里 / 逻辑浓度」时，这里提供**最干净、最标准的开源实现**；
- 带有 MIT License、完整接口说明与数学公式，可在全球开发者社区抢占定义权；
- 一个稳定的 Live HTTPS 端点，让逻辑内核像水一样渗进各种海外智能体与工具里。

**两条轨，物理隔离：**

| 轨道 | 载体 | 角色 |
|---|---|---|
| 国内轨 | 微信小程序 + 微信云函数（#102） | 直面国内用户的商业产品，护城河锁在云端 |
| 海外轨 | 本仓库（GitHub）+ 海外 Serverless | 向全球开发者输出的算法标准与品牌名片 |

---

## 失控系数 R 公式

```
R = (actual_min − estimated_min) / estimated_min
```

分档（4 级「体温状态」）：

| 级别 | 条件 | 命名 |
|---|---|---|
| L0 | R ≤ 0 | 清醒（实际 ≤ 预估，无失控） |
| L1 | 0 < R ≤ 1 | 轻度失控（偏差 ≤ 100%） |
| L2 | 1 < R ≤ 2 | 中度失控（偏差 ≤ 200%） |
| L3 | R > 2 | 重度失控（偏差 > 200%） |

清醒度：`clarity_pct = 100 × min(estimated, actual) / actual`（与 R 同源）。

> ⚠️ 设计稿中的 36.5 / 37.8 / 39.0 / 40.5℃ 仅为**设计示例值，非临床阈值**。本接口只出「体温定级」隐喻，不出医学结论。

---

## 快速开始（本地）

```bash
# 需 Python 3.8+
python h2o-thermometer-api.py
# 或指定端口：python h2o-thermometer-api.py 8866

# 调用
curl -X POST http://localhost:8866/api/thermometer \
  -H "Content-Type: application/json" \
  -d '{"estimated_min": 30, "actual_min": 180, "scene_tag": "short_video"}'

# 健康检查
curl http://localhost:8866/health
```

出参示例：

```json
{
  "ok": true,
  "R": 5.0,
  "deviation_pct": 500,
  "level": "L3",
  "level_name": "重度失控",
  "clarity_pct": 17,
  "card_text": "五倍。屏幕关掉后那点空虚，就是失控的实价。明天定个硬截止。",
  "scene_tag": "short_video"
}
```

**16 套刺痛文案**：4 场景（short_video / work_delay / impulse_buy / general）× 4 级（L0–L3），硬编码在 `CARDS` 表中，零 API、零延迟、不幻觉。

---

## 一键部署（海外 Serverless）

本仓库自带零配置部署文件，关联 GitHub 后自动构建：

| 平台 | 方式 | 说明 |
|---|---|---|
| **Zeabur** | New Project → Deploy from GitHub → 选本仓库 | 港台团队，亚洲节点，国内可直连，无需备案 |
| **Railway** | `railway up` 或 Dashboard 导入仓库 | 自动检测 Python，Always-on，DX 最佳 |
| **Render** | 导入仓库，自动识别 `render.yaml` | 免费层（15 分钟休眠），`/health` 健康检查 |
| **Docker Hub** | `docker build -t h2o-thermometer . && docker run -p 8080:8080 h2o-thermometer` | 见 `Dockerfile` |

部署平台会注入 `PORT` 环境变量（代码已适配），无需任何改动。

---

## Live API 端点

> 🔗 **部署后填入此处的真实地址**（替换下方占位）：
>
> `https://h2o-clarity-thermometer.zeabur.app/api/thermometer`

任何支持 OpenAPI 的平台（RapidAPI / Postman / 各类 Agent 框架）可直接导入本仓库的
[`openapi.yaml`](openapi.yaml) 生成客户端。

---

## 文件结构

```
h2o-thermometer-api/
├── h2o-thermometer-api.py   # 计算内核 + HTTP 服务（算法零依赖标准库）
├── Procfile                 # Heroku / Zeabur 启动命令
├── render.yaml              # Render 一键部署
├── Dockerfile               # 容器化分发（Docker Hub）
├── requirements.txt         # 零第三方依赖声明
├── openapi.yaml             # OpenAPI 3.0 规范（RapidAPI / Postman 导入）
├── LICENSE                  # MIT
└── README.md                # 本文件
```

---

## License

[MIT](LICENSE) © 2026 H2O Clarity Thermometer / 茂林操盘
