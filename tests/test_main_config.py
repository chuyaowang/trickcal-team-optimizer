import json

import main


def test_cn_config_runs_as_gl_cn(tmp_path, capsys):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({
        "server": "cn", "max_job_number": 5,
        "owned_pets": [], "aux_pets_counts": {}, "ui_language": "en",
    }), encoding="utf-8")
    main.run_config(str(cfg), lang="en")
    assert "Server: GL-CN" in capsys.readouterr().out
