"""Thread-safe cooperative controls for one BiliSoul run."""

from __future__ import annotations

from threading import Condition
from typing import Callable


class RunStopped(Exception):
    """Raised at a checkpoint after the user requests a stop."""


class RunController:
    """Pause or stop a worker at the next checkpoint, and publish UI events.

    The callback runs on the worker thread. A GUI must enqueue its events and
    update widgets on the GUI thread.
    """

    def __init__(self, on_event: Callable[[dict], None] | None = None):
        self._condition = Condition()
        self._state = "idle"
        self._stage = "待命"
        self._detail = ""
        self._on_event = on_event

    @property
    def state(self) -> str:
        with self._condition:
            return self._state

    def _event(self, event_type: str, **fields) -> dict:
        with self._condition:
            event = {
                "type": event_type,
                "state": self._state,
                "stage": self._stage,
                "detail": self._detail,
            }
        event.update(fields)
        return event

    def _publish(self, event_type: str, **fields) -> None:
        if self._on_event is not None:
            self._on_event(self._event(event_type, **fields))

    def start(self) -> None:
        with self._condition:
            if self._state in {"stopping", "stopped"}:
                raise RunStopped()
            if self._state != "idle":
                raise RuntimeError("本次运行已经启动")
            self._state = "running"
            self._stage = "启动"
            self._detail = "任务已启动"
        self._publish("status")

    def pause(self) -> None:
        with self._condition:
            if self._state != "running":
                return
            self._state = "pausing"
        self._publish("status", detail="已请求暂停，将在当前步骤结束后暂停")

    def resume(self) -> None:
        with self._condition:
            if self._state not in {"pausing", "paused"}:
                return
            self._state = "running"
            self._condition.notify_all()
        self._publish("status", detail="已继续运行")

    def stop(self) -> None:
        with self._condition:
            if self._state not in {"idle", "running", "pausing", "paused"}:
                return
            self._state = "stopping"
            self._condition.notify_all()
        self._publish("status", detail="已请求停止，将在当前步骤结束后退出")

    def checkpoint(self, stage: str, detail: str = "", **fields) -> None:
        paused_event = None
        with self._condition:
            if self._state == "pausing":
                self._state = "paused"
                paused_event = {
                    "type": "status", "state": "paused",
                    "stage": self._stage,
                    "detail": f"已暂停；下一步：{stage}",
                }
        if paused_event is not None and self._on_event is not None:
            self._on_event(paused_event)
        with self._condition:
            while self._state == "paused":
                self._condition.wait()
            if self._state in {"stopping", "stopped"}:
                raise RunStopped()
            if self._state != "running":
                raise RuntimeError(f"运行状态不允许继续：{self._state}")
            self._stage = stage
            self._detail = detail
        self._publish("progress", **fields)

    def emit(self, event_type: str, **fields) -> None:
        self._publish(event_type, **fields)

    def stopped(self) -> None:
        with self._condition:
            self._state = "stopped"
            self._stage = "停止"
            self._detail = "任务已停止"
            self._condition.notify_all()
        self._publish("status")

    def complete(self) -> None:
        with self._condition:
            if self._state == "stopping":
                self._state = "stopped"
                self._stage = "停止"
                self._detail = "任务已停止"
            else:
                self._state = "completed"
                self._stage = "完成"
                self._detail = "本次运行完成"
            self._condition.notify_all()
        self._publish("status")

    def fail(self, detail: str) -> None:
        with self._condition:
            self._state = "failed"
            self._stage = "错误"
            self._detail = detail
            self._condition.notify_all()
        self._publish("status")
