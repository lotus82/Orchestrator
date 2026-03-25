"""
AI pipeline: OpenCV + Ultralytics YOLOv8, детекция мяча (COCO class 32),
пересечение ROI ворот, антидребезг событий «гол».
Опционально — запись отладочного видео с ROI и bbox мяча.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Callable

import cv2
from ultralytics import YOLO

logger = logging.getLogger(__name__)

# COCO: sports ball
SPORTS_BALL_CLASS_ID = 32

# ROI ворот (x1, y1, x2, y2) в пикселях — подстройте под ваше видео / разрешение.
DEFAULT_GOAL_ROI = (650, 500, 737, 540)


def _point_in_roi(cx: float, cy: float, roi: tuple[int, int, int, int]) -> bool:
    x1, y1, x2, y2 = roi
    return x1 <= cx <= x2 and y1 <= cy <= y2


def _best_ball_box(result) -> tuple[float, float, float, float, float] | None:
    """
    Из результата YOLO возвращает (cx, cy, x1, y1, x2, y2) для класса «мяч» с максимальной уверенностью.
    """
    if result.boxes is None or len(result.boxes) == 0:
        return None
    best_conf = -1.0
    best = None
    for box in result.boxes:
        cls_id = int(box.cls[0].item())
        if cls_id != SPORTS_BALL_CLASS_ID:
            continue
        conf = float(box.conf[0].item())
        if conf <= best_conf:
            continue
        xyxy = box.xyxy[0].cpu().numpy()
        x1, y1, x2, y2 = float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        best = (cx, cy, x1, y1, x2, y2)
        best_conf = conf
    return best


def run_goal_detection_pipeline(
    video_path: Path,
    *,
    roi: tuple[int, int, int, int] = DEFAULT_GOAL_ROI,
    target_process_fps: float = 5.0,
    goal_debounce_sec: float = 2.5,
    model_name: str = "yolov8n.pt",
    debug_mode: bool = False,
    debug_output_path: Path | None = None,
    progress_callback: Callable[[int, float], None] | None = None,
    timecodes_output_path: Path | None = None,
) -> list[float]:
    """
    Обрабатывает видео, возвращает список timestamp_sec (от начала ролика) для событий «goal».

    Логика:
    - читаем кадры, обрабатываем ~target_process_fps кадров в секунду;
    - ищем мяч (класс 32), центр bbox;
    - переход «снаружи ROI -> внутри» при отсутствии события в последние goal_debounce_sec секунд.
    """
    path = Path(video_path)
    if not path.is_file():
        raise FileNotFoundError(f"Видео не найдено: {path}")

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Не удалось открыть видео: {path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_step = max(1, int(round(video_fps / target_process_fps)))

    logger.info(
        "Видео fps=%.2f, шаг кадров=%d (~%.1f обраб/сек), ROI=%s",
        video_fps,
        frame_step,
        video_fps / frame_step,
        roi,
    )

    model = YOLO(model_name)

    writer: cv2.VideoWriter | None = None
    if debug_mode and debug_output_path:
        debug_output_path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out_fps = min(target_process_fps, video_fps)
        writer = cv2.VideoWriter(
            str(debug_output_path),
            fourcc,
            out_fps,
            (width, height),
        )
        if not writer.isOpened():
            logger.warning("Не удалось открыть VideoWriter для %s", debug_output_path)
            writer = None

    goal_timestamps: list[float] = []
    prev_inside = False
    last_goal_time = -1e9
    frame_index = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            if frame_index % frame_step != 0:
                frame_index += 1
                continue

            t_sec = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            if t_sec < 0:
                t_sec = frame_index / video_fps

            results = model.predict(frame, verbose=False, classes=[SPORTS_BALL_CLASS_ID])
            ball = _best_ball_box(results[0]) if results else None

            inside = False
            if ball is not None:
                cx, cy, bx1, by1, bx2, by2 = ball
                inside = _point_in_roi(cx, cy, roi)

                if inside and not prev_inside:
                    if t_sec - last_goal_time >= goal_debounce_sec:
                        goal_timestamps.append(float(t_sec))
                        last_goal_time = t_sec
                        logger.info("Событие goal @ %.3f с", t_sec)

                prev_inside = inside

                if writer is not None:
                    vis = frame.copy()
                    cv2.rectangle(vis, (roi[0], roi[1]), (roi[2], roi[3]), (0, 255, 0), 2)
                    cv2.rectangle(
                        vis,
                        (int(bx1), int(by1)),
                        (int(bx2), int(by2)),
                        (0, 165, 255),
                        2,
                    )
                    cv2.putText(
                        vis,
                        f"t={t_sec:.2f}s",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (255, 255, 255),
                        2,
                    )
                    writer.write(vis)
            else:
                prev_inside = False
                if writer is not None:
                    vis = frame.copy()
                    cv2.rectangle(vis, (roi[0], roi[1]), (roi[2], roi[3]), (0, 255, 0), 2)
                    cv2.putText(
                        vis,
                        "no ball",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (255, 255, 255),
                        2,
                    )
                    writer.write(vis)

            if progress_callback and frame_index % (frame_step * 30) == 0:
                progress_callback(frame_index, t_sec)

            frame_index += 1
    finally:
        cap.release()
        if writer is not None:
            writer.release()

    if timecodes_output_path is not None:
        try:
            import json
            timecodes_output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(timecodes_output_path, "w", encoding="utf-8") as f:
                json.dump({"goal_timestamps": goal_timestamps}, f, indent=4)
            logger.info("Таймкоды голов сохранены в %s", timecodes_output_path)
        except Exception as e:
            logger.error("Ошибка при сохранении таймкодов: %s", e)

    return goal_timestamps


def resolve_debug_path() -> Path:
    return Path(os.environ.get("YOLO_DEBUG_OUTPUT", "./debug_output.mp4"))


def resolve_debug_mode() -> bool:
    return os.environ.get("YOLO_DEBUG_MODE", "").lower() in ("1", "true", "yes")
