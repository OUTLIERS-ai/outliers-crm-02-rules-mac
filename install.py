"""
Outliers CRM - Layer 2 - The Rules

Layer 1 gave you a folder. A folder will accept anything: the same person twice
under two spellings, a record with nothing on it, a field called three different
names. This layer gives your CRM rules, and something that enforces them.

    python install.py

It finds the CRM you built in Layer 1, asks you two or three questions, and
installs the rules into it. Then it looks at the records you already have and
tells you what it found.

Nothing here costs money and nothing leaves your computer. No account, no sign-up,
no internet connection required.

Needs: Python 3.8 or newer, and Layer 1 already installed.
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

# The command a member types to start Python: `python3` on a Mac, which has no plain
# `python` command, and `python` everywhere else, as the Windows guides print it.
PY = "python3" if sys.platform == "darwin" else "python"

# The key a member presses. A Mac keyboard's key is Return; Windows keeps Enter, exactly as before
# (Mac build plan V3, wave s1: the Session 7 ruling on the words installers print).
KEY = "Return" if sys.platform == "darwin" else "Enter"

LAYER = 2
LAYER_NAME = "The Rules"
NEEDS_LAYER = 1

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- small helpers

# No colour codes anywhere. Plenty of terminals print them as literal gibberish,
# and a member's first minute with this must not look broken. Plain text works
# everywhere, which is the whole point of the exercise.
BOLD = DIM = OFF = ""


def say(msg=""):
    print(msg, flush=True)


def ask(question, default=None, helptext=None):
    """One plain question. Enter accepts the default."""
    say()
    say(BOLD + question + OFF)
    if helptext:
        say(DIM + "  " + helptext + OFF)
    prompt = "  > " if default is None else "  [%s] > " % default
    try:
        answer = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        say("\nStopped. Nothing was changed.")
        sys.exit(1)
    return answer or (default or "")


def ask_yes(question, default=True):
    d = "Y/n" if default else "y/N"
    a = ask(question, default=d).strip().lower()
    if a in ("y/n", "y/n".upper(), "y", "yes"):
        return True if a != "y/n" else default
    if a in ("n", "no"):
        return False
    return default


def write(path, content):
    """Write a file without ever damaging one that already exists.

    Writes to a temporary file first, then swaps it into place in a single step.
    If anything goes wrong halfway through, the original is untouched. This is a
    habit worth keeping: the notes in here are the record, and there is no copy.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def copy_in(src, dst):
    """Install one file from this repo into the CRM, atomically."""
    write(dst, Path(src).read_text(encoding="utf-8"))



def ensure_gitignore(home, entries):
    """Add lines to the CRM's .gitignore if they are not already there.

    Never rewrites what is in there, only adds. Layer 1 put your records in this
    file so they cannot be published by accident; each layer adds whatever it
    creates that belongs in the same category.
    """
    p = Path(home) / ".gitignore"
    current = p.read_text(encoding="utf-8") if p.exists() else ""
    lines = [ln.strip() for ln in current.splitlines()]
    missing = [e for e in entries if e not in lines]
    if not missing:
        return False
    body = current
    if body and not body.endswith("\n"):
        body += "\n"
    write(p, body + "\n".join(missing) + "\n")
    return True

# ------------------------------------------------------------------ finding the CRM

def looks_like_a_crm(p):
    return (Path(p) / "_layers" / "config.json").exists()


def find_vault():
    # Layer 1 leaves a pointer in the home folder naming wherever the member chose to
    # put their CRM. Checking it first means anyone who declined the default location
    # is not told, wrongly, that they have not done Layer 1 yet.
    pointer = Path.home() / ".outliers-crm"
    guesses = []
    if pointer.exists():
        try:
            noted = pointer.read_text(encoding="utf-8").strip()
            if noted:
                guesses.append(Path(noted))
        except Exception:
            pass
    guesses += [Path.home() / "CRM", Path.cwd(), Path.cwd().parent]
    for g in guesses:
        if looks_like_a_crm(g):
            say()
            say("Found a CRM at: %s" % g)
            if ask_yes("Is that the one?", default=True):
                return Path(g)
            break
    raw = ask("Where is your CRM?",
              default=str(guesses[0]),
              helptext="The folder Layer 1 built. It has a People folder inside it.")
    return Path(raw.strip().strip('"').strip("'")).expanduser()


def previous_layer(home):
    """Return the config Layer 1 wrote, or None if this layer cannot run yet."""
    cfg_path = Path(home) / "_layers" / "config.json"
    if not cfg_path.exists():
        say()
        say("Layer %d needs Layer %d first. Run that one and come back."
            % (LAYER, NEEDS_LAYER))
        say()
        say("  Looked for: %s" % cfg_path)
        say("  Nothing was changed.")
        return None
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except ValueError:
        say()
        say("Layer %d needs Layer %d first. Run that one and come back."
            % (LAYER, NEEDS_LAYER))
        say()
        say("  %s exists but could not be read." % cfg_path)
        return None
    if int(cfg.get("layer", 0)) < NEEDS_LAYER:
        say()
        say("Layer %d needs Layer %d first. Run that one and come back."
            % (LAYER, NEEDS_LAYER))
        say()
        say("  That CRM is on layer %s." % cfg.get("layer"))
        return None
    return cfg


# ---------------------------------------------------------------- the interview

KEY_CHOICES = {
    "1": ("linkedin-url", "a profile link"),
    "2": ("email", "an email address"),
    "3": ("phone", "a phone number"),
    "profile": ("linkedin-url", "a profile link"),
    "link": ("linkedin-url", "a profile link"),
    "linkedin": ("linkedin-url", "a profile link"),
    "email": ("email", "an email address"),
    "phone": ("phone", "a phone number"),
    "mobile": ("phone", "a phone number"),
}


def interview(cfg):
    say()
    say(BOLD + "=" * 66 + OFF)
    say(BOLD + "  OUTLIERS CRM   LAYER 2   THE RULES" + OFF)
    say(BOLD + "=" * 66 + OFF)
    say()
    say("  Layer 1 gave you a folder. A folder will accept anything, including")
    say("  the same person twice. This adds the rules, and something that checks")
    say("  them. It asks two or three questions first.")
    say()
    say(DIM + "  Press %s to accept anything in [brackets]." % KEY + OFF)

    default_key = cfg.get("identifier") or "linkedin-url"
    default_choice = {"linkedin-url": "1", "email": "2", "phone": "3"}.get(default_key, "1")

    say()
    say(BOLD + "Which identifier will you always have for someone?" + OFF)
    say(DIM + "  1. a profile link   (for example linkedin.com/in/rowan-ashdown)" + OFF)
    say(DIM + "  2. an email address" + OFF)
    say(DIM + "  3. a phone number" + OFF)
    say(DIM + "  This becomes the one thing that identifies a person. A name will" + OFF)
    say(DIM + "  not do the job: names repeat, they change, and they pick up" + OFF)
    say(DIM + "  decoration. The three above survive a name change and are never" + OFF)
    say(DIM + "  handed to somebody else." + OFF)
    raw = ask("Pick a number", default=default_choice)
    key_field, key_label = KEY_CHOICES.get(raw.strip().lower(), KEY_CHOICES[default_choice])

    personal = ask_yes("Do you keep personal contacts in here too? "
                       "(friends, family, people you know outside work)",
                       default=True)

    skip_personal = True
    if personal:
        skip_personal = ask_yes("Should anything commercial skip them?", default=True)

    return {
        "home": None,
        "key_field": key_field,
        "key_label": key_label,
        "personal": personal,
        "skip_personal": skip_personal,
        "people_word": cfg.get("people_word") or "contacts",
    }


# ----------------------------------------------------------------- what we write

def personalised_contract(answers):
    """Take the contract shipped with this repo and set it to their answers."""
    c = json.loads((HERE / "crm" / "_schema" / "person.json").read_text(encoding="utf-8"))
    c["identity"]["canonical_key"] = answers["key_field"]
    c["identity"]["required_on_write"] = True
    c["updated"] = date.today().isoformat()
    c["policy"] = {
        "_comment": ("Your answers at install. Anything that acts on people reads these "
                     "rather than assuming."),
        "personal_contacts_stored": answers["personal"],
        "commercial_skips_personal": answers["skip_personal"],
    }
    if answers["personal"] and answers["skip_personal"]:
        c["state"]["relationship-state"]["_note_personal"] = (
            "personal means friend, family, or anyone you know outside work. Nothing "
            "commercial touches them: not contacted, not scored, not counted in a "
            "pipeline. It is a state rather than a folder so the exclusion is explicit "
            "and a record cannot escape it by being moved.")
    return json.dumps(c, indent=2) + "\n"


def person_template(answers):
    field = answers["key_field"]
    example = {"linkedin-url": "https://www.linkedin.com/in/their-profile",
               "email": "them@theircompany.example",
               "phone": "+44 7700 900000"}[field]
    return """---
name:
{field}:
aliases: []
company:
role:
met-through:
date: {today}
type: person
tags: [crm]
---

## Who they are

## What we have talked about

## What happens next

<!--
{field} is the one thing that identifies this person. Example: {example}

aliases is every OTHER way you have seen them: a nickname, a maiden name, a second
email address, the name on a meeting invite, a handle in a group. People arrive
under all of those. The alias list is how all of them find this one record.
-->
""".format(field=field, today=date.today().isoformat(), example=example)


def layer_note(answers):
    return """# Layer {n} - {name}

**What it built.** Two rules, and code that enforces them.

The first rule is that every person has one identifier, and yours is
`{field}`. Not a name. Names repeat, they change, and they pick up decoration, so a
system that identifies people by name will sooner or later hold one person twice and
be unable to tell which record is right.

The second rule is the record shape, written down in `_engine/_schema/person.json`
where a machine can read it. A rule that nothing checks is not a rule, it is a
preference. Drift happens one reasonable exception at a time, and by the time you
notice you have several kinds of record and no question you can ask across all of
them.

**What it does.**

| File | What it is for |
|---|---|
| `_engine/identity.py` | Answers "which person is this?" and nothing else does. |
| `_engine/schema.py` | Refuses a badly shaped record, and reads old ones anyway. |
| `_engine/_schema/person.json` | The record shape, as data. You own this file. |

Try it:

    {py} _engine/identity.py stats
    {py} _engine/identity.py who "some name or link"
    {py} _engine/identity.py duplicates

**The never-dos.** Three prohibitions live in the contract, and nothing overrides
them. Never delete a person: park them or mark them, but a deleted record takes its
history with it and the history is the asset. Never store anything about health,
beliefs, politics, sexuality, race or biometrics: it is the most sensitive data
there is, it is regulated nearly everywhere, and no CRM benefit is worth holding it.
Never let an automation speak as you.

**What it leaves for Layer 3.** The rules describe the shape but they do not fill it
in, and whatever you write down about a person goes out of date on its own with
nobody touching it. "Spoke to her recently" starts dying the moment you type it.
Layer 3 is the difference between a fact and a description.
""".format(n=LAYER, name=LAYER_NAME, field=answers["key_field"], py=PY)


# ------------------------------------------------------------------------- build

def build(home, answers):
    say()
    say(BOLD + "Installing Layer %d into %s" % (LAYER, home) + OFF)
    say()

    def note(path, what):
        say("  wrote  %-40s %s" % (str(Path(path).relative_to(home)).replace("\\", "/"), what))

    engine = home / "_engine"

    for name in ("identity.py", "schema.py"):
        p = engine / name
        copy_in(HERE / "crm" / name, p)
        note(p, {"identity.py": "decides which person a record is",
                 "schema.py": "checks the shape of a record"}[name])

    p = engine / "_schema" / "person.json"
    write(p, personalised_contract(answers))
    note(p, "the record shape, as data. yours to edit")

    p = home / "_templates" / "Person.md"
    write(p, person_template(answers))
    note(p, "the shape a new record starts from, now with an alias list")

    (home / "_staging").mkdir(parents=True, exist_ok=True)
    say("  made   %-40s %s" % ("_staging/", "for records that are not sure yet"))

    p = home / "_layers" / ("Layer %d - %s.md" % (LAYER, LAYER_NAME))
    write(p, layer_note(answers))
    note(p, "what this layer did, for when you forget")

    if ensure_gitignore(home, ["__pycache__/", "*.pyc"]):
        say("  added  %-40s the code folder writes cache files. those are not yours" % (".gitignore",))

    cfg_path = home / "_layers" / "config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg.update({
        "layer": max(int(cfg.get("layer", 1)), LAYER),
        "identifier": answers["key_field"],
        "identity_key": answers["key_field"],
        "personal_contacts_stored": answers["personal"],
        "commercial_skips_personal": answers["skip_personal"],
        "scan_folders": cfg.get("scan_folders") or ["People", "_staging"],
        "layer_%d_installed" % LAYER: date.today().isoformat(),
    })
    write(cfg_path, json.dumps(cfg, indent=2) + "\n")
    note(cfg_path, "records that Layer %d is in" % LAYER)


# --------------------------------------------------------------------- now use it

def look_at_their_records(home, answers):
    """The point of the layer, made visible on their own records."""
    sys.path.insert(0, str(home / "_engine"))
    os.environ["OUTLIERS_CRM_VAULT"] = str(home)
    try:
        import identity
    except ImportError as e:
        say("  Could not load the identity code (%s). The files are installed; "
            "you can run them yourself." % e)
        return

    idx = identity.build_index(vault=home)
    people = idx["people"]
    keyed = sum(1 for r in people.values()
                if r["slugs"] or r["emails"] or r["phones"])
    dupes = {pid: r["files"] for pid, r in people.items() if len(r["files"]) > 1}

    say()
    say(BOLD + "-" * 66 + OFF)
    say(BOLD + "  What your records look like to the rules" + OFF)
    say(BOLD + "-" * 66 + OFF)
    say()
    say("  people                    %d" % len(people))
    say("  with a strong identifier  %d" % keyed)
    say("  name only                 %d" % (len(people) - keyed))
    say("  in more than one file     %d" % len(dupes))
    say("  ambiguous names           %d" % len(idx["ambiguous_names"]))
    say()
    if len(people) - keyed:
        say("  A record with only a name on it is the fragile kind. If you ever meet")
        say("  a second person with that name, neither of them can be identified")
        say("  with confidence. Filling in the %s is the fix, and you can do it" % answers["key_field"])
        say("  a few at a time.")
        say()
    if dupes:
        say("  These people are held in more than one file:")
        for pid, files in list(dupes.items())[:5]:
            say("    %s" % pid)
            for f in files:
                say("        %s" % f)
        if len(dupes) > 5:
            say("    ... and %d more" % (len(dupes) - 5))
        say()
        say("  The rules found them. Merging is a decision, so nothing was moved.")
        say()
    if idx["ambiguous_names"]:
        say("  These names belong to more than one person, so asking for them by")
        say("  name is refused rather than guessed at:")
        for n in sorted(idx["ambiguous_names"])[:5]:
            say("    %s" % n)
        say()

    say(BOLD + "  Now try it." + OFF)
    say("  Give it a person one way, and it comes back with every other way that")
    say("  same person can be reached. This is thirty seconds and it is the whole")
    say("  idea of the layer made visible.")
    who = ask("A name, a link or an email address (or %s to skip)" % KEY, default="")
    if not who.strip():
        say(DIM + "  Skipped. You can run it any time:" + OFF)
        say(DIM + "    %s _engine/identity.py who \"some name\"" % PY + OFF)
        return
    pid = identity.resolve(who.strip(), index=idx)
    if not pid:
        say()
        say("  Not found, and deliberately not guessed at. Either that person is")
        say("  not in your records, or the name belongs to two people. It is the")
        say("  refusal that keeps two histories from being merged into one.")
        return
    rec = identity.record(pid, index=idx)
    say()
    say("  One record: %s" % pid)
    say("  Held in:    %s" % ", ".join(rec["files"]))
    say("  Answers to: ")
    for i in sorted(identity.identifiers_for(pid, index=idx)):
        say("      %s" % i)


def finish(home, answers):
    say()
    say(BOLD + "=" * 66 + OFF)
    say(BOLD + "  Done. Your CRM has rules." + OFF)
    say(BOLD + "=" * 66 + OFF)
    say()
    say("  What changed:")
    say("    - One identifier per person, and yours is %s." % answers["key_field"])
    say("    - Every record has an alias list, so the same person arriving as a")
    say("      nickname, a second email or a name on an invite finds one record.")
    say("    - The record shape is written down where a machine checks it.")
    say("    - Three never-dos, in the contract, that nothing overrides.")
    say()
    say("  Read: _layers/Layer %d - %s.md" % (LAYER, LAYER_NAME))
    say()
    say(BOLD + "  What Layer 3 does." + OFF)
    say("  Everything you type about a person goes out of date on its own. Layer 3")
    say("  stores what HAPPENED instead, and calculates the rest from it.")
    say()


def main():
    say()
    say("  Outliers CRM, Layer %d: %s" % (LAYER, LAYER_NAME))
    home = find_vault()
    cfg = previous_layer(home)
    if cfg is None:
        return 1

    answers = interview(cfg)
    answers["home"] = home

    say()
    say("  Installing into:   %s" % home)
    say("  Identifier:        %s (%s)" % (answers["key_field"], answers["key_label"]))
    say("  Personal contacts: %s" % ("kept here, skipped by anything commercial"
                                     if answers["personal"] and answers["skip_personal"]
                                     else "kept here" if answers["personal"]
                                     else "not kept here"))
    if not ask_yes("Go ahead?", default=True):
        say("\nStopped. Nothing was changed.")
        return 1

    build(home, answers)
    look_at_their_records(home, answers)
    finish(home, answers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
