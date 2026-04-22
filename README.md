# Turbo Market Maker Live App

## Project goal

This project is a live monitoring application for a turbo / structured products market maker desk.

The main goal is to build a fast, maintainable, and extensible PySide6 desktop app that can:

- monitor live trading logs coming from SQL polling,
- show a dense but useful live overview,
- highlight important market-making activity,
- keep the first tab live and responsive,
- keep the rest of the tabs available for future batch-only analysis.

Priority order:

1. Performance
2. Clarity / maintainability
3. Usability
4. Looks

## Tech constraints

- Python 3.12
- PySide6
- pandas
- numpy
- cProfile
- CPython
- standard libraries preferred
- no unusual external dependencies

## Core design principles

### Heavy startup is acceptable
The app may take time at startup. This is intentional.

At startup, the app can:
- batch-load previous session data,
- compute historical baselines,
- load today's data from early morning until now,
- build caches and live-ready aggregates.

### Runtime responsiveness is critical
Once the app is open, the live tab must remain fast.

This means:
- incremental updates,
- limited recomputation,
- lightweight rendering,
- cheap filters only where justified.

### Only the first tab is live
The Live Overview tab is the only tab that receives periodic live updates.

All other tabs are placeholders for future analysis and should:
- not poll,
- not consume live resources,
- freeze live polling when selected.

### Maintainability matters
The code is split into clear layers so that:
- fake data can be replaced by real SQL easily,
- metrics can be extended later,
- tabs can be added safely,
- logic can be profiled and optimized independently.

## Data assumptions

- The SQL source is append-only.
- Each row has a unique alphanumeric identifier.
- `Time` is the true event timestamp.
- Slightly delayed rows are possible.
- All events are rows in the same structure.
- `Action` determines event meaning (`TradeOK`, `QuoteOK`, etc.).
- Many columns may exist, but only a subset is needed for live monitoring.

## Live app concept

### Live behavior
The app should:
- batch-load the last 14 days for baseline comparisons,
- batch-load today from around 02:00 until current time,
- start polling periodically,
- update only the live tab,
- pause polling when leaving the live tab,
- resume from the last successful cursor when returning.

### Cursor philosophy
Polling should always continue from the last successful cursor.

A small overlap / buffer is recommended to protect against late rows:
- poll from `last_successful_time - small_buffer`,
- deduplicate by unique row id.

## Planned UI structure

1. Live Overview
2. Trade Log *(placeholder)*
3. Pair Trades *(placeholder)*
4. KO / Product Events *(placeholder)*
5. Underlying Analysis *(placeholder)*
6. Counterparty Analysis *(placeholder)*
7. Debug / Profiling *(placeholder)*

Only Live Overview is active in MVP.

## Live Overview tab

### Top control bar
- Run / Freeze
- polling interval
- last update indicator
- include quotes toggle
- simple quick filters

### KPI / summary area
Examples of useful live blocks:
- total rows in view
- trade count
- quote count
- total quantity
- cumulative quantity vs 14d baseline
- cumulative trades vs 14d baseline
- pair-trade PnL summary (dummy adapter for now)
- biggest flow summary

### Ranking / curve area
Examples:
- top underlyings by quantity
- top WKNs by quantity
- cumulative trades vs historical baseline
- cumulative quantity vs historical baseline

### Live table + detail panel
- left side: fast live table with a reduced number of columns
- right side: detail view of the selected row

## Filtering philosophy

Filtering must remain useful without damaging performance.

### Cheap filters acceptable for live MVP
- include quotes on/off
- action filter
- category filter
- side filter
- WKN text filter
- underlying text filter

Recommendation:
- global cheap filters for selected KPIs / rankings,
- table-only filters for more specific exploration.

## Historical comparison philosophy

Initial plan:
- use last 14 days,
- build 5-minute buckets,
- compute cumulative quantity and cumulative trade count,
- compare the current session against the historical average curve.

## Pair trade / toxic flow integration

The real pair-trade logic already exists outside this app.

For now, the app uses a dummy adapter with the same future interface.

The UI should only consume outputs such as:
- highlighted WKNs,
- pair-trade PnL for selected windows,
- pair counts.

## Performance strategy

### Main performance ideas
- preload aggressively at startup,
- keep historical baselines frozen per session,
- use incremental live updates,
- avoid full recomputation on every poll,
- keep charts lightweight,
- use model/view widgets for tables,
- limit heavy filtering on live KPIs.

### Expected scale
- around 30 columns in raw data,
- around 10 columns important for live,
- around 60k–100k rows per day.

### Profiling
cProfile should be integrated early so we can measure:
- startup time,
- polling cycle time,
- aggregation cost,
- UI refresh cost.

## Proposed code structure

```text
app/
    main.py

    core/
        app_controller.py
        live_session.py
        state.py
        cursor_state.py
        profiler.py

    data/
        feed_interface.py
        fake_feed.py
        sql_feed.py
        schemas.py
        row_normalizer.py

    engines/
        historical_engine.py
        live_engine.py
        filter_engine.py
        ranking_engine.py
        pairtrade_adapter.py

    ui/
        main_window.py
        tabs/
            live_overview_tab.py
            analysis_tab_stub.py
            pair_tab_stub.py
            ko_tab_stub.py
        widgets/
            kpi_card.py
            live_table.py
            detail_panel.py
            ranking_panel.py
            filter_bar.py
            curve_panel.py
            status_bar.py

    utils/
        time_buckets.py
        dataframe_utils.py
        qt_helpers.py
        constants.py
```

## Development plan

### Phase 1 — architecture only
- define folder structure
- define feed interface
- define state objects
- define snapshot model
- define live tab responsibilities

### Phase 2 — fake data MVP
- fake batch history loader
- fake today loader
- fake poller
- basic live overview layout
- live table + detail panel
- simple KPIs and rankings

### Phase 3 — live engine
- incremental aggregates
- 14d bucket baseline
- cursor state
- run / freeze behavior
- auto-pause when leaving live tab

### Phase 4 — real integration
- replace fake feed with SQL module
- connect real pair-trade module
- profile and optimize

### Phase 5 — future analysis tabs
- implement batch-only tabs one by one

## Current MVP boundaries

Included in MVP:
- one real live tab
- placeholder extra tabs
- batch startup load
- polling live updates
- top KPIs
- ranking blocks
- live event table
- detail panel
- dummy pair-trade integration

Not included yet:
- export from live tab
- persistent settings
- deep quote analytics
- KO logic
- rich charting
- complex multidimensional KPI filtering

## Notes for future contributors

When extending the project:
- do not put SQL logic directly into UI code,
- do not put heavy pandas logic in the UI thread,
- keep the pair-trade engine behind an adapter,
- prefer incremental state updates over full recomputation,
- keep the live tab strict and performance-first,
- treat all non-live tabs as separate analysis tools.
