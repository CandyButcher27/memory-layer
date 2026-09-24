# Request handling (WSGI/ASGI + middleware)

## Purpose
Turn an incoming WSGI/ASGI request into an `HttpResponse` through settings.MIDDLEWARE and the view.

## Location
`django/core/handlers/base.py` (`BaseHandler`), `wsgi.py`, `asgi.py`, `exception.py`;
URL resolution in `django/urls/`; middleware base in `django/utils/deprecation.py`
(`MiddlewareMixin`).

## Architecture
- `BaseHandler.load_middleware(is_async)` builds the chain **in reverse** over `settings.MIDDLEWARE`,
  starting from `_get_response` (or `_get_response_async`). Each layer is wrapped in
  `convert_exception_to_response`, so a middleware never sees an exception from the inner layer —
  only a response.
- Each middleware declares `sync_capable` (default True) / `async_capable` (default False).
  `adapt_method_mode()` inserts `sync_to_async` / `async_to_sync` wherever adjacent layers differ, so
  mixing modes works but costs a thread hop per switch.
- `process_view` hooks are collected in order; `process_template_response` and `process_exception`
  in reverse. The exception middleware stack is always adapted to **sync**.
- `_get_response`: `resolve_request()` → view middleware → view (wrapped by `make_view_atomic` for
  `ATOMIC_REQUESTS`; it raises for async views with `ATOMIC_REQUESTS`) → `check_response()` (rejects `None`) → template-response middleware → `render()`.
- Sync handler runs async views with `async_to_sync`; async handler runs sync views with
  `sync_to_async(thread_sensitive=True)`.

## Testing
`tests/handlers`, `tests/middleware`, `tests/middleware_exceptions`, `tests/asgi`, `tests/async`,
`tests/urlpatterns_reverse`.
