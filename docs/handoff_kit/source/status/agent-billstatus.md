# agent-billstatus — leginfo milestone dates for Gabriel author/co-lead bills
Started 2026-10-27. Data only; no tracker code edits, no publish. No Exa.
- Scope: role == author or author (co-lead...) in work/gabriel_bills_leginfo.json (all sessions); coauthor/principal coauthor skipped.
- Method: history page (billHistoryClient) holds full dated action list; status page only shows last 5 actions, so history only. Raw results extracted from transcript to work/billstatus_cache/ by code/billstatus/extract.py.
- batches 1-8 done (8 calls); bot_blocked so far: AB2236, AB2617, AB3147 (19-20), AB766, AB1664, AB1991 (21-22) -> retry at end
- batches 9-14 done (14 calls)
- batches 15-22 done (22 calls)
- batches 23-28 + retry 1 done (28 calls)
- retry 2 done (31 calls total). All 273 history pages cached; 0 failures.
- DONE. 273/273 bills parsed (code/billstatus/parse.py) -> work/out/bill_milestones.json (per bill: milestones[{date,step,house,committee,detail}], final_status, tracker_articles/stories) and work/out/bill_milestones.csv (1,895 milestone rows).
- Final status: Chaptered 99 (87 statutes + 12 resolutions), Vetoed 12, Adopted (HR) 19, Died 93, Held in committee 4, On inactive file 4, Pending 42 (2025-26). Chaptered status matches the list's status for every bill.
- Caveats: committee name is inferred from the referral order (history lines say only "From committee:"); committee-vote date = hearing date in parentheses. Coauthor-only bills are skipped, so tracker Bills values SB 1524, AB 715, SB 2, SB 542 (coauthor) and AB 473/301/521 (not in the list) don't match a row.
- 31 TinyFish fetch_content calls (2 per minute or fewer). No Exa. No tracker code edits, no publish.
