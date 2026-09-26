"""One human must resolve to ONE record, from any identifier.

THE RULE (Layer 2): a person has exactly one key, and everything built above joins
through it. Anything that decides identity for itself decides it differently from
its neighbour, and the disagreement is invisible until something behaves oddly in a
way nobody can explain.

WHAT SHOULD HAPPEN: given any identifier that belongs to a person -- a profile link
in any spelling, a filename, a display name however decorated, an email address, an
entry on their alias list -- the resolver returns the same record, and hands back
every other identifier that record answers to, so a caller holding only one of them
can pass all of them to whatever comes next.

WHY THAT LAST PART MATTERS: anything that matches can only match on what it is
given. A hold recorded under a name is invisible to a caller holding only a profile
link. Expanding one identifier into all of them before the check is what closes that
gap, and it is the difference between a rule that holds and a rule that mostly holds.

Every person in here is invented.

Run:  python tests/test_identity_resolution.py
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "crm"))

FAILS = []


def check(label, cond, detail=""):
    ok = bool(cond)
    print(("  PASS  " if ok else "  FAIL  ") + label
          + (("   [" + detail + "]") if detail and not ok else ""))
    if not ok:
        FAILS.append(label)


import identity                                            # noqa: E402

# ---------------------------------------------------------------- fixtures
# A scratch folder. Never point a test at real records.
TMP = Path(tempfile.mkdtemp(prefix="outliers-crm-identity-"))
os.environ["OUTLIERS_CRM_VAULT"] = str(TMP)
(TMP / "People").mkdir()


def note(rel, body):
    p = TMP / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


# 1. The same person written down twice: once with a status symbol in front of the
#    name, once plain. This is the commonest shape of a duplicate.
note("People/~ Rowan Ashdown.md", """---
name: "~ Rowan Ashdown"
linkedin-url: https://www.linkedin.com/in/rowan-ashdown/
company: Ashdown and Co
---
""")
note("_staging/Rowan Ashdown.md", """---
name: Rowan Ashdown
linkedin-url: "https://www.linkedin.com/in/rowan-ashdown"
---
""")

# 1b. A third record for the same person written by something that only had a name.
#     Left alone, a record like this shadows the keyed one and blocks both.
note("_staging/notes/Rowan Ashdown.md", """---
name: Rowan Ashdown
source: meeting invite
---
""")

# 2. Two different people who share a first name.
note("People/Tobias Fenwick.md", """---
name: Tobias Fenwick
linkedin-url: https://uk.linkedin.com/in/tobias-fenwick?originalSubdomain=uk
---
""")
note("People/Tobias Marchetti.md", """---
name: Tobias Marchetti
linkedin-url: https://www.linkedin.com/in/tobias-marchetti-77/
---
""")

# 3. A person with no profile link at all. Must still have an identity, and must not
#    silently merge with anybody.
note("People/Delia Marchetti.md", """---
name: Delia Marchetti
company: Marchetti Joinery
---
""")

# 4. Same person, link written four different ways.
note("People/Mara Quennell.md", """---
name: Mara Quennell
linkedin-url: HTTPS://WWW.LinkedIn.com/IN/MaraQuennell/?trk=search-card
---
""")

# 5. A person who arrives as an email address in one place and a nickname in another.
note("People/Isolde Brackwater.md", """---
name: Isolde Brackwater
email: isolde@brackwater.example
phone: +44 7700 900123
aliases: [Izzy Brackwater, i.brackwater@brackwater.example]
---
""")

idx = identity.build_index(vault=TMP)

print("\n=== 1. two spellings of one person are one record ===")

a = identity.resolve("~ Rowan Ashdown", index=idx)
b = identity.resolve("Rowan Ashdown", index=idx)
c = identity.resolve("https://www.linkedin.com/in/rowan-ashdown/", index=idx)

check("a decorated display name resolves", a is not None)
check("the plain name resolves", b is not None)
check("the profile link resolves", c is not None)
check("all three are the SAME person", a is not None and a == b == c,
      "%r / %r / %r" % (a, b, c))
check("the keyless third record folds in rather than shadowing the other two",
      a is not None and len(identity.record(a, index=idx)["files"]) == 3,
      repr(identity.record(a, index=idx)["files"]) if a else "unresolved")

print("\n=== 1b. a keyless record for someone unknown stays separate ===")

note("_staging/notes/Peregrine Duskwell.md", """---
name: Peregrine Duskwell
---
""")
idx2 = identity.build_index(vault=TMP)
nk = identity.resolve("Peregrine Duskwell", index=idx2)
check("a keyless record with nothing to fold into still resolves on its own",
      nk is not None)
check("and it neither absorbed anyone nor was absorbed",
      nk is not None and len(identity.record(nk, index=idx2)["files"]) == 1)

print("\n=== 2. a link-only caller can obtain the name-shaped identifiers ===")

ids = identity.identifiers_for(c, index=idx) if c else set()
low = {i.lower() for i in ids}
check("the identifier set includes the plain name", "rowan ashdown" in low, repr(sorted(low)))
check("the identifier set includes the profile link",
      any("/in/rowan-ashdown" in i for i in low), repr(sorted(low)))
check("expansion yields more identifiers than the caller started with",
      len(ids) > 1, repr(sorted(low)))
check("expansion contains both a link form and a name form",
      any("/in/" in i for i in ids) and any("/in/" not in i for i in ids))

print("\n=== 3. one profile, four spellings ===")

forms = [
    "HTTPS://WWW.LinkedIn.com/IN/MaraQuennell/?trk=search-card",
    "https://www.linkedin.com/in/maraquennell",
    "linkedin.com/in/MaraQuennell/",
    "https://uk.linkedin.com/in/maraquennell?originalSubdomain=uk",
]
got = {identity.resolve(f, index=idx) for f in forms}
check("every spelling of one profile resolves to one record",
      len(got) == 1 and None not in got, repr(got))

print("\n=== 4. different people stay different ===")

t1 = identity.resolve("Tobias Fenwick", index=idx)
t2 = identity.resolve("Tobias Marchetti", index=idx)
check("two people sharing a first name do not merge",
      t1 is not None and t2 is not None and t1 != t2, "%r vs %r" % (t1, t2))
check("a bare shared first name resolves to neither of them",
      identity.resolve("Tobias", index=idx) is None,
      repr(identity.resolve("Tobias", index=idx)))

print("\n=== 5. a person with no link still has an identity ===")

d = identity.resolve("Delia Marchetti", index=idx)
check("a link-less person resolves by name", d is not None)
check("and does not collide with anyone else",
      d not in {a, t1, t2, identity.resolve("Mara Quennell", index=idx)})

print("\n=== 6. the alias list is how four arrivals find one record ===")

by_name = identity.resolve("Isolde Brackwater", index=idx)
by_nick = identity.resolve("Izzy Brackwater", index=idx)
by_mail = identity.resolve("isolde@brackwater.example", index=idx)
by_alt = identity.resolve("i.brackwater@brackwater.example", index=idx)
by_phone = identity.resolve("07700 900123", index=idx)
check("the name resolves", by_name is not None)
check("a nickname on the alias list resolves", by_nick is not None)
check("an email address resolves", by_mail is not None)
check("a second email on the alias list resolves", by_alt is not None)
check("a phone number written differently resolves", by_phone is not None)
check("all five are the same person",
      len({by_name, by_nick, by_mail, by_alt, by_phone}) == 1,
      repr({by_name, by_nick, by_mail, by_alt, by_phone}))

print("\n=== 7. unknown input is refused, never guessed ===")

check("an unknown name returns nothing",
      identity.resolve("Somebody Not In Here", index=idx) is None)
check("an empty identifier returns nothing", identity.resolve("", index=idx) is None)
check("nothing in, nothing out", identity.resolve(None, index=idx) is None)

print("\n=== 8. a name shared by two people is refused, not picked ===")

note("People/Rowan Ashdown (the other one).md", """---
name: Rowan Ashdown
linkedin-url: https://www.linkedin.com/in/rowan-ashdown-2/
---
""")
idx3 = identity.build_index(vault=TMP)
check("the shared name is flagged ambiguous",
      "rowan ashdown" in idx3["ambiguous_names"], repr(sorted(idx3["ambiguous_names"])))
check("resolving that name returns nothing rather than the wrong person",
      identity.resolve("Rowan Ashdown", index=idx3) is None,
      repr(identity.resolve("Rowan Ashdown", index=idx3)))
check("but each profile link still resolves to its own record",
      identity.resolve("linkedin.com/in/rowan-ashdown", index=idx3)
      != identity.resolve("linkedin.com/in/rowan-ashdown-2", index=idx3)
      and identity.resolve("linkedin.com/in/rowan-ashdown-2", index=idx3) is not None)

shutil.rmtree(TMP, ignore_errors=True)

print("\n%s" % ("ALL PASS" if not FAILS else "FAILURES: " + ", ".join(FAILS)))
sys.exit(1 if FAILS else 0)
