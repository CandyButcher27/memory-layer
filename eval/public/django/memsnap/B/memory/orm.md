# ORM query pipeline

## Purpose
Turn chained `QuerySet` calls into SQL and rows into model instances.

## Location
- `django/db/models/query.py` — `QuerySet`, iterable classes, `Prefetch`, `RelatedPopulator`
- `django/db/models/sql/query.py` — `Query`: the SQL-independent query tree (joins, where, annotations)
- `django/db/models/sql/compiler.py` — `SQLCompiler` + Insert/Delete/Update/Aggregate compilers
- `django/db/models/expressions.py`, `lookups.py`, `query_utils.py` (Q, `RegisterLookupMixin`)
- `django/db/models/base.py` (`ModelBase` metaclass, `Model`), `options.py` (`_meta`)
- `django/db/models/fetch_modes.py` — deferred/related field fetch policies

## Architecture
1. **QuerySet is lazy and immutable-by-convention.** Every chaining method calls `_chain()` →
   `_clone()`, which copies the QuerySet and calls `query.chain()`. Any new QuerySet attribute must
   be copied in `_clone()` or it silently resets on the next chained call. `_disable_cloning()`
   (`PreventQuerySetCloning`) lets internal code mutate in place for performance.
2. `filter()/exclude()` → `Query.add_q()` → `_add_q()` → `build_filter()`, which resolves
   `a__b__c` via `names_to_path()` / `setup_joins()` / `trim_joins()` and builds a lookup via
   `build_lookup()`. Multi-valued excludes go through `split_exclude()` (subquery).
3. Evaluation: `_fetch_all()` fills `_result_cache` from `self._iterable_class(self)`
   (`ModelIterable`, `ValuesIterable`, `ValuesListIterable`, `FlatValuesListIterable`, …), then runs
   prefetches.
4. `Query.get_compiler(using)` → `connection.ops.compiler(self.compiler)` — the compiler class is
   looked up by name in the backend's `compiler_module` (MySQL and PostgreSQL override it), so
   backends can subclass compilers.
5. `SQLCompiler.compile(node)` calls `node.as_<vendor>(compiler, connection)` if defined, else
   `node.as_sql(...)`. This is the per-database override hook for expressions/lookups.

## Interfaces
- Expressions implement `resolve_expression()` (bind to a Query, resolve F()/OuterRef),
  `get_source_expressions()`, `as_sql()`, `get_group_by_cols()`, `select_format()`.
- Lookups/transforms register on fields via `RegisterLookupMixin.register_lookup`.
- **Fetch modes** (`FETCH_ONE` default, `FETCH_PEERS`, `FETCH_RAISE`) control what happens on access
  to a not-loaded deferred field or related object; set via `QuerySet.fetch_mode()` and carried
  into `from_db()`/`RelatedPopulator`. `FETCH_PEERS` batches the fetch across instances loaded by
  the same query (`instance._state.peers`).

## Important Constraints
- `Model.from_db()` without a `fetch_mode` argument is on a `RemovedInDjango2028Warning` path
  (`_get_from_db()` in `query.py`).
- `Query.__deepcopy__` returns `clone()` deliberately to bound copying cost.

## Testing
`tests/queries`, `tests/expressions`, `tests/lookup`, `tests/aggregation`, `tests/annotations`,
`tests/prefetch_related`, `tests/select_related`, `tests/defer`, `tests/basic`.
