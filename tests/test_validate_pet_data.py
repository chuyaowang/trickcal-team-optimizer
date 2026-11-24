import csv

import pytest

from scripts.validate_pet_data import find_unknown_job_traits, find_mission_file_errors

REGIONS = {"LAKE": 5, "POND": 5, "LAB": 4}
TRAITS = {"KIND", "KEEN"}


def _mission_file(tmp_path, *rows):
    path = tmp_path / "missions_260101.csv"
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["location", "trait_1", "trait_2"])
        w.writerows(rows)
    return str(path)


def test_mission_file_without_problems_has_no_errors(tmp_path):
    path = _mission_file(tmp_path, ["LAKE", "KEEN", ""], ["POND", "KIND", "KEEN"])
    assert find_mission_file_errors(path, REGIONS, TRAITS) == []


@pytest.mark.parametrize("rows, needle", [
    ([["NOPE", "KEEN", ""]], "NOPE"),
    ([["LAKE", "WILD", ""]], "WILD"),
    ([["LAKE", "KEEN", ""], ["LAKE", "KIND", ""]], "LAKE"),
    ([["LAKE", "KEEN", ""], ["LAB", "KIND", ""]], "region"),
])
def test_mission_file_problems_are_reported(tmp_path, rows, needle):
    errors = find_mission_file_errors(_mission_file(tmp_path, *rows), REGIONS, TRAITS)
    assert len(errors) == 1 and needle in errors[0]


def test_find_unknown_job_traits_flags_missing_key(tmp_path):
    jobs = tmp_path / "jobs.csv"
    with open(jobs, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Location", "Task", "Trait 1", "Trait 2"])
        w.writerow(["Forest", "Gather", "体贴", "未知特性"])
    # known maps only 体贴 -> KIND
    known = {"体贴": "KIND"}
    unknown = find_unknown_job_traits(str(jobs), known)
    assert unknown == ["未知特性"]
