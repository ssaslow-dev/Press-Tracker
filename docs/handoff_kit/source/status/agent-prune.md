# agent-prune log
- Tue Oct 27 16:48:25 UTC 2026 phase1 start (read-only)
- Live listing: v8 1793119028-42ac, 109 files, 263,269,308 B. Local build/pub shas = manifest (39/39). Live img/0-15,100 downloaded to final_pass/F7/live (img/100 sha = manifest).
- Refs scanned: index.html (0 jgimg, 0 pdf/), 23 articles/*.json (2,434 jgimg refs all resolve in their named shard; 33 pdf/*.jpg refs), sheet.json (0), pipeline (legacy_index.html is build_data.py OLDHTML arg -> keep), db pages/clips collections empty. img_map_F4.json: 3,287 targets, 916 not in any copy (incl. 3 pdf jpgs).
- Plan (img_map counts): remove 6 PDFs + 11 page jpgs (41.9 MB); repack img/3 (8.01 -> 6.57 MB, keeps 192/224, verified byte-equal values); other shards keep (savings <0.27 MB each). Freed 43,347,152 B -> 219,922,156 B.
- Alt (copies only): freed 79.5 MB -> 183.8 MB, needs 91.2 MB re-upload (2 publishes). Files in F7/repack_copies_only.
- Phase 1 done; NOT published. Waiting for go.
- Coordinator: no Phase 2 publish by me; files map written to F7/files_map.json (17 null + img/3 repack) for agent-final-F4's combined publish. Stopped.
