# CampusQ — Glass redesign

## Install
1. Back up your current `templates/` folder and `static/css/style.css`.
2. Copy `templates/*.html` over your existing templates (same 12 file names).
3. Replace `static/css/style.css` with the new one. Your old CSS is not needed.
4. Restart Flask. No changes to `app.py` or `database.py` are required.

## What stayed exactly the same
- Every form `method`, `action`, `formaction`, input `name`, hidden input and datalist.
- Every `url_for(...)` endpoint and every variable the templates read from `app.py`.
- JS hooks: `#servingClock`, `#historySearch`, `#historyTableBody`, `#historyResultCount`,
  `printHistoryReport()`, `loadRow()`, `clearForm()`, the `f_*` input IDs, `#f_toggle`,
  `data-*` row attributes, the delete `confirm()`, and the 60-second refresh on My Queue.

## What changed
- **Brand:** CampusQ everywhere, new blue glass logo mark (also used as the browser tab icon).
- **Class names:** fully rebuilt as one design system (`.glass`, `.card`, `.btn--primary`,
  `.field`, `.table`, `.badge--{status}` …). Page scripts were updated to match.
- **Icons:** all text symbols (≡ ◷ ⓘ ♙ ⌕ ↻) replaced with Bootstrap Icons.
- **Fonts:** Instrument Serif (accents) + Plus Jakarta Sans (UI), loaded from Google Fonts.
- **Page titles:** all end in `| CampusQ`.
- **Links fixed:** navbar "Staff login" → `login`; board "Back to student portal" → `get_number`.
- **Dashboard:** stat cards and service cards are now clickable (service card → that service's queue).
- **History:** a "No matching records" row appears when a search finds nothing; the printed
  report uses the new branding.
- **Board:**
  - *Display mode* button: hides navigation, goes full screen, enlarges numbers.
    The choice is remembered per browser. `/board?display=1` or `?display=0` forces it.
  - Refresh now updates the cards in place every 60 s instead of reloading the page,
    so full screen is kept. If the server can't be reached, the last numbers stay up
    and the pill shows "Reconnecting…".
- **Queue statuses:** `waiting`, `serving`, `served` have their own colours, as do
  `cancelled` / `skipped` / `no_show` / `missed` if your `VALID_STATUS` uses them.
  Any other status gets a neutral badge.
