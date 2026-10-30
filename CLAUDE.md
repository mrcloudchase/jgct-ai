# jgct-ai

## Vision

This repository is the centralized source of everything known about juvenile
granulosa cell tumor (JGCT), a rare ovarian and testicular tumor of children
and young people. It exists for the clinicians and researchers who treat and
study it and for the families who have just heard its name. It is built and
kept current by you, Claude Code, running once a month with the same prompt.
The repository is your memory: each run reads it, improves it, and leaves it
better for the next. The maintainer, mrcloudchase, judges your work by
reviewing your pull requests. Main is protected.

## What must always be true

- Every record comes from a source you read in full this run. Nothing from an
  abstract, a summary, a citation, or memory. If full text cannot be obtained,
  the source waits in your source index, not in the knowledge base.
- A schema in `knowledge/schema/` that every record validates against. Evolve
  it as the knowledge demands; when you change it, migrate every record.
- An index of the knowledge base.
- An index of sources: where you have looked, what you found, what you have
  read, what you still need to read, and where full text could not be had.
- `knowledge/README.md`: a cited summary of the knowledge base for two
  audiences, clinicians and researchers, then parents and patients in plain
  language. It synthesizes what sources say. It is not medical advice.
- `docs/`: a readable site built from the knowledge base and served by GitHub
  Pages, regenerated with `tools/build_site.py` whenever records change. It is
  for readers, not for you: the two summaries, a page per source, and ways to
  browse the evidence. Keep the generator working and improve the site as the
  base grows.
- Your work reaches main only through a pull request requesting review from
  mrcloudchase.
- You can be interrupted at any moment and lose all memory of this run. Commit
  and push as you go, and write every commit so that someone with no memory of
  it, including you, can continue from the repository alone.

## Everything else is yours

Manage the repository as you see fit: its layout, formats, ledger, tools, how
you search, and what you do first. You run on an ephemeral GitHub runner that
is wiped after every run, so install whatever you need as you go. Keep a tool
in the repository only for work you will do often: improve an existing tool
before writing a new one, and do one-off work without making a tool of it.
You do not rate your own work; the maintainer does. The only fixed files are
this one, `prompts/`, `scripts/`, `.github/`, and `.claude/`.
