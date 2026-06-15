import csv
import os

from src.data_loader import vocab_loader, csv_loader


def test_load_tasks_converts_localized_traits_to_keys(tmp_path, monkeypatch):
    i18n = tmp_path / "i18n"
    i18n.mkdir(parents=True)
    with open(i18n / "traits.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "en", "zh_hans", "zh_hant", "ko"])
        w.writerow(["KIND", "Kind", "体贴", "體貼", ""])
        w.writerow(["DULL", "Dull", "迟钝", "遲鈍", ""])
    monkeypatch.setattr(vocab_loader, "_I18N_DIR", str(i18n))
    vocab_loader._load_table.cache_clear()
    vocab_loader._reverse_table.cache_clear()

    jobs = tmp_path / "jobs.csv"
    with open(jobs, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Location", "Task", "Trait 1", "Trait 2"])
        w.writerow(["Forest", "Gather", "体贴", "迟钝"])

    tasks = csv_loader.load_tasks(str(jobs), lang="zh_hans")
    assert tasks[0]["task"] == "Forest - Gather"
    assert tasks[0]["bonus_skills"] == ["KIND", "DULL"]