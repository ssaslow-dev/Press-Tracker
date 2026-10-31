# leginfo + TinyFish probe: discovering Gabriel's 2025-26 bills

Probed 2026-10-27. 9 TinyFish calls (8 `fetch_content`, 1 `run_web_automation`). No Exa.

## Recommendation

One `fetch_content` call on the leginfo author search. It is the same URL the Assembly's own member page (assembly.ca.gov/assemblymembers/46) links to as "Authored Bills".

```
mcp__TinyFish__fetch_content({
  urls: ["https://leginfo.legislature.ca.gov/faces/billSearchClient.xhtml?session_year=20252026&house=Both&author=Gabriel&lawCode=All"],
  format: "markdown",            // or "html"; both parse cleanly
  links: true,                   // gives billNavClient bill_id URLs in row order
  include_selectors: ["#bill_results"],
  ttl: 0,                        // force live; default ttl may serve cache
  per_url_timeout_ms: 90000,
  image_links: false, iframe_links: false, page_metadata: false
})
```

URL template: `https://leginfo.legislature.ca.gov/faces/billSearchClient.xhtml?session_year={YYYY}{YYYY+1}&house=Both&author=Gabriel&lawCode=All`

- Latency: 2.7 s, 3.1 s, 2.9 s on three live runs. All 89 rows came back on one page, with no pagination.
- Covers the regular session and the 1st Extraordinary Session (ABX1-*) together.
- The result matches the 2025-26 `role: author` rows in `gabriel_bills_leginfo.json` exactly: 89 vs 89, with nothing new and nothing missing.

### Parsing notes
- With `include_selectors:["#bill_results"]` and markdown format, the text is just the table. Columns: `Measure | Subject | Author | Status`.
- Measure uses a hyphen form: `AB-1264`, `ABX1-1`, `ACA-20`, `ACR-195`, `HR-18`. To match the JSON `bill` key, apply `measure.replace('-', ' ')` to regular bills. Keep `ABX1-1` and `SBX1-1` as they are, since the JSON already stores those with hyphens.
- Subject is blank for HR resolutions (HR-18/29/60/90).
- `links[]` comes back in the same order as the table rows: `billNavClient.xhtml?bill_id={session}{X}{TYPE}{NUM}`. X is 0 for the regular session and 1 for the 1st Extraordinary, e.g. `202520261AB1` = ABX1-1. To get the status page, swap `billNavClient` for `billStatusClient`. The JSON's `url` field uses the status page.
- Session label: the bill_id flag of `1` means `2025-2026 (1st Ex. Sess.)`; otherwise `2025-2026`.
- Without the selector, the markdown starts with `Bills Returned: N`. Use that as a completeness check if you skip the selector. With the selector, compare the row count against `links.length`.
- Every row's Author column is `Gabriel`, so every row is role `author`.
- In html format the `<td>` for Measure has trailing whitespace and newlines inside the `<a>`, so strip it.

### Sample parsed output
```json
[
 {"measure":"ABX1-1","bill":"ABX1-1","session":"2025-2026 (1st Ex. Sess.)","title":"Budget Act of 2024.","status":"Assembly - Died - Budget","role":"author","bill_id":"202520261AB1"},
 {"measure":"AB-1127","bill":"AB 1127","session":"2025-2026","title":"Firearms: converter pistols.","status":"Chaptered","role":"author","bill_id":"202520260AB1127"},
 {"measure":"AB-1264","bill":"AB 1264","session":"2025-2026","title":"Pupil nutrition: restricted school foods and ultraprocessed foods of concern: prohibition.","status":"Chaptered","role":"author","bill_id":"202520260AB1264"},
 {"measure":"AB-2750","bill":"AB 2750","session":"2025-2026","title":"Development projects.","status":"Assembly - Pending Referral","role":"author","bill_id":"202520260AB2750"},
 {"measure":"HR-18","bill":"HR 18","session":"2025-2026","title":"","status":"Assembly - Passed","role":"author","bill_id":"202520260HR18"}
]
```

## Known blind spot: the author search only matches the FIRST-listed lead author
- AB 1127 (lead authors "Gabriel, Stefani") IS returned.
- AB 671 (lead authors "Wicks, Gabriel") is NOT returned, even though the status page lists Gabriel as a lead author.
- So the search misses all 17 non-`author` 2025-26 rows in the JSON: co-lead bills (AB 671, AB 1665, SBX1-1..4), principal coauthor bills (AB 715, AB 1468), and coauthor bills (AB 1709, AB 1853, AB 2017, AB 2156, AB 2664, AB 770, SB 281, SB 411, SB 417).
- Leginfo has no URL-addressable coauthor search. Suggested handling: the Update check diffs only `role=author` rows against the search. For known co-lead and coauthor bills it re-fetches their status pages if a status refresh is wanted. Discovering *new* co-lead or coauthor bills is not possible from the search.

## Definitional note: Committee on Budget bills
Keyword search surfaced AB-155, AB-159 and AB-162. Their status pages list the lead author as "Committee on Budget (A) - (Assembly Members Gabriel (Chair), Addis, ...)". These are not in the JSON and not in the author search. They are budget trailer bills where Gabriel acts as chair. Whether the tracker should count them is a policy call for Sammy, not a parser bug. Searching `author=Committee%20on%20Budget` returned `bot_blocked` once, so it is untested.

## Other approaches tried
| Approach | Call | Result |
|---|---|---|
| Per-bill status page | `fetch_content` on `billStatusClient.xhtml?bill_id=202520260AB1264` (also AB1127, AB671, AB162) | Readable, about 2.2-2.8 s each, batchable up to 10 per call. Fields: Measure, Lead Authors (ordered, house-tagged), Principal Coauthors, Coauthors, Topic, Title (act text), House Location, Chaptered/Last Amended dates, Type of Measure, last 5 history actions. Best for verification and status, but needs bill numbers already in hand, so it can't discover bills. |
| Member site `a46.asmdc.org/legislation` | fetch | 404. `a46.asmdc.org` redirects to `gabriel.asmdc.org` (7.9 s). |
| `gabriel.asmdc.org/legislative-summary` | fetch | Readable but stale: only 14 bills, all from **2023-24** (AB 2316...AB 3160). Unusable for the current session. Press releases on the home page mention current bills in prose only. |
| Assembly member page `www.assembly.ca.gov/assemblymembers/46` | fetch (0.8 s) | No bill list of its own. Its "Authored Bills" link is exactly the recommended leginfo search URL. |
| Leginfo keyword search `...&keyword=Gabriel` | fetch (2.3 s / 7.1 s) | Noisy: 76 hits, mostly "San Gabriel Valley". Paginated 10 per page via a JSF postback, so pages aren't addressable by URL. Not usable. |
| `run_web_automation` on the author search URL (lite, 240 s cap, output_schema) | | **Timed out at 230 s** with no result, and the run may still be billed. Not needed, since plain fetch returns the full table in about 3 s. |

## Failure modes to handle in the Update button
- A `bot_blocked` per-URL error occurred once (on the Committee-on-Budget author param). Retry once, then surface "leginfo unavailable" rather than treating an empty list as "no bills".
- Treat 0 rows as an error, not as a valid empty result.
- Pass `ttl: 0` so cached results aren't served.
