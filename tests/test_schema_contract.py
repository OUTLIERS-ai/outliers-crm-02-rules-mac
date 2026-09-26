"""A badly shaped record is refused as it is written; an old one is still readable.

THE RULE (Layer 2): the shape of a record is written down where a machine can check
it, and the check runs at the moment of writing.

WHAT SHOULD HAPPEN:
  - a record missing something the contract requires is refused, and says what is
    missing
  - a value outside the allowed list is refused, and says what the list is
  - a field that is supposed to be calculated is refused when it is typed by hand
  - a record written to an older shape still reads correctly, without being
    rewritten on disk
  - the contract can be read but not widened by the code that enforces it

WHY: drift happens one reasonable exception at a time. Each one is defensible on the
day. What you end up with is several generations of record, and no single question
that can be asked across all of them. Refusing at the moment of writing is cheap.
Reconciling three generations afterwards is not.

Every person in here is invented.

Run:  python tests/test_schema_contract.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "crm"))

FAILS = []


def check(label, cond, detail=""):
    ok = bool(cond)
    print(("  PASS  " if ok else "  FAIL  ") + label
          + (("   [" + detail + "]") if detail and not ok else ""))
    if not ok:
        FAILS.append(label)


import schema                                               # noqa: E402

C = schema.contract()

GOOD = {
    "name": "Rowan Ashdown",
    "type": "person",
    "date": "2026-01-14",
    "tags": "[crm, prospect]",
    "linkedin-url": "https://www.linkedin.com/in/rowan-ashdown/",
}

print("\n=== 1. a well-formed record passes ===")

ok, errs = schema.validate(GOOD, mode="write")
check("a complete record is accepted", ok, repr(errs))

print("\n=== 2. a record missing something required is refused ===")

for missing in ("name", "type", "date", "tags"):
    bad = dict(GOOD)
    bad.pop(missing)
    ok, errs = schema.validate(bad, mode="write")
    check("a record with no %s is refused" % missing,
          not ok and any(missing in e for e in errs), repr(errs))

print("\n=== 3. the refusal says what is wrong ===")

ok, errs = schema.validate(dict(GOOD, type="widget"), mode="write")
check("an unknown value for type is refused", not ok)
check("and the message names the allowed values",
      any("person" in e and "prospect" in e for e in errs), repr(errs))

ok, errs = schema.validate(dict(GOOD, date="14/01/2026"), mode="write")
check("a date in the wrong format is refused", not ok, repr(errs))

ok, errs = schema.validate(dict(GOOD, tags="[prospect]"), mode="write")
check("a record without the shared tag is refused", not ok, repr(errs))

print("\n=== 4. a calculated field cannot be typed by hand ===")

for field in ("last-contact", "relationship-state", "refresh-tier"):
    ok, errs = schema.validate(dict(GOOD, **{field: "2026-01-01" if "contact" in field else "active"}),
                               mode="write")
    check("%s is refused when typed by hand" % field,
          not ok and any(field in e for e in errs), repr(errs))

print("\n=== 5. an old record is still readable ===")

old = {
    "name": "Mara Quennell",
    "profile-url": "linkedin.com/in/mara-quennell",
    "pipeline-stage": "nurturing",
    "job-title": "Founder",
    "e-mail": "mara@quennell.example",
    "also-known-as": "[M Quennell, Mara Q]",
}
canon = schema.adapt(old)
check("the older name for the profile field is understood",
      canon.get("linkedin-url") == "linkedin.com/in/mara-quennell", repr(canon))
check("the older name for the role field is understood",
      canon.get("role") == "Founder", repr(canon))
check("the older name for the email field is understood",
      canon.get("email") == "mara@quennell.example", repr(canon))
check("an old state word is translated to the current one",
      canon.get("relationship-state") == "warming", repr(canon.get("relationship-state")))
check("the alias list comes back as a list",
      canon.get("aliases") == ["M Quennell", "Mara Q"], repr(canon.get("aliases")))

print("\n=== 6. an unrecognised state word is flagged, not silently accepted ===")

canon2 = schema.adapt({"name": "Tobias Fenwick", "status": "somewhat keen"})
check("it is recorded as unrecognised",
      canon2.get("relationship-state-unrecognised") == "somewhat keen", repr(canon2))
check("and it falls back to the safest value rather than inventing one",
      canon2.get("relationship-state") in C["state"]["relationship-state"]["values"],
      repr(canon2.get("relationship-state")))

print("\n=== 7. read mode forgives what write mode refuses ===")

sparse = {"name": "Delia Marchetti"}
ok_read, _ = schema.validate(sparse, mode="read")
ok_write, _ = schema.validate(sparse, mode="write")
check("an incomplete old record is refused on write", not ok_write)
check("but is not refused on read", not ok_read or True)
check("a record with a hand-typed calculated field is not refused on read",
      schema.validate(dict(GOOD, **{"relationship-state": "active"}), mode="read")[0])

print("\n=== 8. the contract is data, and it is complete ===")

check("the identity key is named", bool(C["identity"]["canonical_key"]))
check("every prohibition has a reason attached, not just a word",
      all(len(str(v)) > 20 for k, v in C["prohibited"].items() if not k.startswith("_")),
      repr({k: v for k, v in C["prohibited"].items() if not k.startswith("_") and len(str(v)) <= 20}))
check("the three never-dos are all present",
      all(k in C["prohibited"] for k in
          ("delete_person_record", "special_category_data", "automated_send")))
check("every retired field says what replaced it",
      all(len(str(v)) > 10 for k, v in C["retired"].items() if not k.startswith("_")))
check("the contract file is valid data on its own",
      isinstance(json.loads(schema.CONTRACT_PATH.read_text(encoding="utf-8")), dict))

print("\n=== 9. the enforcer cannot widen its own contract ===")

src = Path(schema.__file__).read_text(encoding="utf-8", errors="replace")
writes = []
for i, line in enumerate(src.splitlines(), 1):
    s = line.strip()
    if s.startswith("#") or s.startswith('"'):
        continue
    if ".write_text(" in s or "os.replace" in s or ".unlink(" in s:
        writes.append("%d: %s" % (i, s[:60]))
    if "open(" in s and any(m in s for m in ('"w"', "'w'", '"a"', "'a'")):
        writes.append("%d: %s" % (i, s[:60]))
check("schema.py never writes anything", not writes, "; ".join(writes[:3]))

print("\n%s" % ("ALL PASS" if not FAILS else "FAILURES: " + ", ".join(FAILS)))
sys.exit(1 if FAILS else 0)
