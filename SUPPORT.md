# Support

Use GitHub issues for reproducible bugs, documentation problems, and workflow improvement requests.

Before filing an issue, run:

```bash
python -m compileall -q -f skills/review-driven-development/scripts
python skills/review-driven-development/scripts/validate_skill.py --skill-dir skills/review-driven-development
python skills/review-driven-development/scripts/self_test.py
pytest -q
```

Include the command output and your Python version.
