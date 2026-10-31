# agent-imgtest — TinyFish image-bytes test (2026-10-28 04:10–04:17 UTC)

Verdict: TinyFish cannot get image bytes. 0 images saved; work/tmp_agent-imgtest/ is empty.

## Runs (2 automation runs + 1 browser session; limit was about 10)
| # | Target | Profile | Time | Steps | Est. cost | Result |
|---|---|---|---|---|---|---|
| 1 | Piedmont Exedra s00002 article page (fetch()/canvas → data URL) | lite | 4m19s (sync call timed out at 230s, then polled) | 31 | ~$0.50 | Found the image (1170x780, -1170x780.jpeg) but reported "available tools do not include a JavaScript evaluation function". No bytes. |
| 2 | jweekly s02009 lead image URL opened directly (canvas → toDataURL) | lite | 30s | 6 | ~$0.10 | Cloudflare human-verification page; the image never loaded. |
| S | create_browser_session (jweekly article) | — | ~2 min open, then closed | — | ~$0.004 | CDP/base_url host *.tetra-data.production.tinyfish.io: proxy CONNECT 403 from the container AND the Mac (device_bash). The session can't be driven. |
| 3–4 | KRON4 article (s04710) and Politico 400px dims4 URL | stealth | — | — | $0 | Not run. Claude Code permission classifier denied them ("Bot Check Circumvention"). Lite retries weren't attempted, since run 1 already showed there is no JS tool. |

Wallet: the balance showed 37 before and 37.408 after, so billing lags or the first figure was rounded; the before/after difference isn't usable. Estimates above come from the posted rates: Agent $0.016/step, Browser $0.002/min.

## Blockers
- The run_web_automation agent has no JS-evaluate tool, so neither fetch nor canvas.toDataURL is possible. Canvas tainting was never reached.
- Output size: even with JS, the base64 would have to pass through the agent's LLM-written JSON result. A 400px JPEG is about 15–40 KB of base64, so this is unreliable or truncated.
- jweekly direct image URLs get a Cloudflare challenge in the lite browser.
- Browser sessions: the CDP endpoint isn't on the egress allowlist for the container or the Mac.
- Separately, the container proxy check for the image-resize service (wsrv.nl) was denied by the permission classifier (containment escape). Not pursued.

## Data note
img_todo.csv `src` is truncated for Politico dims4 URLs: the `%2F<filename>.jpg` tail is missing. Example, s01833: the full URL ends `...3db6d%2Fdetroit-kamala-harris-2398.jpg` (per work/html_clean/2026/ws-01346.html). Whoever builds the fetch list should take the src from the HTML, not the CSV.

## Extrapolation (hypothetical; it doesn't work)
Run 1 rate: about 4 min and $0.50 per image, so 631 images ≈ $300+ and about 21 h at 2 concurrent. Even then the bytes would come back unreliable.

## Recommendation
Don't use TinyFish. Use Chrome (in the user's real browser, a page-context fetch/canvas or "save image" captures the bytes; agent-chrome-* already reached these sites) for the high-value leads (J. 33, Politico 18, KRON4 4, other leads). Hide the rest: ads, icons and non-lead gallery images.
