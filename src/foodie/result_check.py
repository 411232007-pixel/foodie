"""Parse and check what `claude -p` sends back. Nothing here may crash the program:
every problem becomes an AnalysisError that the caller turns into a failure reply."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass

MAX_NAME_CHARS = 50
MAX_INGREDIENTS = 15
MAX_INGREDIENT_CHARS = 30
MAX_WEIGHT_G = 5000
MAX_CALORIES_KCAL = 5000

_NUMERIC_TEXT = re.compile(r"[0-9]+(\.[0-9]+)?")


class AnalysisError(Exception):
    """The analysis could not produce a usable result."""


class NotLegible(AnalysisError):
    """The photo is too blurry or dark to judge."""


@dataclass(frozen=True)
class FoodResult:
    is_food: bool
    legible: bool
    name: str
    ingredients: tuple[str, ...]
    weight_g: float
    calories_kcal: float


def parse_claude_stdout(stdout: str) -> FoodResult:
    """`claude -p --output-format json` wraps the answer in an outer JSON envelope."""
    try:
        outer = json.loads(stdout)
    except ValueError as exc:
        raise AnalysisError("claude 的輸出不是合法 JSON") from exc
    if not isinstance(outer, dict):
        raise AnalysisError("claude 的輸出格式不對")
    if outer.get("is_error"):
        raise AnalysisError(f"claude 回報錯誤:{outer.get('subtype') or outer.get('result')}")

    inner = outer.get("structured_output")
    if not isinstance(inner, dict):
        inner = extract_json_object(outer.get("result"))
    return validate_result(inner)


def extract_json_object(text: object) -> dict:
    """Pull the outermost {...} out of free text (models sometimes add ``` fences or a sentence)."""
    if not isinstance(text, str):
        raise AnalysisError("claude 沒有回答")
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise AnalysisError("回答裡找不到 JSON")
    try:
        obj = json.loads(text[start : end + 1])
    except ValueError as exc:
        raise AnalysisError("回答不是合法 JSON") from exc
    if not isinstance(obj, dict):
        raise AnalysisError("回答的 JSON 不是物件")
    return obj


def validate_result(obj: dict) -> FoodResult:
    name = _clean_text(obj.get("name"), "name", MAX_NAME_CHARS)
    if not name:
        raise AnalysisError("name 是空的")

    raw_ingredients = obj.get("ingredients")
    if not isinstance(raw_ingredients, list):
        raise AnalysisError("ingredients 不是清單")
    ingredients = []
    for item in raw_ingredients[:MAX_INGREDIENTS]:
        text = _clean_text(item, "ingredients 的項目", MAX_INGREDIENT_CHARS)
        if text:
            ingredients.append(text)

    return FoodResult(
        is_food=_boolean(obj, "is_food"),
        legible=_boolean(obj, "legible"),
        name=name,
        ingredients=tuple(ingredients),
        weight_g=_number(obj, "weight_g", MAX_WEIGHT_G),
        calories_kcal=_number(obj, "calories_kcal", MAX_CALORIES_KCAL),
    )


def _boolean(obj: dict, key: str) -> bool:
    value = obj.get(key)
    if not isinstance(value, bool):
        raise AnalysisError(f"{key} 不是 true/false")
    return value


def _number(obj: dict, key: str, upper: float) -> float:
    value = obj.get(key)
    if isinstance(value, bool):
        raise AnalysisError(f"{key} 不是數字")
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str) and _NUMERIC_TEXT.fullmatch(value.strip()):
        number = float(value.strip())
    else:
        raise AnalysisError(f"{key} 不是數字")
    if not math.isfinite(number) or number < 0 or number > upper:
        raise AnalysisError(f"{key} 的數字不合理:{number}")
    return number


def _clean_text(value: object, label: str, max_chars: int) -> str:
    if not isinstance(value, str):
        raise AnalysisError(f"{label} 不是文字")
    return " ".join(value.split())[:max_chars]
