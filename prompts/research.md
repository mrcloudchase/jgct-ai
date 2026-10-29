Research all sources of information available on juvenile granulosa cell tumor (JGCT) and organize it into a knowledge base within this repo, taking into account what is already in the repo before you start so you do not duplicate work.

Read CLAUDE.md first. It tells you where the knowledge base lives, the record schema, the source index, the credibility rubric, the ledger of sources already processed, and the procedure in the research-sweep skill. Follow that procedure.

Create and update knowledge base records using the schema in knowledge/schema/record.schema.json. Keep sources/index.md current as the index of all sources, adding any credible source you discover. Record every source you touch in the ledger so the next run can pick up where you stopped.

Work until the backlog is empty or you are near your budget. Stop cleanly: run the validator, rebuild the generated indexes, and write the run report. Do not run git commands; the surrounding script commits your work and opens the pull request for human review.
