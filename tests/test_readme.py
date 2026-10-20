"""README promises where the four guards are. Keep that promise honest."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROW = re.compile(r"^\| 防護 (\d) \|.*\| `(src/foodie/\w+\.py)` \| `(\w+)` \| (\d+)–(\d+) \|\s*$", re.M)
TOLERANCE = 12


def test_readme_guard_table_matches_the_code():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    rows = ROW.findall(readme)
    assert [r[0] for r in rows] == ["1", "2", "3", "4"], "README guard table is missing or malformed"

    for guard, file, function, start, end in rows:
        lines = (ROOT / file).read_text(encoding="utf-8").splitlines()
        marker_start = next(i for i, l in enumerate(lines, 1) if f"==== 防護 {guard}：" in l)
        marker_end = next(i for i, l in enumerate(lines, 1) if f"==== 防護 {guard} 結束" in l)
        assert abs(marker_start - int(start)) <= TOLERANCE, f"防護 {guard} starts at line {marker_start}, README says {start}"
        assert abs(marker_end - int(end)) <= TOLERANCE, f"防護 {guard} ends at line {marker_end}, README says {end}"

        # the function named in the README must really be the one that contains the block
        defs = [(i, l) for i, l in enumerate(lines, 1) if re.match(rf"\s*(async )?def {function}\(", l)]
        assert defs, f"{function} not found in {file}"
        assert defs[0][0] < marker_start < marker_end
        between = lines[defs[0][0] : marker_start - 1]
        assert not any(re.match(r"\S", l) for l in between), f"{function} ends before the 防護 {guard} block"
