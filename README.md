# JGCT Knowledge Base

Everything known about juvenile granulosa cell tumor (JGCT), gathered from sources read in full, written for the clinicians and researchers who treat and study it and for the families who have just heard its name.

**Read it here: [mrcloudchase.github.io/jgct-ai](https://mrcloudchase.github.io/jgct-ai/)**, built from this repository on every change. Or read the sources directly: [For clinicians and researchers](knowledge/summary/clinicians.md), [For parents and patients](knowledge/summary/families.md), and the [topic articles](knowledge/topics/).

> **Not medical advice.** This knowledge base reports what published sources say. Decisions about any person's care belong with their care team.

## What is here

| Where | What |
|---|---|
| [`knowledge/summary/`](knowledge/summary/) | The two overviews, for clinicians and for families, every sentence cited. |
| [`knowledge/topics/`](knowledge/topics/) | One synthesized article per subject: what every source reports, where they agree and disagree, what is unknown. |
| [`knowledge/records/`](knowledge/records/) | One file per source: what it is, where its full text was read, and what it says. |
| [`knowledge/INDEX.md`](knowledge/INDEX.md) | Index of every record. |
| [`analyses/`](analyses/) | The agent's own analyses across records: a patient-level dataset of published cases and pooled cohort tables, under a written protocol. Unreviewed; not a source. |
| [`analyses/`](analyses/) | The agent's own analyses across records: a patient-level dataset of published cases and pooled cohort tables, under a written protocol. Unreviewed; not a source. |
| [`sources/INDEX.md`](sources/INDEX.md) | Where the base has looked, what it found, and which relevant sources could not be read in full. |
| `state/runs/` | One report per maintenance run: what was done, what was found, what was left. |
| [`site/`](site/) | The generator that builds the public site from everything above. The site itself is built and published automatically, never committed. |

## How it is maintained

Once a month an AI agent (Claude Code) reads this whole repository, searches for everything new about JGCT, reads every source in full, updates the records, the indexes, the summaries and the site, and opens a pull request. The maintainer reviews every change before it reaches this branch and the site. The rules it works under are short and public: [`CLAUDE.md`](CLAUDE.md) and [`prompts/research.md`](prompts/research.md).

Three rules do not bend. Every record says what it rests on: the complete text, read start to finish, or, when no open route to the full text exists, the abstract alone, which is marked on the record and on every citation of it until the full text can be read. Numbers are copied from sources, never computed across them. Where sources disagree, both are recorded and neither is declared right.

The agent never rates its own work. Every record is a draft until a human has checked it against its source.

## How to help

- **Full text.** The largest gap is papers behind paywalls, including several of the field's foundational studies. Their records rest on abstracts alone; they are listed on the site under [Not yet read in full](https://mrcloudchase.github.io/jgct-ai/pending.html). If you have library access or wrote one of them, open an issue and we will arrange a way for the agent to read it.
- **Corrections.** If a record misstates its source, open an issue or a pull request naming the record and the passage.
- **Sources.** If you know of a registry, a meeting abstract, a guideline, or a paper the base has missed, open an issue with a link.

## Why

Started by a parent whose seven-year-old daughter is being treated for JGCT. See [awesome-cancer-ai](https://github.com/mrcloudchase/awesome-cancer-ai) for the wider map of AI against cancer.

## Licenses

Content under `knowledge/` is CC BY 4.0. Code is MIT.
