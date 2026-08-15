#!/usr/bin/env python3
"""H2O 清醒度体温计 · 极简计算内核 API（v1 草案 / 阶段0 交付）

设计纪律（杨植麟"去雕花" + 段永平"不为清单"）：
- 纯函数、零状态、零外部调用：只做 预估/实际 → 失控系数R → 4级体温 → 刺痛文案。
- 一个计算内核，多端分发：微信小程序(兜底入口) / 微信 Agent Skill / WorkBuddy Skill 共用本 API。
- 不在此文件做渠道分发（Skill 外壳属 1.0 不为清单），只预留标准 HTTP 接口。

接口契约（以 H2O-极简API与Skill规范.md 为准）：
  POST /api/thermometer
   入参: {"estimated_min":int, "actual_min":int, "scene_tag":str?}
   出参: {"R":float|null, "deviation_pct":int|null, "level":str, "level_name":str,
          "clarity_pct":int|null, "card_text":str, "scene_tag":str,
          "warning":str?}   # est<=0 时返回，提示补填预估；R/deviation_pct/clarity_pct 为 null
  GET  /health -> {"status":"ok"}

三处必修红线：
  ① 除零保护（修订）：estimated_min <= 0 不静默当 1、也不拒入；归特殊 L0「无意识失控期」并提示补填——"无预估即失控"恰是最该记录的场景。
  ② 36.5/37.8/39.0/40.5℃ 仅为设计示例值，非临床阈值（本接口不出体温数字，只出"体温定级"隐喻）。
  ③ 术语统一：对外称「失控系数 R」，不混用"水分率"。

部署适配说明（对算法内核零污染）：
  - 入口处优先读取 PaaS 注入的 PORT 环境变量（Zeabur / Railway / Render / Heroku 标准）。
  - compute_thermometer() 与 CARDS 文案表完全不动，本文件仅入口与 import 适配。
  - 使用 ThreadingHTTPServer 提供基础并发，纯计算无状态，安全无害。
"""
import json
import http.server
import sys
import os  # 部署适配：读取 PORT / HOST 环境变量


# ============ 计算内核 ============
def compute_thermometer(estimated_min, actual_min, scene_tag='general'):
    """纯函数：预估/实际 -> 失控系数 R -> 体温定级 + 刺痛文案。
    返回 (result_dict, error_str)。error 非空表示入参非法。"""
    if estimated_min is None or actual_min is None:
        return None, '请先填写预估时间和实际时间。'
    if estimated_min <= 0:
        # 红线①（修订）：预估 0/空 = 无意识失控，最该记录，绝不拒入。
        # 无法算 R（除零），归特殊 L0「无意识失控期」并提示补填预估。
        resolved_scene = scene_tag if scene_tag in CARDS else 'general'
        return {
            'R': None,
            'deviation_pct': None,
            'level': 'L0',
            'level_name': '无意识失控期',
            'clarity_pct': None,
            'card_text': '你连预估都没设，就已经失控了——这正是无意识让渡的典型。补填一个预估时长，让数据替你照见偏差。',
            'scene_tag': resolved_scene,
            'warning': 'estimated_min 为 0 或空：失控系数无法计算，本次记为「无意识失控期」。请补填预估以生成精确体温。',
        }, None
    if actual_min <= 0:
        return None, '请填写实际花费的时间（大于 0）。'

    R = (actual_min - estimated_min) / estimated_min
    deviation_pct = round(R * 100)

    # 分档 L0-L3（4级"体温状态"）
    if R <= 0:
        level, level_name = 'L0', '清醒（无失控）'
    elif R <= 1:
        level, level_name = 'L1', '轻度失控'
    elif R <= 2:
        level, level_name = 'L2', '中度失控'
    else:
        level, level_name = 'L3', '重度失控'

    # 反推正向前值（与小程序 v1 同源）：清醒度 = 100×est/actual = 100/(1+R)
    clarity_pct = round(100 * estimated_min / actual_min)
    clarity_pct = max(0, min(100, clarity_pct))

    resolved_scene = scene_tag if scene_tag in CARDS else 'general'
    card_text = pick_card(resolved_scene, level)

    return {
        'R': round(R, 3),
        'deviation_pct': deviation_pct,
        'level': level,
        'level_name': level_name,
        'clarity_pct': clarity_pct,
        'card_text': card_text,
        'scene_tag': resolved_scene,
    }, None


# ============ 16 套硬编码刺痛文案（4 场景 × 4 级）============
# 风格：刺痛却本分（"数据不会撒谎，把手重新放到方向盘上"），零 API 零延迟不幻觉。
# 待任务#100 评审微调；此处为可用种子版。
CARDS = {
    'short_video': {  # 刷短剧 / 娱乐失控
        'L0': '刷得比预估还少？这半小时你拿回去了，记住这种收手的感觉。',
        'L1': '多刷了一倍时间。手指停下的那一刻，下次可以再早五分钟。',
        'L2': '三倍时间没了。不是剧好看，是你没给手指一个停的理由。',
        'L3': '五倍。屏幕关掉后那点空虚，就是失控的实价。明天定个硬截止。',
    },
    'work_delay': {  # 加班 / 工作拖延
        'L0': '收工比预估早，今天这活你控住了。明天的排期可以再狠一点。',
        'L1': '多花一倍。卡住的那一步，写下来，明天开工先捅它。',
        'L2': '三倍工时。不是活多，是中间切出去太多次。下次开干前先关通知。',
        'L3': '五倍。你不是在加班，是在为白天的犹豫买单。流程该重捋了。',
    },
    'impulse_buy': {  # 冲动消费
        'L0': '比预估还省，这单你清醒。记账留个痕，强化这种手感。',
        'L1': '多花一倍。下单前那三秒，本来可以救你一半钱。',
        'L2': '三倍支出。冲动不是性格，是没给钱包设一道闸。下回加购物车晾一夜。',
        'L3': '五倍。钱花出去不回头，但这次的疼能当你下次的刹车。',
    },
    'general': {  # 通用 / 精力透支
        'L0': '实际没超预估，这桩事你做主了。保持。',
        'L1': '超了一倍。偏差不大，但别习惯。复盘一下哪步松了。',
        'L2': '两倍失控。你的精力被这事吃掉了三份，值得吗？重排优先级。',
        'L3': '失控五倍。你不是在做事，是事在拖你。先停，再想清楚要不要做。',
    },
}

def pick_card(scene_tag, level):
    scene = CARDS.get(scene_tag, CARDS['general'])
    return scene.get(level, CARDS['general'][level])


# ============ HTTP 服务 ============
class Handler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self._send_json({'status': 'ok'})
        else:
            self._send_json({'error': 'not found'}, 404)

    def do_POST(self):
        if self.path != '/api/thermometer':
            self._send_json({'error': 'not found'}, 404)
            return
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length) if length > 0 else b'{}'
        try:
            body = json.loads(raw.decode('utf-8'))
        except Exception:
            self._send_json({'error': 'invalid json'}, 400)
            return

        est = body.get('estimated_min')
        act = body.get('actual_min')
        scene = body.get('scene_tag', 'general') or 'general'

        # 容错：前端可能传字符串
        try:
            est = float(est) if est is not None else None
            act = float(act) if act is not None else None
        except Exception:
            est, act = None, None

        result, err = compute_thermometer(est, act, scene)
        if err:
            self._send_json({'ok': False, 'error': err}, 200)
        else:
            self._send_json({'ok': True, **result})

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    # 部署适配：优先读 PaaS 注入的 PORT 环境变量（Zeabur/Railway/Render/Heroku 标准）。
    # 本地不传 PORT 时回退到命令行参数或默认 8866。算法内核零改动。
    port = int(os.environ.get('PORT', sys.argv[1] if len(sys.argv) > 1 else 8866))
    host = os.environ.get('HOST', '0.0.0.0')
    print(f'H2O 清醒度体温计 API: http://{host}:{port}/api/thermometer')
    http.server.ThreadingHTTPServer((host, port), Handler).serve_forever()
