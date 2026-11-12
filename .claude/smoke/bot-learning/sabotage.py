"""Control negativo de `templates/bot-learning` y `templates/bot-trace` (sub-ola 3.40).

Planta un sabotaje por garantía en una copia de los kits y comprueba que algún test cae.
Necesita un python con pytest (el del sistema no lo trae):

    bash .claude/hooks/check-ram.sh && <venv>/bin/python .claude/smoke/bot-learning/sabotage.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "templates"
PY = sys.argv[2] if len(sys.argv) > 2 else sys.executable
SABOTAGES = [
    ("bot-learning", "owner_comments.py", "turn = index.resolve(comment.message_id)",
     "turn = list(index._by_message.values())[-1] if index._by_message else None"),
    ("bot-learning", "owner_comments.py", '"comment": mask(comment.text)', '"comment": comment.text'),
    ("bot-learning", "owner_comments.py", '"qa-" + hashlib', '"qa-" + str(id(comment_id)) + hashlib'),
    ("bot-learning", "dataset.py", 'random.Random(f"{seed}:{case_id}").random()', "random.random()"),
    ("bot-learning", "dataset.py", "if not human and not case.approved_by_human:", "if False:"),
    ("bot-learning", "dataset.py", "if case.tenant_id != dataset_tenant and not allow_cross_tenant:", "if False:"),
    ("bot-learning", "scores.py", 'if name.startswith("fb."):', "if False:"),
    ("bot-learning", "learning_check.py", "elif SHUFFLE.search(text):", "elif False:"),
    ("bot-learning", "learning_check.py", '".claude", ', ""),
    ("bot-trace", "comms_recorder.py", "if k.lower() not in _FORBIDDEN_KEYS", "if True"),
    ("bot-trace", "comms_recorder.py", '"path": path or "/"', '"path": url'),
    ("bot-trace", "comms_recorder.py", '":id" if _ID_SEGMENT.search(s) else s', "s"),
    ("bot-trace", "comms_recorder.py", 'clean["filter"] = sorted(clean["filter"])', "pass"),
    ("bot-trace", "comms_recorder.py", "    except Exception:  # defensive: el observador no tumba el turno\n        pass",
     "    except ZeroDivisionError:\n        pass"),
    ("bot-trace", "comms_recorder.py", "if not (force or enabled()):", "if False:"),
    ("bot-trace", "explorer.py", 'b["mark"] = FAIL_MARK if (b["failed"] and not marked) else ""',
     'b["mark"] = FAIL_MARK if b["failed"] else ""'),
    ("bot-trace", "explorer.py", 'return e.get("system") == "error" or e.get("ok") is False', "return False"),
    ("bot-trace", "conformance.py", '"result": UNKNOWN,\n                           "detail": "la grabadora no marcó nodos"',
     '"result": OK,\n                           "detail": "la grabadora no marcó nodos"'),
    ("bot-trace", "conformance.py", "ok = all(p >= 0 for p in pos) and pos == sorted(pos)", "ok = True"),
    ("bot-trace", "conformance.py", '"result": OK if n <= cap else FAIL', '"result": OK'),
]
caught = 0
for kit, fname, old, new in SABOTAGES:
    with tempfile.TemporaryDirectory() as d:
        dst = Path(d) / kit
        shutil.copytree(ROOT / kit, dst)
        f = dst / fname
        text = f.read_text()
        assert old in text, (kit, fname, old)
        f.write_text(text.replace(old, new, 1))
        r = subprocess.run([PY, "-m", "pytest", str(dst), "-q", "-x", "-p", "no:cacheprovider"],
                           capture_output=True, text=True)
        ok = r.returncode != 0
        caught += ok
        print(("CAZADO " if ok else "ESCAPA ") + f"{kit}/{fname}: {new[:60]!r}")
print(f"{caught}/{len(SABOTAGES)} sabotajes cazados")
sys.exit(0 if caught == len(SABOTAGES) else 1)
