"""The four guards must be wrapped in clear start/end comments, one block each, so a lesson can switch
them off one at a time (see CLAUDE.md)."""

import re
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "foodie"
START = re.compile(r"^\s*# ==== 防護 (\d)：.*　開始 ====\s*$")
END = re.compile(r"^\s*# ==== 防護 (\d) 結束 ====\s*$")


def find_blocks():
    found = {}
    for path in sorted(SRC.glob("*.py")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, start=1):
            if match := START.match(line):
                found.setdefault(match.group(1), []).append((path.name, number, "start"))
            elif match := END.match(line):
                found.setdefault(match.group(1), []).append((path.name, number, "end"))
    return found


def test_each_guard_has_exactly_one_start_and_one_end_in_the_same_file():
    blocks = find_blocks()
    assert sorted(blocks) == ["1", "2", "3", "4"]
    for guard, marks in blocks.items():
        assert [kind for _, _, kind in marks] == ["start", "end"], f"防護 {guard}: {marks}"
        assert marks[0][0] == marks[1][0], f"防護 {guard} 的開始和結束不在同一個檔案"
        assert marks[0][1] < marks[1][1]


@pytest.mark.parametrize("guard", ["1", "2", "3", "4"])
def test_guard_blocks_are_not_commented_out(guard):
    path, start, _ = find_blocks()[guard][0]
    end = find_blocks()[guard][1][1]
    lines = (SRC / path).read_text(encoding="utf-8").splitlines()[start : end - 1]
    code = [line for line in lines if line.strip() and not line.strip().startswith("#")]
    assert code, f"防護 {guard} 裡面沒有程式,是不是被註解掉了?"
