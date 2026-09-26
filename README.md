**This is the Mac version.** On Windows, use [outliers-crm-02-rules](https://github.com/OUTLIERS-ai/outliers-crm-02-rules).

# Outliers CRM - Layer 2 - The Rules

Layer 1 gave you a folder with one file per person in it. A folder will accept
anything. The same person can be in it twice under two spellings, a record can be
missing everything that matters, and one field can end up with three different
names. Nothing stops any of it.

This layer gives your CRM two rules and the code that enforces them.

## Install it

From this folder:

    python3 install.py

It finds the CRM you built in Layer 1, asks you two or three questions, installs
itself into that folder, and then shows you what your existing records look like
once the rules are applied.

If Layer 1 is not installed, this refuses and tells you so. Nothing is changed.

## What it needs beneath it

Layer 1. This installer looks for `_layers/config.json` inside your CRM folder,
which is the file Layer 1 writes. Without it there is nowhere to install to.

## What the two rules are

**One identifier per person.** Not a name. Names repeat, names change, and names
pick up decoration: a status symbol at the front, a middle initial, a company
suffix, a nickname. A system that identifies people by name will sooner or later
hold one person twice and have no way to tell you which record is right.

The installer asks which identifier you will always have for someone: a profile
link, an email address, or a phone number. Whichever you pick becomes the key. All
three survive a name change and none of them is ever handed to somebody else.

Every record also gets an **alias list**: every other name, handle, address or link
you have seen for that person. People arrive as a profile one day, an email address
the next, a name on a meeting invite the week after and a handle in a group after
that. The alias list is how all four find the one record.

**The record shape, written down where a machine can check it.** It lives in
`_engine/_schema/person.json` as data, not as a paragraph in a document. A rule that
nothing checks is not a rule, it is a preference. Drift happens one reasonable
exception at a time. Each exception is defensible on the day, and what you end up
with is several kinds of record and no single question you can ask across all of
them.

## What gets installed

| File | What it is for |
|---|---|
| `_engine/identity.py` | Answers "which person is this?". Nothing else does. |
| `_engine/schema.py` | Refuses a badly shaped record. Reads old ones anyway. |
| `_engine/_schema/person.json` | The record shape, as data. You own this file. |
| `_templates/Person.md` | Updated, so new records start with an alias list. |
| `_staging/` | A folder for records that are not certain yet. Layer 4 uses it. |
| `_layers/Layer 2 - The Rules.md` | What this layer did, for when you forget. |

## How identity resolution works

Given any identifier, in this order and never a different one:

1. profile slug (the last part of a profile link)
2. email address
3. phone number, compared on the last nine digits so country codes do not matter
4. the alias list
5. a full display name, **only** when that name belongs to exactly one person
6. otherwise nothing at all

There is deliberately no fuzzy matching. A wrong merge is worse than a miss. A miss
shows up as a skip you can see; a merge silently mixes one person's history into
another's and there is no way back. Near-matches belong in a review pile, not in a
join.

The other half of the same idea: `identifiers_for()` hands back every identifier a
person answers to. Anything that checks a person can only check what it is given, so
a note recorded under a name is invisible to a caller holding only a profile link.
Expanding one identifier into all of them before the check is what closes that gap.

## The three never-dos

These live in the contract and nothing overrides them.

**Never delete a person.** Park them, or mark them as a non-buyer, or mark them as
personal. A deleted record takes its history with it, and the history is the part
that took years to accumulate.

**Never store anything about health, beliefs, politics, sexuality, race or
biometrics.** It is the most sensitive category of personal data there is, it is
separately regulated nearly everywhere, and no CRM benefit is worth holding it.

**Never let an automation speak as you.** Nothing reaches a human being without your
hand on it.

## Try it

In Terminal, from your CRM folder (if your CRM is not at `~/CRM`, put your own folder in the `cd` line):

    cd ~/CRM
    python3 _engine/identity.py stats         a summary of your records
    python3 _engine/identity.py who "a name"  resolve one identifier
    python3 _engine/identity.py duplicates    people held in more than one file
    python3 _engine/identity.py collisions    names that belong to two people
    python3 _engine/schema.py contract        print the record shape
    python3 _engine/schema.py sweep           check your records, write nothing

## Run the tests

From the folder you downloaded:

    cd ~/outliers-crm-02-rules-mac
    python3 tests/test_identity_resolution.py
    python3 tests/test_schema_contract.py

They build a scratch folder, put invented people in it, and delete it afterwards.
They never touch your records.

## What it does not do

It does not merge anything. When it finds one person in two files it tells you, and
stops. Merging is a decision about which history is right, and a decision like that
is yours.

It does not fill anything in. The rules describe the shape; Layer 3 and Layer 4 are
what put things in it.

## Requirements

Python 3.8 or newer. Nothing else: no libraries to install, no account, no internet
connection. Runs on macOS and Linux.

This repo is made automatically from outliers-crm-02-rules@d6f5852. To report a problem or suggest a change, use that repo, not this one.
