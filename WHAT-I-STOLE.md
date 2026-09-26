# What this layer borrows

Almost nothing in here is new. These are old ideas from fields that had to solve the
same problem at a much larger scale, and they are worth naming honestly so you know
where to read more.

## Record linkage

The problem of deciding whether two records describe the same real-world thing has a
name and a literature going back to the 1940s and 50s, in public health and census
work. Halbert Dunn called it "record linkage" in 1946; Newcombe and colleagues
automated it in 1959; Fellegi and Sunter gave it a formal treatment in 1969.

What this layer takes from it is the framing more than the maths: identity is a
decision made from evidence, not a fact you read off a field. It also takes the
distinction between a **deterministic** match (two records share a key that is
unique by construction) and a **probabilistic** one (two records are similar enough
that they are probably the same person).

What this layer deliberately does not take is the probabilistic half. At the scale a
one-person business works at, a wrong merge costs more than a missed one. A miss
shows up as a skip you can see. A merge quietly mixes two people's histories and
there is no undo. So there is no fuzzy matching here at all. Near-matches go to a
review pile.

## Natural keys and surrogate keys

Straight from database design. A **natural key** is an identifier the world already
gives you: a profile link, an email address. A **surrogate key** is one you invent,
usually a number, with no meaning outside your system.

The rule this layer follows is the old one: a key must be unique, stable, and never
reused. A name fails all three. A profile link passes all three, which is why it is
the default here. The system uses it as-is rather than minting its own ID, because
an invented ID would be one more thing to reconcile every time data arrives from
outside.

## Canonicalisation, and Postel's law

Normalising an identifier into a single canonical form before comparing it is how
every URL library, email system and search index has worked for decades. Here it is
`slug()`, `norm_name()`, `norm_email()` and `norm_phone()`.

The pairing is sometimes called the robustness principle, or Postel's law, from an
early internet specification: be conservative in what you send, liberal in what you
accept. That is exactly the split between `validate()` and `adapt()`. Records are
written to one strict shape; records are read in any shape they have ever been
written in.

## Union-find (disjoint-set)

The algorithm that groups records sharing any identifier into one person is
union-find, from Galler and Fischer in 1964. It is about fifteen lines here. It is
the standard way to answer "these things are connected, how many distinct groups are
there?" without holding a graph in memory.

## Schema-as-data, and schema validation

Holding the record contract as a JSON file that code reads, rather than as rules
spread through the code itself, is the same idea as JSON Schema, XML Schema, or a
database's DDL. One statement of the shape, many things checking against it.

Two properties of that idea matter more than the format:

- **Validation happens at write time.** This is the "parse, don't validate" argument
  from the functional-programming world, applied to a folder of notes. Refuse a bad
  record at the door and everything downstream can assume a good one.
- **The enforcer cannot edit the contract.** Anything that can widen its own rules
  has no rules. There is a test in `tests/` that checks `schema.py` never writes
  anything at all.

## Tolerant reading, without migration

The pattern where writers write the current shape and readers understand every past
shape is standard in long-lived systems: schema evolution in Avro and Protocol
Buffers, expand-and-contract migrations in databases, versioned APIs.

The reason it is here is not elegance. It is that a migration over a folder of
personal records is a risk you do not need to take. Reading old records correctly
costs a lookup table. Rewriting several thousand files costs you the one copy you
have.

## Provenance

The requirement that a written fact carries where it came from, when, and how
confident the source was, comes from scientific data management and from library
cataloguing before that. The W3C has a standard for it called PROV.

The practical reason it is in the contract: an accurate statement and an invented one
are formatted identically. A week later the source is the only thing that tells them
apart.

## Data-protection practice

The prohibition on storing anything about health, beliefs, politics, sexuality, race
or biometrics is not a house style. Those categories are separately and more
strictly regulated in most of the world, including under the UK and EU General Data
Protection Regulation, where they are called special category data.

The rule here is stricter than the law, on purpose: do not hold it at all. The
simplest way to comply with a rule about sensitive data is to have none.
