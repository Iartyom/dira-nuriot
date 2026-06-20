#!/usr/bin/env python3
# permissive validator for apartment.json and renovation.json
import json
import os
import sys
from jsonschema import Draft7Validator, exceptions as js_ex

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  Missing file: {path}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️  Invalid JSON in {path}: {e}", file=sys.stderr)
        return None


def _validate_one(data, schema, name, strict=False):
    if data is None:
        msg = f"{name}: data missing or invalid JSON"
        if strict:
            print("ERROR:", msg, file=sys.stderr)
            return False
        else:
            print("Warning:", msg, file=sys.stderr)
            return True
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if not errors:
        return True
    if strict:
        print(f"ERROR: Schema validation failed for {name}:")
        for e in errors:
            print(f" - {list(e.path)}: {e.message}", file=sys.stderr)
        return False
    else:
        print(f"Warning: Schema issues in {name} (permissive mode) — see examples:")
        for e in errors[:5]:
            print(f" - {list(e.path)}: {e.message}", file=sys.stderr)
        return True


def validate_all(base_dir=None, strict=False):
    base = base_dir or os.path.dirname(os.path.abspath(__file__))
    apt_path = os.path.join(base, "apartment.json")
    reno_path = os.path.join(base, "renovation.json")
    apt_schema_path = os.path.join(base, "apartment.schema.json")
    reno_schema_path = os.path.join(base, "renovation.schema.json")
    management_path = os.path.join(base, "management.json")
    management_schema_path = os.path.join(base, "management.schema.json")

    apt = _load(apt_path)
    reno = _load(reno_path)
    management = _load(management_path)
    try:
        with open(apt_schema_path, encoding="utf-8") as f:
            apt_schema = json.load(f)
    except Exception as e:
        print(f"⚠️  Could not load apartment.schema.json: {e}", file=sys.stderr)
        apt_schema = {}
    try:
        with open(reno_schema_path, encoding="utf-8") as f:
            reno_schema = json.load(f)
    except Exception as e:
        print(f"⚠️  Could not load renovation.schema.json: {e}", file=sys.stderr)
        reno_schema = {}
    try:
        with open(management_schema_path, encoding="utf-8") as f:
            management_schema = json.load(f)
    except Exception as e:
        print(f"⚠️  Could not load management.schema.json: {e}", file=sys.stderr)
        management_schema = {}

    ok1 = _validate_one(apt, apt_schema, "apartment.json", strict=strict)
    ok2 = _validate_one(reno, reno_schema, "renovation.json", strict=strict)
    ok3 = _validate_one(management, management_schema, "management.json", strict=strict)
    return bool(ok1 and ok2 and ok3)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--strict', action='store_true', help='Fail on schema errors')
    args = p.parse_args()
    ok = validate_all(strict=args.strict)
    if not ok:
        print('Validation failed', file=sys.stderr)
        sys.exit(2)
    print('Validation passed')
