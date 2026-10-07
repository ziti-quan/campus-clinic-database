# -*- coding: utf-8 -*-
"""一键截取三个前端的所有验证页面。

用法：双击同目录下的「一键截图.bat」，或执行
        python auto_shoot.py
脚本会自动完成：
   1) 检查 5000/5001/5002 三个服务，未启动则自动拉起（结束后自动关闭自己拉起的进程）
   2) 用 Edge 无头模式 + CDP 自动登录、切换视图
   3) 把每个画面截图保存到 ../截图/网页截图/

依赖：requests、websocket-client（Anaconda 自带；否则 pip install requests websocket-client）
"""

import base64
import json
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    import requests
    import websocket
except ImportError as exc:
    raise SystemExit(
        "缺少依赖：%s\n请先执行：pip install requests websocket-client" % exc.name)

PROJ = Path(__file__).resolve().parent.parent
OUT = PROJ / "截图" / "网页截图"
DEBUG_PORT = 9222
W, H = 1600, 1000

P, D, A = "http://127.0.0.1:5000", "http://127.0.0.1:5001", "http://127.0.0.1:5002"

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

_PROCS = []          # 需要在本脚本退出时清理的子进程


def port_open(port):
    with socket.socket() as s:
        s.settimeout(1.0)
        return s.connect_ex(("127.0.0.1", port)) == 0


def start_app(mod, port):
    code = ("import sys; sys.path.insert(0, r'%s'); import %s as m; "
            "m.app.run(host='127.0.0.1', port=%d, debug=False, use_reloader=False)"
            % (PROJ, mod, port))
    proc = subprocess.Popen([sys.executable, "-c", code], cwd=str(PROJ))
    _PROCS.append(proc)
    return proc


class Page:
    """浏览器级 CDP 会话（flatten 模式）。"""

    def __init__(self, ws, session):
        self.ws = ws
        self.session = session
        self.seq = 0

    def cmd(self, method, **params):
        self.seq += 1
        mid = self.seq
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params,
                                 "sessionId": self.session}))
        while True:
            try:
                raw = self.ws.recv()
            except Exception as exc:
                raise RuntimeError(
                    "与浏览器的调试通道断开（%s）。常见原因：安全软件/沙箱拦截了 Edge、"
                    "Edge 版本过旧、或 --headless=new 不被支持（可改成 --headless 重试）。"
                    % type(exc).__name__) from exc
            msg = json.loads(raw)
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError("%s -> %s" % (method, msg["error"]))
                return msg.get("result", {})

    def js(self, expression):
        return self.cmd("Runtime.evaluate", expression=expression,
                        returnByValue=True)["result"].get("value")

    def goto(self, url, settle=1.0):
        self.cmd("Page.navigate", url=url)
        for _ in range(120):
            time.sleep(0.15)
            try:
                if self.js("document.readyState") == "complete":
                    break
            except Exception:
                pass
        time.sleep(settle)

    def cookie(self, value):
        self.cmd("Network.setCookie", name="session", value=value,
                 domain="127.0.0.1", path="/")

    def shot(self, name, full=True):
        params = {"format": "png"}
        if full:
            m = self.cmd("Page.getLayoutMetrics")["cssContentSize"]
            params["clip"] = {"x": 0, "y": 0, "width": m["width"],
                              "height": max(m["height"], H), "scale": 1}
            params["captureBeyondViewport"] = True
        data = self.cmd("Page.captureScreenshot", **params)["data"]
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / (name + ".png")
        path.write_bytes(base64.b64decode(data))
        print("  已保存 %-42s %6d KB" % (path.name, path.stat().st_size // 1024))


def login_cookie(base, path, data):
    s = requests.Session()
    r = s.post(base + path, data=data, timeout=15, allow_redirects=False)
    if r.status_code != 302:
        raise SystemExit("登录失败（%s）：请确认数据库已导入 seed_data.sql" % r.status_code)
    return s.cookies.get("session")


def main():
    launched = []
    for mod, port in (("app", 5000), ("app_D", 5001), ("admin", 5002)):
        if not port_open(port):
            print("端口 %d 未监听，自动启动 %s.py ..." % (port, mod))
            launched.append(start_app(mod, port))
    for _ in range(40):
        if all(port_open(p) for p in (5000, 5001, 5002)):
            break
        time.sleep(0.5)
    else:
        raise SystemExit("三个服务未能启动，请检查依赖是否安装（requirements.txt）")
    print("三个服务已就绪")

    edge = next((p for p in EDGE_CANDIDATES if Path(p).exists()), None)
    if not edge:
        raise SystemExit("未找到 Microsoft Edge，请修改脚本中的 EDGE_CANDIDATES")

    patient = login_cookie(P, "/login", {"phone": "13800138000", "password": "123456"})
    doctor = login_cookie(D, "/doctor_login", {"name": "张伟", "password": "123456"})
    visit = requests.get(P + "/api/my_registrations",
                         cookies={"session": patient}, timeout=10).json()[0]["visit_date"]
    print("演示就诊日期 =", visit)

    profile = Path(__file__).resolve().parent / "_edge_profile"
    if profile.exists():
        shutil.rmtree(profile, ignore_errors=True)
    print("启动 Edge（无头）...")
    proc = subprocess.Popen([
        edge, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
        "--hide-scrollbars", "--remote-allow-origins=*",
        "--remote-debugging-port=%d" % DEBUG_PORT,
        "--user-data-dir=%s" % profile,
        "--window-size=%d,%d" % (W, H), "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _PROCS.append(proc)

    ws_url = None
    for _ in range(60):
        time.sleep(0.5)
        try:
            info = json.loads(urllib.request.urlopen(
                "http://127.0.0.1:%d/json/version" % DEBUG_PORT, timeout=3).read())
            ws_url = info["webSocketDebuggerUrl"]
            break
        except Exception:
            pass
    if not ws_url:
        raise SystemExit("无法连接 Edge 调试端口")

    def browser_cmd(mid, method, **params):
        ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            m = json.loads(ws.recv())
            if m.get("id") == mid:
                return m["result"]

    ws = websocket.create_connection(ws_url, timeout=60)
    tid = browser_cmd(1, "Target.createTarget", url="about:blank")["targetId"]
    sid = browser_cmd(2, "Target.attachToTarget", targetId=tid, flatten=True)["sessionId"]

    page = Page(ws, sid)
    page.cmd("Page.enable")
    page.cmd("Network.enable")
    page.cmd("Runtime.enable")
    page.cmd("Emulation.setDeviceMetricsOverride", width=W, height=H,
             deviceScaleFactor=1, mobile=False)

    print("\n[患者端]")
    page.goto(P + "/login")
    page.shot("01_患者端_登录页")
    page.cookie(patient)
    page.goto(P + "/")
    page.js("showDeptSelection()")
    time.sleep(0.6)
    page.shot("02_患者端_首页与科室选择")
    page.js("loadSchedules('内科', '%s')" % visit)
    time.sleep(1.2)
    page.shot("03_患者端_按科室日期查号源")
    page.js("showMyRegistrations()")
    time.sleep(1.2)
    page.shot("04_患者端_我的挂号记录")
    page.js("showMedicalRecords()")
    time.sleep(1.2)
    page.shot("05_患者端_我的病历")
    page.js("showPrescriptions()")
    time.sleep(1.2)
    page.shot("06_患者端_我的药单")

    print("\n[医生端]")
    page.goto(D + "/doctor_login")
    page.shot("07_医生端_登录页")
    page.cookie(doctor)
    page.goto(D + "/doctor_dashboard")
    page.js("document.getElementById('showSchedulesBtn').click()")
    time.sleep(0.5)
    page.js("(() => { const b = document.querySelectorAll('.date-btn')[0];"
            " b.dataset.date = '%s'; b.textContent = '%s'; b.click(); })()" % (visit, visit))
    time.sleep(1.2)
    page.shot("08_医生端_当日就诊患者")
    page.js("document.getElementById('showMedicinesBtn').click()")
    time.sleep(1.2)
    page.shot("09_医生端_药品库存")
    page.js("document.getElementById('showMyScheduleBtn').click()")
    time.sleep(1.2)
    page.shot("10_医生端_我的排班")
    page.js("document.getElementById('showAllPatientsBtn').click()")
    time.sleep(1.2)
    page.shot("11_医生端_全部患者")
    page.goto(D + "/patient_record/1?date=" + visit)
    page.shot("12_医生端_病历查看与编辑")
    pr = requests.get(D + "/api/prescribe/patients",
                      cookies={"session": doctor}, timeout=10).json()
    if pr:
        rid = pr[0]["registration_id"]
        page.goto(D + "/prescribe_medicine?registration_id=%d" % rid)
        page.js("(() => { const s = document.getElementById('medicineSelect');"
                " s.value = s.options[1].value;"
                " document.getElementById('medicineQuantity').value = 2;"
                " document.getElementById('addMedicineBtn').click(); })()")
        time.sleep(1.0)
        page.shot("13_医生端_开处方（含历史处方）")

    print("\n[管理端]")
    page.goto(A + "/")
    page.shot("14_管理端_科室管理")
    for tab, name in [("doctor", "15_管理端_医生管理"),
                      ("medicine", "16_管理端_药品管理"),
                      ("schedule", "17_管理端_排班管理")]:
        page.js("document.querySelector('.tab-btn[data-tab=\"%s\"]').click()" % tab)
        time.sleep(1.2)
        page.shot(name)

    report = PROJ / "数据库验证报告.html"
    if report.exists():
        print("\n[数据库验证报告]")
        page.goto(report.resolve().as_uri())
        time.sleep(1.0)
        page.shot("18_数据库验证报告_表结构与关联")
        page.js("window.scrollTo(0, document.body.scrollHeight * 0.45)")
        time.sleep(0.6)
        page.shot("19_数据库验证报告_范式与约束", full=False)
        page.js("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(0.6)
        page.shot("20_数据库验证报告_约束与并发", full=False)

    proc.terminate()
    for p in launched:
        p.terminate()
    print("\n全部完成，截图目录：%s" % OUT)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:                     # noqa: BLE001
        print("\n[失败] %s" % exc)
        print("排查建议：")
        print("  1) 先在浏览器里手动打开 http://127.0.0.1:5000 ，确认能正常显示页面")
        print("  2) 若提示缺少模块：pip install requests websocket-client")
        print("  3) 若 Edge 启动失败：编辑本文件顶部的 EDGE_CANDIDATES 指向本机 msedge.exe")
        print("  4) 若报调试通道断开：把启动参数里的 --headless=new 换成 --headless 再试")
        sys.exit(1)
    finally:
        for p in _PROCS:
            try:
                p.terminate()
            except Exception:
                pass
