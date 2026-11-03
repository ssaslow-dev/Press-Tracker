# Look and function check: results after TIDY-v1 (2026-11-03)

Run: `run_lookcheck.py` (full: every route and state, both viewports, function parity) against the live v65 files (`live_v65`, workbook sha 0bccc1fc) and a fresh Linux build assembled from the v65 workbook with patches 15 to 18 and the new Tracker files masthead button. Method and the meaning of the columns: README.md, section "TIDY-v1".

## Verdict

- **Exception applied (the live page with the recorded exceptions, TIDY-v1 included, against the PC page): 0 differing pixels, 0 style differences, 0 font-file differences, in all 45 routes and states at 1440x900 and at 960x1040**, with one noise case: `data_hover` at 960x1040 showed 10 pixels (0.001 percent) in the full run and 0 pixels when run alone (the same raster noise as noted for `data_on` earlier; no style, box or text differs).
- **Function parity** (reference side = the live page with the TIDY-v1 patches): 0 differences in every interaction at both sizes (search, dates, facets, sort, saved copies, history, downloads, 69 tab-table steps).
- The PC page asked nothing outside 127.0.0.1 (the console errors listed in `errors.json` are the sandboxed-frame script messages and the container's blocked outside hosts, on the reference side as well).
- **Raw column** (untouched live against PC): no longer 0. It is where TIDY-v1 changed the page on purpose: table header edges and Top issues cells (Reporters, Outlets), Outlets columns at 960 (page height 14261 vs 11571 at 1440 because Top issues are stacked), tab, Filters and badge text 1 px lower (every page: masthead tab row), heading padding, Back/Forward height, Home tile labels, Manage opening on the Update log with 4 tabs, reworded sentences, the Tracker files button. Nothing else differs once the exception is applied (previous column).

### 1440x900

| route / state | page size | differing pixels (exception applied) | % | style differences | font-file differences | differing pixels (raw: untouched live against PC; informational, TIDY-v1 changes) |
|---|---|---|---|---|---|---|
| bill_hover | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 3,204 | 0 of 1,848 | 2559 |
| bill_page | 1440x8472 | 0 of 12,199,680 | 0.0000 | 0 of 3,204 | 0 of 1,848 | 57065 |
| bills | 1440x4913 | 0 of 7,074,720 | 0.0000 | 0 of 1,129 | 0 of 960 | 13658 |
| bills_scrolled | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,129 | 0 of 960 | 2618 |
| clips | 1440x4035 | 0 of 5,810,400 | 0.0000 | 0 of 2,219 | 0 of 1,360 | 73170 |
| clips_badge_station_web | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,026 | 0 of 681 | 7403 |
| clips_f1 | 1440x4219 | 0 of 6,075,360 | 0.0000 | 0 of 2,194 | 0 of 1,322 | 68004 |
| clips_f2 | 1440x3717 | 0 of 5,352,480 | 0.0000 | 0 of 2,030 | 0 of 1,285 | 62811 |
| clips_f3 | 1440x4116 | 0 of 5,927,040 | 0.0000 | 0 of 2,341 | 0 of 1,514 | 88571 |
| clips_scrolled | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 2,219 | 0 of 1,360 | 16674 |
| clips_search | 1440x7452 | 0 of 10,730,880 | 0.0000 | 0 of 2,295 | 0 of 1,436 | 65994 |
| clips_sort_dense | 1440x3216 | 0 of 4,631,040 | 0.0000 | 0 of 1,932 | 0 of 1,302 | 4390 |
| data_hover | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 4,353 | 0 of 2,478 | 2549 |
| data_off | 1440x5791 | 0 of 8,339,040 | 0.0000 | 0 of 4,353 | 0 of 2,478 | 3641 |
| data_on | 1440x5819 | 0 of 8,379,360 | 0.0000 | 0 of 4,386 | 0 of 3,645 | 3650 |
| data_scrolled | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 4,353 | 0 of 2,478 | 2559 |
| home | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 120 | 0 of 259 | 54473 |
| manage | 1440x4035 | 0 of 5,810,400 | 0.0000 | 0 of 2,996 | 0 of 1,813 | 242502 |
| outlets | 1440x11571 | 0 of 16,662,240 | 0.0000 | 0 of 3,774 | 0 of 2,536 | 5712317 |
| outlets_scrolled | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 3,774 | 0 of 2,536 | 118045 |
| release_page | 1440x1091 | 0 of 1,571,040 | 0.0000 | 0 of 389 | 0 of 416 | 7133 |
| release_page_later | 1440x3059 | 0 of 4,404,960 | 0.0000 | 0 of 1,226 | 0 of 890 | 23841 |
| release_page_pick | 1440x1091 | 0 of 1,571,040 | 0.0000 | 0 of 389 | 0 of 416 | 7133 |
| releases | 1440x7479 | 0 of 10,769,760 | 0.0000 | 0 of 2,206 | 0 of 1,571 | 13574 |
| releases_facets | 1440x7479 | 0 of 10,769,760 | 0.0000 | 0 of 2,208 | 0 of 1,572 | 6310 |
| releases_quiet | 1440x4031 | 0 of 5,804,640 | 0.0000 | 0 of 1,455 | 0 of 980 | 5603 |
| releases_quiet7 | 1440x4031 | 0 of 5,804,640 | 0.0000 | 0 of 1,455 | 0 of 980 | 5603 |
| releases_scrolled | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 2,206 | 0 of 1,571 | 2623 |
| reporters | 1440x8554 | 0 of 12,317,760 | 0.0000 | 0 of 2,465 | 0 of 1,431 | 5190492 |
| reporters_scrolled | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 2,465 | 0 of 1,431 | 125168 |
| saved_copy_data | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,573 | 0 of 1,011 | 7594 |
| saved_copy_data_end | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,573 | 0 of 1,011 | 7594 |
| saved_copy_old | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,195 | 0 of 751 | 7490 |
| saved_copy_old_end | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,195 | 0 of 751 | 7490 |
| saved_copy_old_mid | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,195 | 0 of 751 | 7490 |
| saved_copy_old_wide | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,195 | 0 of 751 | 4131 |
| story_av_time | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,148 | 0 of 743 | 7466 |
| story_lang_he | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,141 | 0 of 748 | 9553 |
| story_lang_ko_clip | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,124 | 0 of 724 | 7566 |
| story_lang_zh | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,140 | 0 of 748 | 10698 |
| story_sheet | 1440x4035 | 0 of 5,810,400 | 0.0000 | 0 of 2,292 | 0 of 1,391 | 73331 |
| story_sheet_wide | 1440x4035 | 0 of 5,810,400 | 0.0000 | 0 of 2,292 | 0 of 1,391 | 74898 |
| story_yt_clip | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,113 | 0 of 714 | 5027 |
| travel | 1440x8686 | 0 of 12,507,840 | 0.0000 | 0 of 1,849 | 0 of 1,355 | 71358 |
| travel_scrolled | 1440x900 | 0 of 1,296,000 | 0.0000 | 0 of 1,849 | 0 of 1,355 | 5909 |
| **total** | | **0** | | **0** | **0** | **12297728** |

Function parity at 1440x900:

| interaction | steps compared | differences |
|---|---|---|
| clips_search | 11 | 0 |
| clips_dates | 18 | 0 |
| clips_facets | 22 | 0 |
| clips_sort | 17 | 0 |
| saved_views | 10 | 0 |
| story_sheet | 8 | 0 |
| saved_copy | 5 | 0 |
| team_notes | 6 | 0 |
| history | 14 | 0 |
| hash_routes | 11 | 0 |
| downloads | 11 | 0 |
| tab_tables | 69 | 0 |

### 960x1040

| route / state | page size | differing pixels (exception applied) | % | style differences | font-file differences | differing pixels (raw: untouched live against PC; informational, TIDY-v1 changes) |
|---|---|---|---|---|---|---|
| bill_hover | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 3,202 | 0 of 1,848 | 2510 |
| bill_page | 960x10407 | 0 of 9,990,720 | 0.0000 | 0 of 3,202 | 0 of 1,848 | 55415 |
| bills | 960x5706 | 0 of 5,477,760 | 0.0000 | 0 of 1,127 | 0 of 960 | 13129 |
| bills_scrolled | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,127 | 0 of 960 | 2569 |
| clips | 960x6191 | 0 of 5,943,360 | 0.0000 | 0 of 2,217 | 0 of 1,360 | 72655 |
| clips_badge_station_web | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,024 | 0 of 681 | 6876 |
| clips_f1 | 960x5987 | 0 of 5,747,520 | 0.0000 | 0 of 2,192 | 0 of 1,322 | 67479 |
| clips_f2 | 960x5406 | 0 of 5,189,760 | 0.0000 | 0 of 2,028 | 0 of 1,285 | 62348 |
| clips_f3 | 960x6126 | 0 of 5,880,960 | 0.0000 | 0 of 2,339 | 0 of 1,514 | 88036 |
| clips_scrolled | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 2,217 | 0 of 1,360 | 13169 |
| clips_search | 960x10188 | 0 of 9,780,480 | 0.0000 | 0 of 2,293 | 0 of 1,436 | 65292 |
| clips_sort_dense | 960x3828 | 0 of 3,674,880 | 0.0000 | 0 of 1,930 | 0 of 1,302 | 3862 |
| data_hover | 960x1040 | 10 of 998,400 | 0.0010 | 0 of 4,390 | 0 of 2,496 | 2510 |
| data_off | 960x6800 | 0 of 6,528,000 | 0.0000 | 0 of 4,351 | 0 of 2,478 | 3592 |
| data_on | 960x6828 | 0 of 6,554,880 | 0.0000 | 0 of 4,384 | 0 of 3,645 | 3601 |
| data_scrolled | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 4,351 | 0 of 2,478 | 2500 |
| home | 960x1051 | 0 of 1,008,960 | 0.0000 | 0 of 118 | 0 of 219 | 65296 |
| manage | 960x6191 | 0 of 5,943,360 | 0.0000 | 0 of 2,994 | 0 of 1,813 | 240229 |
| outlets | 960x10374 | 0 of 9,959,040 | 0.0000 | 0 of 2,963 | 0 of 2,536 | 6812579 |
| outlets_scrolled | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 2,963 | 0 of 2,536 | 114471 |
| release_page | 960x1306 | 0 of 1,253,760 | 0.0000 | 0 of 384 | 0 of 416 | 6603 |
| release_page_later | 960x3970 | 0 of 3,811,200 | 0.0000 | 0 of 1,221 | 0 of 890 | 22874 |
| release_page_pick | 960x1306 | 0 of 1,253,760 | 0.0000 | 0 of 384 | 0 of 416 | 6603 |
| releases | 960x9084 | 0 of 8,720,640 | 0.0000 | 0 of 2,204 | 0 of 1,571 | 13044 |
| releases_facets | 960x9084 | 0 of 8,720,640 | 0.0000 | 0 of 2,206 | 0 of 1,572 | 5606 |
| releases_quiet | 960x4828 | 0 of 4,634,880 | 0.0000 | 0 of 1,453 | 0 of 980 | 4899 |
| releases_quiet7 | 960x4828 | 0 of 4,634,880 | 0.0000 | 0 of 1,453 | 0 of 980 | 4899 |
| releases_scrolled | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 2,204 | 0 of 1,571 | 2573 |
| reporters | 960x8614 | 0 of 8,269,440 | 0.0000 | 0 of 2,261 | 0 of 1,431 | 974812 |
| reporters_scrolled | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 2,261 | 0 of 1,431 | 98228 |
| saved_copy_data | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,568 | 0 of 1,011 | 5367 |
| saved_copy_data_end | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,568 | 0 of 1,011 | 5367 |
| saved_copy_old | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,190 | 0 of 751 | 5505 |
| saved_copy_old_end | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,190 | 0 of 751 | 5505 |
| saved_copy_old_mid | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,190 | 0 of 751 | 5505 |
| saved_copy_old_wide | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,190 | 0 of 751 | 5505 |
| story_av_time | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,143 | 0 of 743 | 5538 |
| story_lang_he | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,136 | 0 of 748 | 9306 |
| story_lang_ko_clip | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,119 | 0 of 724 | 5500 |
| story_lang_zh | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,135 | 0 of 748 | 8364 |
| story_sheet | 960x6191 | 0 of 5,943,360 | 0.0000 | 0 of 2,287 | 0 of 1,391 | 67142 |
| story_sheet_wide | 960x6191 | 0 of 5,943,360 | 0.0000 | 0 of 2,287 | 0 of 1,391 | 67142 |
| story_yt_clip | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,108 | 0 of 714 | 4802 |
| travel | 960x9891 | 0 of 9,495,360 | 0.0000 | 0 of 1,847 | 0 of 1,355 | 70844 |
| travel_scrolled | 960x1040 | 0 of 998,400 | 0.0000 | 0 of 1,847 | 0 of 1,355 | 6850 |
| **total** | | **10** | | **0** | **0** | **9116501** |

Function parity at 960x1040:

| interaction | steps compared | differences |
|---|---|---|
| clips_search | 11 | 0 |
| clips_dates | 18 | 0 |
| clips_facets | 22 | 0 |
| clips_sort | 17 | 0 |
| saved_views | 10 | 0 |
| story_sheet | 8 | 0 |
| saved_copy | 5 | 0 |
| team_notes | 6 | 0 |
| history | 14 | 0 |
| hash_routes | 11 | 0 |
| downloads | 11 | 0 |
| tab_tables | 69 | 0 |

