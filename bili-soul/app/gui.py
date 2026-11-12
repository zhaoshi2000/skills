"""Desktop controls for observing and running BiliSoul."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import queue
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext, ttk

from bili_soul import db
from bili_soul.control import RunController
from main import extract_bvid, run


class QueueLogHandler(logging.Handler):
    def __init__(self, events: queue.Queue):
        super().__init__()
        self.events = events

    def emit(self, record):
        self.events.put(("log", record.getMessage()))


class BiliSoulWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.events: queue.Queue = queue.Queue()
        self.worker: threading.Thread | None = None
        self.controller: RunController | None = None
        self.closing = False
        self.paused = False
        self.started_at: float | None = None
        self.video_url = tk.StringVar()
        self.status_text = tk.StringVar(value="就绪")
        self.step_text = tk.StringVar(value="等待启动")
        self.video_text = tk.StringVar(value="尚未选择视频")
        self.elapsed_text = tk.StringVar(value="00:00")
        self.count_text = tk.StringVar(value="已分析 0 条视频 · 待审核 0 条草稿")

        self.root.title("BiliSoul · 视频观察")
        self.root.geometry("1080x760")
        self.root.minsize(820, 600)
        self.root.configure(bg="#f5f7fb")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._build_style()
        self._build_ui()

        self.log_handler = QueueLogHandler(self.events)
        logging.getLogger().addHandler(self.log_handler)
        self.refresh_results()
        self.root.after(100, self._drain_events)
        self.root.after(1000, self._tick)

    def _build_style(self):
        style = ttk.Style(self.root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("TFrame", background="#f5f7fb")
        style.configure("TLabel", background="#f5f7fb", foreground="#172033",
                        font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 22),
                        foreground="#1b365d")
        style.configure("Muted.TLabel", foreground="#627087", font=("Segoe UI", 9))
        style.configure("Section.TLabel", font=("Segoe UI Semibold", 11))
        style.configure("TButton", font=("Segoe UI", 10), padding=(14, 7))
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9))

    def _build_ui(self):
        shell = ttk.Frame(self.root, padding=18)
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(3, weight=1)

        header = ttk.Frame(shell)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        ttk.Label(header, text="BiliSoul", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="观察 B 站视频、字幕、评论与待审核草稿",
                  style="Muted.TLabel").pack(anchor="w", pady=(2, 0))

        controls = ttk.Frame(shell)
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        controls.columnconfigure(0, weight=1)
        ttk.Label(controls, text="视频链接或 BV 号（留空则读取首页推荐）").grid(
            row=0, column=0, columnspan=5, sticky="w", pady=(0, 5))
        self.url_entry = ttk.Entry(controls, textvariable=self.video_url)
        self.url_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.start_button = ttk.Button(controls, text="启动", command=self.start)
        self.start_button.grid(row=1, column=1, padx=(0, 6))
        self.pause_button = ttk.Button(controls, text="暂停", command=self.toggle_pause,
                                       state="disabled")
        self.pause_button.grid(row=1, column=2, padx=(0, 6))
        self.stop_button = ttk.Button(controls, text="停止任务", command=self.stop,
                                      state="disabled")
        self.stop_button.grid(row=1, column=3, padx=(0, 6))
        ttk.Button(controls, text="关闭窗口", command=self.close).grid(row=1, column=4)
        ttk.Label(controls, text="暂停和停止会在当前网络、下载或转录步骤结束后生效。",
                  style="Muted.TLabel").grid(row=2, column=0, columnspan=5,
                                               sticky="w", pady=(7, 0))

        progress = ttk.Frame(shell)
        progress.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        progress.columnconfigure(1, weight=1)
        ttk.Label(progress, text="状态", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.state_label = tk.Label(progress, textvariable=self.status_text, bg="#e5f2eb",
                                    fg="#17623c", font=("Segoe UI Semibold", 10),
                                    padx=10, pady=3)
        self.state_label.grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Label(progress, textvariable=self.elapsed_text, style="Muted.TLabel").grid(
            row=0, column=2, sticky="e")
        ttk.Label(progress, text="当前视频", style="Muted.TLabel").grid(
            row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Label(progress, textvariable=self.video_text).grid(
            row=1, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=(8, 0))
        ttk.Label(progress, text="当前步骤", style="Muted.TLabel").grid(
            row=2, column=0, sticky="w", pady=(4, 0))
        ttk.Label(progress, textvariable=self.step_text).grid(
            row=2, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=(4, 0))
        ttk.Label(progress, textvariable=self.count_text, style="Muted.TLabel").grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))

        content = ttk.Panedwindow(shell, orient="vertical")
        content.grid(row=3, column=0, sticky="nsew")

        results = ttk.Frame(content)
        results.columnconfigure(0, weight=2)
        results.columnconfigure(1, weight=3)
        results.rowconfigure(1, weight=1)
        ttk.Label(results, text="已完成的视频", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Label(results, text="分析与评论草稿", style="Section.TLabel").grid(
            row=0, column=1, sticky="w", padx=(10, 0), pady=(0, 6))
        self.video_list = ttk.Treeview(results, columns=("score",), show="tree headings",
                                       selectmode="browse")
        self.video_list.heading("#0", text="视频")
        self.video_list.heading("score", text="兴趣")
        self.video_list.column("#0", width=310, minwidth=190)
        self.video_list.column("score", width=58, minwidth=50, anchor="center")
        self.video_list.grid(row=1, column=0, sticky="nsew")
        self.video_list.bind("<<TreeviewSelect>>", self._show_selected)
        self.detail = scrolledtext.ScrolledText(results, wrap="word", state="disabled",
                                                font=("Microsoft YaHei UI", 10),
                                                bg="#ffffff", fg="#172033",
                                                relief="flat", padx=12, pady=10)
        self.detail.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        content.add(results, weight=3)

        logs = ttk.Frame(content)
        logs.columnconfigure(0, weight=1)
        logs.rowconfigure(1, weight=1)
        ttk.Label(logs, text="运行日志", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", pady=(7, 6))
        self.log_box = scrolledtext.ScrolledText(logs, wrap="word", state="disabled",
                                                 font=("Consolas", 9), bg="#132033",
                                                 fg="#e5eefb", insertbackground="#ffffff",
                                                 relief="flat", padx=10, pady=8)
        self.log_box.grid(row=1, column=0, sticky="nsew")
        content.add(logs, weight=2)

    def _set_status(self, text: str, kind: str = "ready"):
        palette = {
            "ready": ("#e5f2eb", "#17623c"),
            "running": ("#e4efff", "#17559b"),
            "paused": ("#fff1d6", "#8b5700"),
            "stopping": ("#fde8e7", "#a8322b"),
            "error": ("#fde8e7", "#a8322b"),
        }
        bg, fg = palette.get(kind, palette["ready"])
        self.status_text.set(text)
        self.state_label.configure(bg=bg, fg=fg)

    def _append_log(self, text: str):
        stamp = time.strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{stamp}  {text}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _on_controller_event(self, event: dict):
        self.events.put(("progress", event))

    def start(self):
        if self.worker and self.worker.is_alive():
            return
        value = self.video_url.get().strip()
        if value:
            try:
                extract_bvid(value)
            except ValueError as exc:
                self._set_status("输入无效", "error")
                self._append_log(str(exc))
                return
        self.controller = RunController(on_event=self._on_controller_event)
        self.paused = False
        self.closing = False
        self.started_at = time.monotonic()
        self._set_status("运行中", "running")
        self.step_text.set("正在启动")
        self.video_text.set(value or "首页推荐")
        self.start_button.configure(state="disabled")
        self.pause_button.configure(state="normal", text="暂停")
        self.stop_button.configure(state="normal")
        self.url_entry.configure(state="disabled")
        self._append_log("任务已启动")
        self.worker = threading.Thread(target=self._run_worker, args=(value or None,),
                                       daemon=True, name="BiliSoulWorker")
        self.worker.start()

    def _run_worker(self, video_url: str | None):
        try:
            asyncio.run(run(video_url, controller=self.controller))
        except Exception as exc:
            if self.controller and self.controller.state == "stopped":
                self.events.put(("done", "已停止"))
            else:
                self.events.put(("error", f"{type(exc).__name__}: {exc}"))
        else:
            self.events.put(("done", "已停止" if self.controller and
                             self.controller.state == "stopped" else "已完成"))

    def toggle_pause(self):
        if not self.controller or not self.worker or not self.worker.is_alive():
            return
        if self.paused:
            self.controller.resume()
            self.paused = False
            self.pause_button.configure(text="暂停")
            self._set_status("运行中", "running")
            self._append_log("已继续")
        else:
            self.controller.pause()
            self.paused = True
            self.pause_button.configure(text="继续")
            self._set_status("等待暂停", "paused")
            self._append_log("已请求暂停，将在当前步骤结束后生效")

    def stop(self):
        if not self.controller or not self.worker or not self.worker.is_alive():
            return
        self.controller.stop()
        self.pause_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")
        self._set_status("正在停止", "stopping")
        self._append_log("已请求停止，将在当前步骤结束后生效")

    def close(self):
        if self.worker and self.worker.is_alive():
            self.closing = True
            self.stop()
            self._set_status("正在关闭", "stopping")
            return
        self._destroy()

    def _destroy(self):
        logging.getLogger().removeHandler(self.log_handler)
        self.root.destroy()

    def _drain_events(self):
        for _ in range(100):
            try:
                kind, payload = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "log":
                self._append_log(payload)
                if payload.startswith("[记录]"):
                    self.refresh_results()
            elif kind == "progress":
                self._handle_progress(payload)
            elif kind == "error":
                self._append_log(payload)
                self._finish("运行失败", "error")
            elif kind == "done":
                self._finish(payload, "ready")
        if self.root.winfo_exists():
            self.root.after(100, self._drain_events)

    def _handle_progress(self, event: dict):
        stage = event.get("stage")
        detail = event.get("detail")
        title = event.get("title")
        if stage:
            self.step_text.set(f"{stage}：{detail}" if detail else stage)
        if title:
            self.video_text.set(title)
        state = event.get("state")
        if state == "paused":
            self._set_status("已暂停", "paused")
        elif state == "stopping":
            self._set_status("正在停止", "stopping")
        elif state == "running" and not self.paused:
            self._set_status("运行中", "running")
        if event.get("type") == "analysis" or stage == "记录":
            self.refresh_results()

    def _finish(self, text: str, kind: str):
        self._set_status(text, kind)
        self.step_text.set(text)
        self.pause_button.configure(state="disabled", text="暂停")
        self.stop_button.configure(state="disabled")
        self.start_button.configure(state="normal")
        self.url_entry.configure(state="normal")
        self.paused = False
        self.refresh_results()
        self._append_log(text)
        if self.closing:
            self._destroy()

    def _tick(self):
        if self.started_at and self.worker and self.worker.is_alive():
            seconds = int(time.monotonic() - self.started_at)
            self.elapsed_text.set(f"{seconds // 60:02}:{seconds % 60:02}")
        if self.root.winfo_exists():
            self.root.after(1000, self._tick)

    def refresh_results(self):
        try:
            connection = db.connect()
            rows = connection.execute(
                "SELECT bvid,title,analysis,comments_json,score FROM videos "
                "ORDER BY created_at DESC, rowid DESC"
            ).fetchall()
            draft_count = connection.execute(
                "SELECT COUNT(1) FROM drafts WHERE status='pending'"
            ).fetchone()[0]
            connection.close()
        except Exception as exc:
            self._append_log(f"读取结果失败：{exc}")
            return
        selected = self.video_list.selection()
        selected_id = selected[0] if selected else None
        self.rows = {row["bvid"]: row for row in rows}
        existing = self.video_list.get_children()
        if existing:
            self.video_list.delete(*existing)
        for row in rows:
            title = row["title"] or row["bvid"]
            short = title[:32] + ("…" if len(title) > 32 else "")
            self.video_list.insert("", "end", iid=row["bvid"], text=short,
                                   values=(f"{row['score']:.2f}",))
        self.count_text.set(f"已分析 {len(rows)} 条视频 · 待审核 {draft_count} 条草稿")
        if selected_id in self.rows:
            self.video_list.selection_set(selected_id)
        elif rows:
            self.video_list.selection_set(rows[0]["bvid"])
        self._show_selected()

    def _show_selected(self, _event=None):
        selected = self.video_list.selection()
        row = self.rows.get(selected[0]) if selected else None
        if not row:
            content = "完成分析后，这里会显示内容概括、评论视角和待审核草稿。"
        else:
            try:
                result = json.loads(row["analysis"] or "{}")
                sample = json.loads(row["comments_json"] or "{}")
            except json.JSONDecodeError:
                result, sample = {}, {}
            points = "\n".join(f"  • {value}" for value in result.get("key_points", []))
            content = (
                f"{row['title']}\n{row['bvid']}\n\n"
                f"内容概括\n{result.get('summary', '')}\n\n"
                f"主要内容\n{points}\n\n"
                f"评论视角（样本 {sample.get('count', 0)} 条）\n"
                f"{result.get('comment_perspective', '')}\n\n"
                f"证据判断\n{result.get('evidence_assessment', '')}\n\n"
                f"局限与不确定性\n{result.get('uncertainty', '')}\n\n"
                f"待审核评论草稿\n{result.get('draft_comment', '')}"
            )
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", content)
        self.detail.yview_moveto(0)
        self.detail.configure(state="disabled")


def main():
    root = tk.Tk()
    BiliSoulWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
