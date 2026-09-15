# RMB Answer-Level Stage Attribution

## atlas-historical

Question: What database did Atlas originally use?
Required facts: PostgreSQL
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## atlas-timeline

Question: What did Atlas use originally and what does it use currently?
Required facts: PostgreSQL, SQLite
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## atlas-project

Question: Which project uses event-sourced architecture?
Required facts: Atlas, event-sourced
Baseline: retrieval=FAIL, context=FAIL, answer=FAIL; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## atlas-preference

Question: What does user currently prefer for Atlas?
Required facts: concise updates
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## atlas-comparison

Question: Compare Atlas's original database with the database currently used.
Required facts: PostgreSQL, SQLite
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## atlas-multi

Question: What are Atlas's current database and architecture, and why?
Required facts: SQLite, event-sourced, offline operation
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## atlas-provenance

Question: Which session is the source for Atlas's current primary database decision?
Required facts: atlas-session-10
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## atlas-constraint

Question: What constraint caused Atlas's database change?
Required facts: offline operation
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## beacon-historical

Question: What database did Beacon originally use?
Required facts: MySQL
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## beacon-timeline

Question: What did Beacon use originally and what does it use currently?
Required facts: MySQL, DuckDB
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## beacon-project

Question: Which project uses columnar architecture?
Required facts: Beacon, columnar
Baseline: retrieval=FAIL, context=FAIL, answer=FAIL; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## beacon-preference

Question: What does user currently prefer for Beacon?
Required facts: weekly demos
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## beacon-comparison

Question: Compare Beacon's original database with the database currently used.
Required facts: MySQL, DuckDB
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## beacon-multi

Question: What are Beacon's current database and architecture, and why?
Required facts: DuckDB, columnar, single-node analytics
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## beacon-provenance

Question: Which session is the source for Beacon's current primary database decision?
Required facts: beacon-session-10
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## beacon-constraint

Question: What constraint caused Beacon's database change?
Required facts: single-node analytics
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## cedar-historical

Question: What database did Cedar originally use?
Required facts: MongoDB
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## cedar-timeline

Question: What did Cedar use originally and what does it use currently?
Required facts: MongoDB, PostgreSQL
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## cedar-project

Question: Which project uses hexagonal architecture?
Required facts: Cedar, hexagonal
Baseline: retrieval=FAIL, context=FAIL, answer=FAIL; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## cedar-preference

Question: What does user currently prefer for Cedar?
Required facts: typed APIs
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## cedar-comparison

Question: Compare Cedar's original database with the database currently used.
Required facts: MongoDB, PostgreSQL
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## cedar-multi

Question: What are Cedar's current database and architecture, and why?
Required facts: PostgreSQL, hexagonal, transaction safety
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## cedar-provenance

Question: Which session is the source for Cedar's current primary database decision?
Required facts: cedar-session-10
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## cedar-constraint

Question: What constraint caused Cedar's database change?
Required facts: transaction safety
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## delta-historical

Question: What database did Delta originally use?
Required facts: SQLite
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## delta-timeline

Question: What did Delta use originally and what does it use currently?
Required facts: SQLite, MySQL
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## delta-project

Question: Which project uses service-oriented architecture?
Required facts: Delta, service-oriented
Baseline: retrieval=FAIL, context=FAIL, answer=FAIL; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## delta-preference

Question: What does user currently prefer for Delta?
Required facts: short reports
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## delta-comparison

Question: Compare Delta's original database with the database currently used.
Required facts: SQLite, MySQL
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## delta-multi

Question: What are Delta's current database and architecture, and why?
Required facts: MySQL, service-oriented, write concurrency
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## delta-provenance

Question: Which session is the source for Delta's current primary database decision?
Required facts: delta-session-10
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## delta-constraint

Question: What constraint caused Delta's database change?
Required facts: write concurrency
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ember-historical

Question: What database did Ember originally use?
Required facts: DuckDB
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ember-timeline

Question: What did Ember use originally and what does it use currently?
Required facts: DuckDB, MongoDB
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ember-project

Question: Which project uses document-driven architecture?
Required facts: Ember, document-driven
Baseline: retrieval=FAIL, context=FAIL, answer=FAIL; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ember-preference

Question: What does user currently prefer for Ember?
Required facts: dark themes
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ember-comparison

Question: Compare Ember's original database with the database currently used.
Required facts: DuckDB, MongoDB
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ember-multi

Question: What are Ember's current database and architecture, and why?
Required facts: MongoDB, document-driven, schema flexibility
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ember-provenance

Question: Which session is the source for Ember's current primary database decision?
Required facts: ember-session-10
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ember-constraint

Question: What constraint caused Ember's database change?
Required facts: schema flexibility
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## forge-historical

Question: What database did Forge originally use?
Required facts: PostgreSQL
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## forge-timeline

Question: What did Forge use originally and what does it use currently?
Required facts: PostgreSQL, DuckDB
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## forge-project

Question: Which project uses pipeline-first architecture?
Required facts: Forge, pipeline-first
Baseline: retrieval=FAIL, context=FAIL, answer=FAIL; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## forge-preference

Question: What does user currently prefer for Forge?
Required facts: Python tooling
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## forge-comparison

Question: Compare Forge's original database with the database currently used.
Required facts: PostgreSQL, DuckDB
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## forge-multi

Question: What are Forge's current database and architecture, and why?
Required facts: DuckDB, pipeline-first, local analytics
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## forge-provenance

Question: Which session is the source for Forge's current primary database decision?
Required facts: forge-session-10
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## forge-constraint

Question: What constraint caused Forge's database change?
Required facts: local analytics
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## grove-historical

Question: What database did Grove originally use?
Required facts: MySQL
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## grove-timeline

Question: What did Grove use originally and what does it use currently?
Required facts: MySQL, SQLite
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## grove-project

Question: Which project uses offline-first architecture?
Required facts: Grove, offline-first
Baseline: retrieval=FAIL, context=FAIL, answer=FAIL; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## grove-preference

Question: What does user currently prefer for Grove?
Required facts: small releases
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## grove-comparison

Question: Compare Grove's original database with the database currently used.
Required facts: MySQL, SQLite
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## grove-multi

Question: What are Grove's current database and architecture, and why?
Required facts: SQLite, offline-first, edge deployment
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## grove-provenance

Question: Which session is the source for Grove's current primary database decision?
Required facts: grove-session-10
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## grove-constraint

Question: What constraint caused Grove's database change?
Required facts: edge deployment
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## harbor-historical

Question: What database did Harbor originally use?
Required facts: MongoDB
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## harbor-timeline

Question: What did Harbor use originally and what does it use currently?
Required facts: MongoDB, PostgreSQL
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## harbor-project

Question: Which project uses layered architecture?
Required facts: Harbor, layered
Baseline: retrieval=FAIL, context=FAIL, answer=FAIL; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## harbor-preference

Question: What does user currently prefer for Harbor?
Required facts: reference docs
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## harbor-comparison

Question: Compare Harbor's original database with the database currently used.
Required facts: MongoDB, PostgreSQL
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## harbor-multi

Question: What are Harbor's current database and architecture, and why?
Required facts: PostgreSQL, layered, auditability
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## harbor-provenance

Question: Which session is the source for Harbor's current primary database decision?
Required facts: harbor-session-10
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## harbor-constraint

Question: What constraint caused Harbor's database change?
Required facts: auditability
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ion-historical

Question: What database did Ion originally use?
Required facts: SQLite
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ion-timeline

Question: What did Ion use originally and what does it use currently?
Required facts: SQLite, MongoDB
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ion-project

Question: Which project uses modular architecture?
Required facts: Ion, modular
Baseline: retrieval=FAIL, context=FAIL, answer=FAIL; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ion-preference

Question: What does user currently prefer for Ion?
Required facts: visual reviews
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ion-comparison

Question: Compare Ion's original database with the database currently used.
Required facts: SQLite, MongoDB
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ion-multi

Question: What are Ion's current database and architecture, and why?
Required facts: MongoDB, modular, rapid schema change
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ion-provenance

Question: Which session is the source for Ion's current primary database decision?
Required facts: ion-session-10
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## ion-constraint

Question: What constraint caused Ion's database change?
Required facts: rapid schema change
Baseline: retrieval=PASS, context=PASS, answer=PASS; attribution=none
Redstone: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure

## juniper-historical

Question: What database did Juniper originally use?
Required facts: DuckDB
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## juniper-decision

Question: What database did Juniper choose and why?
Required facts: MySQL, replication support
Baseline: retrieval=PASS, context=PASS, answer=PASS; attribution=none
Redstone: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure

## juniper-timeline

Question: What did Juniper use originally and what does it use currently?
Required facts: DuckDB, MySQL
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## juniper-preference

Question: What does user currently prefer for Juniper?
Required facts: morning meetings
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## juniper-comparison

Question: Compare Juniper's original database with the database currently used.
Required facts: DuckDB, MySQL
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## juniper-multi

Question: What are Juniper's current database and architecture, and why?
Required facts: MySQL, message-driven, replication support
Baseline: retrieval=FAIL, context=PASS, answer=PASS; attribution=retrieval_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## juniper-provenance

Question: Which session is the source for Juniper's current primary database decision?
Required facts: juniper-session-10
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

## juniper-constraint

Question: What constraint caused Juniper's database change?
Required facts: replication support
Baseline: retrieval=PASS, context=PASS, answer=FAIL; attribution=answer_generation_failure
Redstone: retrieval=PASS, context=PASS, answer=PASS; attribution=none

