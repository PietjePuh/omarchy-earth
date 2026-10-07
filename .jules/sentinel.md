## 2024-10-07 - Cross-Site Scripting (XSS) in Map Search
**Vulnerability:** User input from search queries (`q`) in `web/earth.html` is directly interpolated into DOM elements (`searchResults.innerHTML`) when no results are found.
**Learning:** Even internal mapping tools often overlook basic escaping of search terms when displaying "No results for X".
**Prevention:** Always use a dedicated HTML escape function (like `newsEscapeHtml` which was already present in the codebase) for all user input rendered into the DOM via `innerHTML`, or use `textContent` where applicable.
