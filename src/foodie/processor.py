"""Everything that happens to one photo, start to finish. Blocking code: call it from a worker thread."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from foodie.analyzer import analyze
from foodie.config import Config
from foodie.ledger import Ledger, LedgerBusy, LogRecord
from foodie.photo_store import PhotoStoreError, detect_image_ext, save_photo
from foodie.result_check import AnalysisError, FoodResult, NotLegible

log = logging.getLogger("foodie.processor")

NOT_FOOD_TITLE = "不是食物"

Status = Literal["ok", "unclear", "failed", "ledger_busy", "too_big"]


@dataclass(frozen=True)
class PhotoResult:
    status: Status
    is_food: bool = False
    name: str = ""
    ingredients: tuple[str, ...] = ()
    weight_g: float = 0.0
    calories_kcal: float = 0.0
    daily_total: float | None = None


def process_image(
    cfg: Config,
    ledger: Ledger,
    data: bytes,
    uploader: str,
    uploader_id: str,
    caption: str,
    now: datetime | None = None,
    analyze_fn: Callable[..., FoodResult] = analyze,
) -> PhotoResult:
    """analyze -> check -> save photo -> add Excel row. Never raises: every problem is a status."""
    now = now or datetime.now()

    ext = detect_image_ext(data)
    if ext is None:
        log.warning("不是支援的圖片格式,略過")
        return PhotoResult("failed")

    try:
        result = analyze_fn(cfg, data, ext, caption)
    except NotLegible:
        return PhotoResult("unclear")
    except AnalysisError as exc:
        log.warning("分析失敗:%s", exc)
        return PhotoResult("failed")
    except Exception:
        log.exception("分析時發生意外")
        return PhotoResult("failed")

    if result.is_food:
        title, ingredients = result.name, "、".join(result.ingredients)
        weight, calories = result.weight_g, result.calories_kcal
    else:
        # Not food: the "title" column says so, the "ingredients" column says what it really is,
        # and the numbers are forced to 0 whatever the model guessed.
        title, ingredients = NOT_FOOD_TITLE, result.name
        weight, calories = 0.0, 0.0
    short_name = result.name if result.is_food else NOT_FOOD_TITLE

    try:
        saved = save_photo(cfg.photos_dir, now, short_name, data, ext)
    except (OSError, PhotoStoreError) as exc:
        log.warning("存照片失敗:%s", exc)
        return PhotoResult("failed")

    record = LogRecord(
        when=now,
        uploader=uploader,
        uploader_id=uploader_id,
        title=title,
        ingredients=ingredients,
        weight_g=weight,
        calories_kcal=calories,
        photo_path=str(saved.relative_to(cfg.data_dir)),
    )
    try:
        daily_total = ledger.append(record)
    except LedgerBusy:
        saved.unlink(missing_ok=True)  # no row, so no photo either
        return PhotoResult("ledger_busy")
    except Exception:
        log.exception("寫 Excel 時發生意外")
        saved.unlink(missing_ok=True)
        return PhotoResult("failed")

    return PhotoResult(
        status="ok",
        is_food=result.is_food,
        name=result.name,
        ingredients=result.ingredients,
        weight_g=weight,
        calories_kcal=calories,
        daily_total=daily_total,
    )
