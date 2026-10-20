import json

import pytest

from foodie.result_check import AnalysisError, extract_json_object, parse_claude_stdout, validate_result

GOOD = {
    "is_food": True,
    "legible": True,
    "name": "牛肉麵",
    "ingredients": ["牛肉", "麵條"],
    "weight_g": 500,
    "calories_kcal": 650,
}


def envelope(**overrides) -> str:
    outer = {"is_error": False, "structured_output": dict(GOOD), "result": ""}
    outer.update(overrides)
    return json.dumps(outer, ensure_ascii=False)


def test_structured_output_is_used():
    result = parse_claude_stdout(envelope())
    assert result.name == "牛肉麵"
    assert result.weight_g == 500
    assert result.calories_kcal == 650
    assert result.ingredients == ("牛肉", "麵條")


def test_falls_back_to_result_text_with_code_fence():
    text = "好的:\n```json\n" + json.dumps(GOOD, ensure_ascii=False) + "\n```"
    result = parse_claude_stdout(envelope(structured_output=None, result=text))
    assert result.calories_kcal == 650


@pytest.mark.parametrize("stdout", ["", "not json", "[1, 2]", "null", "{"])
def test_garbage_outer_output_is_an_analysis_error(stdout):
    with pytest.raises(AnalysisError):
        parse_claude_stdout(stdout)


def test_claude_reporting_an_error():
    with pytest.raises(AnalysisError):
        parse_claude_stdout(envelope(is_error=True, subtype="error_during_execution"))


@pytest.mark.parametrize("text", [None, 5, "no braces here", "{broken", "[1]"])
def test_extract_json_object_rejects_junk(text):
    with pytest.raises(AnalysisError):
        extract_json_object(text)


@pytest.mark.parametrize("field", ["weight_g", "calories_kcal"])
@pytest.mark.parametrize(
    "bad",
    ["約 650", "650 大卡", "", "abc", None, True, [650], {"v": 1}, -1, float("inf"), float("nan"), 999999, "-5", "1e3"],
)
def test_numbers_that_are_not_numbers_are_rejected(field, bad):
    with pytest.raises(AnalysisError):
        validate_result({**GOOD, field: bad})


def test_numeric_text_is_accepted():
    result = validate_result({**GOOD, "weight_g": "250", "calories_kcal": " 99.5 "})
    assert (result.weight_g, result.calories_kcal) == (250.0, 99.5)


@pytest.mark.parametrize("field", ["is_food", "legible"])
@pytest.mark.parametrize("bad", ["yes", "true", 1, 0, None])
def test_booleans_must_be_real_booleans(field, bad):
    with pytest.raises(AnalysisError):
        validate_result({**GOOD, field: bad})


@pytest.mark.parametrize("field", ["is_food", "legible", "name", "ingredients", "weight_g", "calories_kcal"])
def test_missing_fields_are_rejected(field):
    obj = dict(GOOD)
    del obj[field]
    with pytest.raises(AnalysisError):
        validate_result(obj)


def test_text_is_tidied_and_capped():
    result = validate_result({**GOOD, "name": "  牛肉\n麵  " + "長" * 100, "ingredients": ["a"] * 40 + [" "]})
    assert "\n" not in result.name and len(result.name) <= 50
    assert len(result.ingredients) <= 15


def test_blank_name_is_rejected():
    with pytest.raises(AnalysisError):
        validate_result({**GOOD, "name": "   "})


def test_ingredients_must_be_a_list_of_text():
    with pytest.raises(AnalysisError):
        validate_result({**GOOD, "ingredients": "牛肉"})
    with pytest.raises(AnalysisError):
        validate_result({**GOOD, "ingredients": [1, 2]})
