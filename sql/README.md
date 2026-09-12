# SQL analysis

If I make a mistake and need to start fresh:

rm local_data/nesc_weather.db
sqlite3 local_data/nesc_weather.db < sql/0_schema.sql

_________

This directory is reserved for readable SQL queries against the generated SQLite weather database.

Planned progression:

- basic exploration and QA
- freezing-liquid conditions
- wet-snow conditions
- in-cloud / rime-icing potential
- cold high-wind exposure
- later event-based analyses

KPI definitions belong here rather than in the database-building layer whenever practical.
