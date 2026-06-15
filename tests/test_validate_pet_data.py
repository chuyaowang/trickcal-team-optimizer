import csv

from scripts.validate_pet_data import find_unknown_job_traits


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
