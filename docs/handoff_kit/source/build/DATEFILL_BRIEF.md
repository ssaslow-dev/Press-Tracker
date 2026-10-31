# DATEFILL: fill incomplete dates, plus other blanks on the same rows (Sammy 2026-10-28)
L = /tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib. Source: L/work/coverage_current.xlsx, Coverage tab (master 4d7fb37c…; rp-final may commit a newer master soon, so re-read it before the write).

Rows whose Date isn't a full YYYY-MM-DD, about 687 in all:
- **Group A** (agent df-orig): 22 Originals with YYYY-MM, 6 with YYYY only, 3 blank Originals (02356, 09773, 09774), and 1 Reprint with YYYY-MM (06925). Total 32.
- **Group B** (agent df-linked): 94 "Reprint" rows with a blank date that HAVE a Publisher link.
- **Group C** (agent df-unlinked): 561 "Reprint (unverified)" rows with a blank date and NO link (old "Tracker reprint list" rows). Find the outlet's own copy of the story: search outlet + the Original's headline, around the Original's date.

## Rules (from DECISIONS; read README, DECISIONS, HANDOFF §3)
- **Tools:** TinyFish search and fetch_content are free; use those. Browser automation costs money, so use it sparingly. Deep research and Exa are not allowed. Don't work around paywalls, Cloudflare or logins.
- **Dates:** take the date the page itself states (byline date, `article:published_time`, JSON-LD `datePublished`). Never use a save, crawl or "updated" date unless it's the only date and clearly the publish date. Station video pages never date a row (AVTAB-v3): leave those blank with a note. For print, use the edition date.
- **Fill blanks only:** Headline, Author/byline (people only; Author title rule), Publisher link, Link status, Section, Word count, Medium/Reach/Language (copy from the same outlet's rows), Translated Headline/Story in English for non-English pages (translate), and Mentions "Gabriel" in text. Never overwrite a filled cell, unless the cell is plainly wrong and you list it separately as a proposed correction.
- **Reprint check:** for a found reprint page, run the text rule (code/reprint_rule.py: runs of 25 or more words covering at least 90% of both texts) against the Original's saved text.
  - Pass: it can become "Reprint" (verified) and count.
  - Fail: list it as "not the same text". Don't regroup; report it.
  - No text to test: keep "Reprint (unverified)".
- **Saved copies:** save each found page's cleaned HTML (code/clean_html.py) to L/work/tmp_datefill/pages/<ArticleID>.html, for the writer to add to the library.
- **Not found:** the row stays as is, with the attempt recorded in the "Search lookup" column convention, e.g. "Not found (Oct 28)".
- **Output:** L/work/tmp_datefill/<group>.csv, one row per change: Article ID, column, old, new, source URL, evidence (quote of the date line), confidence (high/med). Only high-confidence values get written; medium ones go to a review list.
- **No sheet writes by researchers.** The writer (df-write) does one rule-7 write after rp-final's commit (token "none", re-stage the current master), and updates HANDOFF and DECISIONS.
- Log in status/agent-<name>.md.

## CHANGE (Sammy): Group C (unverified reprints) SKIPPED — df-unlinked stopped; any partial output in work/tmp_datefill/C* is discarded, not written.

## Writer df-write (later): ONE rule-7 write combining Group A + B datefill CSVs and work/tmp_uv/changes.csv (+ library copies, Removed moves, # of reprints recompute, Originals mirror, AV rows, review-queue items cat "uvreprint"), after rp-final's commit.

## Group A done (work/tmp_datefill/groupA.csv). Coordinator rulings for df-write: write the 19 high-confidence dates + 3 field fills; APPLY corrections 06915 (→2026-03-25) and 06933 (→2024-10-02) (page JSON-LD contradicts the partial month — plainly wrong); APPLY 06925 fold into 01537 (same outlet edition: Publisher link onto 01537 if blank, 06925 → Removed "2 duplicate", recompute counts); medium ones (06913, 06918, 06916 date+author, 06939, 06952) → review queue cat "dates"; not-found 8 get "Not found (Oct 28)". 06912 (URL no longer mentions Gabriel) → review queue.

## Group B done (work/tmp_datefill/B*.csv). Coordinator rulings for df-write: write B.csv (477 high); B_review.csv (6) → review queue cat "dates"; corrections APPLY: 03183 Link status dead + label "Reprint (unverified)" (no text to test, per rule), 08959 label "Reprint (unverified)" + byline fix to page's "Food & Wine" only if Author cell rule allows (people only → leave author, note), 08145 Language Spanish + Author Robin Foster, 08144 Author Robin Foster; QUEUE (cat "regroup"): the 5 text-rule fails (05360, 07141, 01063, 02101, 04662) and HealthDay-as-Original for s(08144); reprints dated a day before their Original (00695, 03221, 04119, 04183, 05035) → note only (time-zone/edition), no change.
