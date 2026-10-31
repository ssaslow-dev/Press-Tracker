# Library gap report (T26, agent-libinventory, 2026-10-27)

Compared every source saved in the new tracker (articles/*.json + manifest, pdf/*, img/*.json, lib/work/texts/tracker) with ~/Desktop/Tracker library (3,497 HTML; ID set checksum-verified against the Mac).

## Tracker sources vs library

| Tracker source | Count | In library? |
|---|---|---|
| articles/*.json saved pages (3,317 codes) | 3,317 | All 3,317 (3,294 under Article IDs, 23 still jg-xxxxxx.html). 472 of them are ProQuest/print-page copies (435 text-only, 37 page-image) |
| pdf/<code>/p*.jpg page images (37 codes, 53 JPGs) | 37 pages | **No.** The 37 library HTMLs are byte-identical to the tracker pages but point at pdf/<code>/pN.jpg, which is not in the library -> blank images |
| pdf/<code>.pdf full print editions (Valley News Group) | 6 | **No** (library holds no PDFs) |
| texts/tracker/<sid>.html (T11 + fetch copies) | 220 | 217 have a library file for the story's Original. 3 do not, but each is another row's page that IS in the library (see below) |
| img/*.json (photos embedded in web pages, `jgimg:` refs) | 3,967 refs in 2,362 pages | Photos inside web pages, not article page images; not copied. Library files contain no `jgimg:` refs (0 on the Mac), so they keep their own image links |

## Prepared in lib/work/library_new/ (index: lib/work/library_new_index.csv)

| fmt | ext | action | files |
|---|---|---|---|
| pq | html | replace | 31 |
| ws | html | replace | 6 |
| ws | pdf | add | 6 |
| **total** | | | **43** (92.9 MB) |

- **add** = no file of this kind in the library (the 6 PDFs).
- **replace** = the library already has this Article ID's HTML (byte-identical to the tracker page) but its page images are missing; the new file is the same page with the JPGs inlined as data URIs, the tracker's PDF-page CSS added, and a one-line "Copy saved from the tracker" note. agent-librename should overwrite the library file with it (or keep both).
- The 6 Valley News Group HTMLs link their PDF as `<old aid>.pdf`; update that link when the PDF is renamed.
- `nb-01307 (jg-d83455).html` mirrors the library name: the log gives nb-01307/jg-00539, the map gives pq-00360/jg-04252 (a duplicate row removed in the FIX). It is a ProQuest page image (fmt pq); its own Article ID needs a decision.
- The 6 PDFs are publisher web PDFs (ws- rows), so fmt = ws, not pq.
- No text-only copies were needed: every ProQuest text copy (435) is already in the library as pq-xxxxx.html.

## Texts copies not added (other rows' pages, already in library)

| Story | Original | texts/tracker copy is the page of | note |
|---|---|---|---|
| jg-00128 | ws-00230 (JTA) | pq-00005 (code jg-11712b, ProQuest print reprint) | reprint row of the same story |
| jg-01508 | ws-01193 (JTA) | ws-01195 (code jg-8423cb) | reprint row of the same story |
| jg-04087 | ws-03775 (AP) | ws-03777 (ABC10 AP copy, code jg-130dec) | reprint row of the same story |

Copying these under the Original's ID would file another outlet's page as the Original. Left for Sammy/coordinator.

## Story coverage (4,195 Original rows)

- own copy: 3,962
- only a reprint row has a copy: 3
- no copy anywhere: 230

"Copy" = a library file (by Article ID / Print Article ID, or a jg-named file of the row's code), a tracker saved page, a T25 NewsBank split PDF, or a file in library_new.

## Stories with no saved copy anywhere (230; also lib/work/library_gap_no_copy.csv)

By source: Tracker scrape 229, ProQuest 1

| Story | Article | Date | Outlet | Headline |
|---|---|---|---|---|
| jg-01776 | ws-01276 | 2026 | LA Progressive | Beware: California Israel Lobby 2026 Agenda |
| jg-01777 | ws-01277 | 2026 | Jewish California | Jewish California Capitol Summit 2026 / AB 715 Lawsuit Panel |
| jg-01795 | ws-01308 | 2023-03 | NBC Boston | California Lawmaker Looks to Ban Chemicals Found in Skittles |
| jg-01796 | ws-01309 | 2023-03 | CBS Los Angeles | On Your Side: Outdoor dining permits costs |
| jg-01821 | ws-01332 | 2026-10-20 | Daily Breeze | immigration |
| jg-01822 | ws-01333 | 2026-10-20 | Pasadena Star-News | immigration |
| jg-01823 | ws-01334 | 2026-10-19 | State Affairs Pro | For California lawmaker leading fight against toxic food additives in schools, it's person |
| jg-01859 | ws-01373 | 2026-10-07 | PublicNow | California Legislative Central Coast Caucus Issues ... |
| jg-01868 | ws-01383 | 2026-10-05 | Bloomberg Law | California Law Takes On Ultra Processed Food: States of Play |
| jg-01874 | ws-01389 | 2026-10-02 | PublicNow | Amid Youth Mental Health Crisis, California and NBA ... |
| jg-01884 | ws-01400 | 2026-10-01 | PublicNow | Governor signs Pacheco bill to strengthen mental health ... |
| jg-01889 | ws-01405 | 2026-09-30 | Organic Consumers Association | New California Law Creates Non-Ultra |
| jg-01893 | ws-01409 | 2026-09-30 | PublicNow | New California Law Protects Affordable Housing from ... |
| jg-01908 | ws-01433 | 2026-09-29 | ABC10 | Newsom signs first-in-the-nation bills targeting federal immigration enforcement in Califo |
| jg-01909 | ws-01435 | 2026-09-29 | ABC10 | California bans law enforcement use of 'shock gloves' and imposes tax on private detention |
| jg-01923 | ws-01452 | 2026-09-29 | PublicNow | California Adopts Comprehensive Strategy to Prevent ... |
| jg-01924 | ws-01453 | 2026-09-29 | PublicNow | New Laws: Assembly Democrats are Leading the Nation in ... |
| jg-01925 | ws-01454 | 2026-09-28 | Bloomberg Law | Newsom Clears First Government Seal for Non-Ultra-Processed Food |
| jg-01926 | ws-01455 | 2026-09-28 | Politico Pro | Newsom adds another MAHA feather to his cap |
| jg-01933 | ws-01462 | 2026-09-28 | PublicNow | California Becomes First State to Create an Official ... |
| jg-01935 | ws-01464 | 2026-09-26 | PublicNow | Building on Success, California Strengthens Its Flagship ... |
| jg-01938 | ws-01469 | 2026-09-25 | State of Israel, The | Newsom Signs Laws Shielding Worshippers From Protesters and Funding Event Security |
| jg-01964 | ws-01498 | 2026-09-20 | Jurisora | Новые законы США: иски о нацистском искусстве из Лос ... |
| jg-01968 | ws-01502 | 2026-09-19 | Washington Post, The | New laws trigger a fresh legal fight over Nazi |
| jg-01970 | ws-01505 | 2026-09-19 | San Antonio Express-News | Nuevas leyes desatan batalla legal en EEUU por arte ... |
| jg-01971 | ws-01506 | 2026-09-18 | State Affairs Pro | Experts say lawmakers should use 'astonishing' pile of cash only as 'last resort' |
| jg-01972 | ws-01507 | 2026-09-18 | State Affairs Pro | California's Record Cash Hoard: Lawmakers Shift Deficit Strategies |
| jg-01976 | ws-01512 | 2026-09-15 | San Francisco Chronicle | CalMatters: How a gym, a farmers market and MMA ... (syndicated) |
| jg-01977 | ws-01513 | 2026-09-15 | Local News Matters | From farmers markets to MMA fighters, state lawmakers ... |
| jg-01995 | ws-01537 | 2026-09-07 | Politico | California just won $2.1B from Meta. Here's how the state |
| jg-01997 | ws-01540 | 2026-09-06 | San Francisco Chronicle | San Jose Spotlight: Bay Area Lawmaker's Bills To Combat ... (syndicated) |
| jg-02003 | ws-01550 | 2026-09-03 | Inner City Law Center | ICLC به عنوان حامی مشترک لایحه پیشگیری از بی‌خانمانی AB ... |
| jg-02004 | ws-01551 | 2026-09-02 | Just Food | California Approves First-In-US State Seal For Non-Ultra-Processed Foods Under AB2244 |
| jg-02009 | ws-01558 | 2026-09-01 | J. The Jewish News of Northern California | California bill to classify Jews as an ethnic group heads to ... |
| jg-02012 | ws-01561 | 2026-09-01 | Davis Vanguard | California Homelessness Prevention Bill Heads to ... |
| jg-02024 | ws-01576 | 2026-08-28 | Politico Pro | Newsom to consider first-of-its-kind seal for non-ultraprocessed foods |
| jg-02026 | ws-01578 | 2026-08-25 | Politico California Playbook | Why California is still fighting over the 2025 vote |
| jg-02036 | ws-01589 | 2026-08-11 | PublicNow | Equality California Condemns Final CMS Rule Blocking ... |
| jg-02056 | ws-01613 | 2026-07-02 | ABC10 | 'Nothing about us without us!' Disability rights advocates, seniors send a message to the  |
| jg-02057 | ws-01614 | 2026-07-02 | ABC10 | Trump DOJ sues California over new gun conversion device law |
| jg-02065 | ws-01623 | 2026-07-01 | PublicNow | California Legislative Central Coast Caucus Announces ... |
| jg-02066 | ws-01624 | 2026-06-30 | State Affairs Pro | Newsom signs $351.7B budget deal with billions for healthcare, housing |
| jg-02072 | ws-01633 | 2026-06-30 | State Affairs Pro | Newsom Signs $351.7 Billion Budget, Funding State Through 2027 |
| jg-02075 | ws-01636 | 2026-06-29 | San Francisco Chronicle | Newsom signs $352B spending plan and reflects on |
| jg-02079 | ws-01640 | 2026-06-26 | CRBC News | DOJ Threatens Lawsuit Over California's New Handgun Sale Restriction - What AB 1127 Means |
| jg-02081 | ws-01642 | 2026-06-26 | PublicNow | California Leaders Announce Balanced Budget Agreement ... |
| jg-02082 | ws-01643 | 2026-06-26 | PublicNow | California Legislature Places Constitutional Amendment to ... |
| jg-02091 | ws-01654 | 2026-06-23 | PublicNow | California State Leaders Announce Historic Constitutional ... |
| jg-02092 | ws-01655 | 2026-06-23 | PublicNow | California leaders announce Save for California's Future ... |
| jg-02093 | ws-01656 | 2026-06-19 | Korea Daily | 행사/모임 |
| jg-02106 | ws-01677 | 2026-06-15 | Politico Pro | California lawmakers approve budget deal |
| jg-02112 | ws-01683 | 2026-06-04 | PublicNow | California State Assembly Democratic Caucus |
| jg-02115 | ws-01686 | 2026-06-03 | Politico | Becerra and Bass surge in California as anti-establishment |
| jg-02119 | ws-01690 | 2026-06-01 | Washington Post, The | The liberal-establishment divides in California's House ... |
| jg-02124 | ws-01694 | 2026-05-29 | Davis Vanguard | Bipartisan Bill Targets California's Failure on Homelessness Prevention |
| jg-02125 | ws-01695 | 2026-05-29 | Politico | State Dems race to tax payouts from Trump's 'anti-weaponization' fund |
| jg-02126 | ws-01697 | 2026-05-28 | Politico | Bass warning signs — and a blue-seat brawl |
| jg-02130 | ws-01704 | 2026-05-27 | Politico Pro | Ultraprocessed food label bill clears Assembly |
| jg-02136 | ws-01713 | 2026-05-20 | Politico | 'The crisis is here and now': Hollywood's anxiety reshapes its political agenda |
| jg-02137 | ws-01714 | 2026-05-19 | J. The Jewish News of Northern California | Jewish groups say San Diego mosque shooting proves need ... |
| jg-02146 | ws-01724 | 2026-05-14 | PublicNow | Budget Chair Jesse Gabriel, Speaker Robert Rivas |
| jg-02152 | ws-01731 | 2026-05-06 | LA Progressive | Los Angeles Progressive Voter Guide |
| jg-02159 | ws-01738 | 2026-04-22 | Politico Pro | New Assembly select committee will focus on young men |
| jg-02217 | ws-01803 | 2026-03-05 | Politico | Keeping Hollywood in LA, and a longshot Dem drops out |
| jg-02227 | ws-01814 | 2026-02-11 | ABC10 | Newsom signs $90M Planned Parenthood funding into law |
| jg-02232 | ws-01820 | 2026-02-04 | Politico Pro | California Democrats take aggressive approach with new anti-ICE bills |
| jg-02238 | ws-01827 | 2026-01-30 | ABC10 | California Democrats pushing wave of bills aimed at limiting ICE activity |
| jg-02239 | ws-01828 | 2026-01-30 | Politico | The Mahan factor and Newsom's shade |
| jg-02242 | ws-01831 | 2026-01-27 | San Francisco Chronicle | CalMatters: California Democrats urge government ... (syndicated) |
| jg-02248 | ws-01838 | 2026-01-26 | Politico Pro | California Dems propose immigration enforcement-resistance bills in response to Minneapoli |
| jg-02262 | ws-01854 | 2026-01-14 | ABC10 | Healthcare advocates criticize Newsom's budget proposal over lack of plan to offset federa |
| jg-02268 | ws-01862 | 2026-01-09 | ABC10 | Newsom unveils final California budget proposal |
| jg-02273 | ws-01867 | 2026-01-05 | Politico | Maduro's capture seeps into the midterms |
| jg-02285 | ws-01878 | 2025-12-15 | Davis Vanguard | California Jewish Caucus Condemns Deadly Hanukkah ... |
| jg-02288 | ws-01881 | 2025-12-12 | Politico | Newsom's star turn and a GOP health care headache |
| jg-02302 | ws-01893 | 2025-11-19 | San Francisco Chronicle | California is facing an $18B deficit |
| jg-02308 | ws-01901 | 2025-10-29 | Davis Vanguard | Millions Face Food Insecurity as Trump Administration ... |
| jg-02333 | ws-01930 | 2025-10-15 | Mixed Times | NRA, Gun Owners of America Vow To Sue California For Passing Glock Gun Ban |
| jg-02342 | ws-01940 | 2025-10-14 | ABC10 | California law seeks to counter antisemitism in schools |
| jg-02345 | ws-01943 | 2025-10-14 | GV Wire | California's Fierce Fight Over Antisemitism in Schools |
| jg-02365 | ws-01969 | 2025-10-10 | GV Wire | California Cuts Red Tape for Restaurant Outdoor Dining ... |
| jg-02366 | ws-01970 | 2025-10-10 | Sacramento Business Journal | California restaurants receive streamlined permitting ... |
| jg-02372 | ws-01975 | 2025-10-09 | ABC10 | California phasing out harmful ultraprocessed foods in schools |
| jg-02386 | ws-01997 | 2025-10-08 | NYC Food Policy Center | Ultra-Processed Foods and All-Cause Mortality: Understanding the Nova Classification |
| jg-02390 | ws-02001 | 2025-10-08 | Politico | Newsom signs ban on 'ultraprocessed' food in California school lunches |
| jg-02391 | ws-02002 | 2025-10-08 | Politico | Held by immigration officials in LA hospital |
| jg-02412 | ws-02027 | 2025-09-17 | Gold Report, The | California passes bill banning junk food in schools—with a catch |
| jg-02418 | ws-02033 | 2025-09-15 | Politico | Farmers' labor plea |
| jg-02419 | ws-02034 | 2025-09-15 | Politico | How Arnold will talk about redistricting |
| jg-02421 | ws-02035 | 2025-09-14 | Davis Vanguard | California Legislature Passes Bill to Combat Antisemitism ... |
| jg-02429 | ws-02045 | 2025-09-09 | Politico | California's '41st senator' is causing climate headaches |
| jg-02454 | ws-02072 | 2025-08-19 | Politico | Scoop: How Dems are preparing to torch a megadonor fighting CA redistricting |
| jg-02456 | ws-02073 | 2025-08-14 | Politico | Congress is lukewarm on RFK Jr.'s plans. In the states, it's a MAHA nation |
| jg-02476 | ws-02092 | 2025-07-09 | Jewish Insider | Trump's burnt Bridge (Daily Kickoff) |
| jg-02477 | ws-02093 | 2025-07-09 | Pasadena Star-News | San Bernardino bishop excuses churchgoers from Sunday ... |
| jg-02480 | ws-02096 | 2025-07-08 | Politico Pro | California lawmakers delay hearing for antisemitism bill amid broad opposition |
| jg-02498 | ws-02121 | 2025-06-19 | Brandon Pena blog | WSJ Global Food Forum 2025: Exclusive Chicago Coverage |
| jg-02500 | ws-02123 | 2025-06-14 | State Affairs Pro | The Legislature passed the budget bill; here are some contentious issues — and what happen |
| jg-02501 | ws-02124 | 2025-06-13 | ABC10 | California lawmakers approve $325 billion budget |
| jg-02504 | ws-02127 | 2025-06-12 | Recorder, The | Restrictions on Legal Aid for Immigrants Slipped Into State ... |
| jg-02508 | ws-02131 | 2025-06-11 | GV Wire | Is a Waxed Apple 'Ultra |
| jg-02509 | ws-02132 | 2025-06-10 | Daily News | Newsom urges Americans to 'not give in to' President ... |
| jg-02513 | ws-02137 | 2025-06-07 | Yahoo News | California bill targeting gun manufacturers passes State Assembly |
| jg-02519 | ws-02143 | 2025-06-04 | Politico Pro | California Assembly advances effort to take on ultraprocessed foods in schools |
| jg-02524 | ws-02153 | 2025-05-31 | Davis Vanguard | AB 690 Targets Flawed Indigent Defense Contracts in ... |
| jg-02529 | ws-02159 | 2025-05-27 | Orange County Register, The | California lawmakers halt hundreds of bills with new ... |
| jg-02538 | ws-02169 | 2025-05-15 | ABC10 | California Handgun Roster: Glocks could be banned for sale |
| jg-02559 | ws-02193 | 2025-05-02 | Gun News Daily | Glock Pistols Face Potential Ban Under New CA Legislation |
| jg-02575 | ws-02212 | 2025-04-09 | Survival World | "DIY Machine Guns": California Aims to Ban Glock Pistols |
| jg-02580 | ws-02216 | 2025-03-31 | J. The Jewish News of Northern California | State grants $5.6M for security to Northern California Jewish orgs amid freeze on FEMA fun |
| jg-02582 | ws-02218 | 2025-03-25 | Politico Pro | California lawmaker says May budget could include cannabis tax freeze |
| jg-02609 | ws-02249 | 2025-03-19 | Wall Street Journal | California Bill Targets Ultraprocessed Foods in School Meals |
| jg-02614 | ws-02254 | 2025-03-14 | Politico | California tries Trump-proofing by another name |
| jg-02621 | ws-02261 | 2025-03-04 | Organic Consumers Association | Bill Shielding Bayer From Cancer Lawsuits Moves Forward |
| jg-02626 | ws-02265 | 2025-02-24 | Politico | California agrees to drop parts of social media law challenged by Elon Musk's X |
| jg-02633 | ws-02273 | 2025-02-19 | Politico Pro | California lawmaker introduces bill to require drinking water limit for 'forever chemicals |
| jg-02641 | ws-02281 | 2025-02-12 | State Affairs Pro | Trump’s federal spending cuts leave California budget officials in the dark |
| jg-02665 | ws-02305 | 2025-01-28 | State Affairs Pro | California lawmakers advance legal aid bills, clash with Trump on wildfire Tours |
| jg-02684 | ws-02324 | 2025-01-16 | Politico | California Trump allies prep for deportation fight |
| jg-02693 | ws-02334 | 2025-01-15 | NBC Los Angeles | FDA bans Red No. 3, artificial coloring used in beverages |
| jg-02706 | ws-02350 | 2025-01-13 | ABC10 | Newsom special 'Trump Proof' session to include proposal for LA fire relief |
| jg-02710 | ws-02353 | 2025-01-12 | Politico Pro | Newsom and legislative leaders strike $50M deal to Trump-proof California |
| jg-02711 | ws-02355 | 2025-01-11 | Davis Vanguard | California Attorney Union Opposes $$ for Private Lawyers ... |
| jg-02716 | ws-02360 | 2025-01-06 | ABC10 | California Legislative session priorities: Affordability and ... |
| jg-02717 | ws-02361 | 2025-01-06 | GV Wire | Five Things to Watch as CA Legislature Returns to Capitol |
| jg-02723 | ws-02367 | 2024-12-30 | J. The Jewish News of Northern California | Decoding the alphabet soup: Acronyms of Jewish life in the Bay Area |
| jg-02725 | ws-02369 | 2024-12-27 | Orange County Register, The | New bill seeks to limit clustered drug rehab centers in ... |
| jg-02734 | ws-02377 | 2024-12-05 | Daily News | Outgoing LA Councilmember Paul Krekorian to help region ... |
| jg-02765 | ws-02407 | 2024-12-02 | GV Wire | Newsom, California Lawmakers to Begin Special Session ... |
| jg-02772 | ws-02421 | 2024-11-20 | ABC10 | California's budget forecasted to be relatively balanced |
| jg-02773 | ws-02422 | 2024-11-19 | Daily News | Los Angeles City Council passes sanctuary city ordinance ... |
| jg-02785 | ws-02435 | 2024-11-06 | J. The Jewish News of Northern California | How Bay Area Jewish candidates fared on Election Day |
| jg-02786 | pq-00131 | 2024-11-05 | Southern California Record, The | New California food dye ban: Is it protection for kids or shady science? |
| jg-02787 | ws-02436 | 2024-11-05 | San Francisco Chronicle | California Election Results and Live Maps |
| jg-02801 | ws-02448 | 2024-10-04 | Orange County Register, The | These 7 new California laws came from 1000 bills Gov. ... |
| jg-02868 | ws-02528 | 2024-09-11 | GV Wire | Trailblazing Les Kimber Honored With Naming of New City ... |
| jg-02877 | ws-02537 | 2024-09-05 | Organic Consumers Association | California Lawmakers Pass Landmark Ban on Toxic Dyes ... |
| jg-02878 | ws-02538 | 2024-09-05 | EdSource | Grade Levels Early Ed |
| jg-02889 | ws-02548 | 2024-09-01 | GV Wire | California to Remove Certain Food Additives from School Meals |
| jg-02930 | ws-02596 | 2024-08-13 | STAT | Q&A: Media mogul Todd Wagner is taking on ultra |
| jg-02954 | ws-02619 | 2024-07-15 | EdSource | UC leaders don't want encampments this fall as lawmakers ... |
| jg-02970 | ws-02632 | 2024-06-28 | Davis Vanguard | Letter: SF Public Defender Applauds Restoration of State's ... |
| jg-02973 | ws-02634 | 2024-06-27 | J. The Jewish News of Northern California | LAPD says it was unprepared for violent protest outside ... |
| jg-02974 | ws-02635 | 2024-06-27 | Sacramento Business Journal | 'Junk fees' exemption for restaurants unanimously passes ... |
| jg-02978 | ws-02639 | 2024-06-26 | ABC10 | California budget slashes spending to address $46B deficit |
| jg-03021 | ws-02693 | 2024-05-17 | GV Wire | Where Do State Lawmakers Stand on War in Gaza ... |
| jg-03030 | ws-02701 | 2024-05-10 | ABC10 | Newsom would slash 10000 vacant state jobs to close deficit |
| jg-03032 | ws-02703 | 2024-05-10 | GV Wire | California Governor Would Slash 10000 Vacant State Jobs ... |
| jg-03033 | ws-02704 | 2024-05-04 | J. The Jewish News of Northern California | Photos of victims adorn California Legislature for Yom HaShoah |
| jg-03035 | ws-02706 | 2024-05-02 | Davis Vanguard | Jewish Caucus Condemns Total Failure by UCLA ... |
| jg-03042 | ws-02712 | 2024-04-26 | Recorder, The | Polarizing Assemblymember Returned to Judiciary ... |
| jg-03052 | ws-02723 | 2024-04-15 | J. The Jewish News of Northern California | This bill could harm the cause of good journalism in California |
| jg-03057 | ws-02727 | 2024-04-11 | Politico Pro | California Legislature sends Gavin Newsom budget deal to ... |
| jg-03070 | ws-02739 | 2024-04-01 | ABC10 | California legislature to enter crunch time |
| jg-03082 | ws-02746 | 2024-03-21 | J. The Jewish News of Northern California | State bill aims to make college campuses safer for Jewish students |
| jg-03119 | ws-02786 | 2024-03-13 | GV Wire | CA Bill Would Ban Flamin' Hot Cheetos & Other Snacks in Public ... |
| jg-03160 | ws-02829 | 2024-01-10 | ABC10 | Newsom to reveal spending plan amid deficit |
| jg-03162 | ws-02831 | 2024-01-10 | GV Wire | Newsom Says Budget Deficit Is $38B, not $68B. His ... |
| jg-03168 | ws-02835 | 2024-01-05 | Troib News | California Jewish Lawmakers Warn Cease-Fire Protest That Shut Down State Assembly Exposed  |
| jg-03169 | ws-02836 | 2024-01-05 | Jewish Insider | Daily Kickoff: WaPo's Israel coverage under fire |
| jg-03179 | ws-02843 | 2023-12-29 | Recorder, The | X Corp. Loses Early Challenge to California's Social Media ... |
| jg-03200 | ws-02863 | 2023-11-27 | GV Wire | Speaker Rivas Shuffles the Leadership Deck and Pro |
| jg-03213 | ws-02875 | 2023-11-21 | J. The Jewish News of Northern California | Pro-Palestinian protests grind California Dems convention to a halt |
| jg-03228 | ws-02888 | 2023-11-08 | Davis Vanguard | Following Antisemitic Incidents on Campuses, California ... |
| jg-03239 | ws-02894 | 2023-10-24 | Sacramento Bee, The | California will ban controversial red dye. Here's when — and 6 Halloween treats that have  |
| jg-03249 | ws-02905 | 2023-10-18 | New York Times, The | What to Know About the 4 Food Additives Banned by ... |
| jg-03254 | ws-02910 | 2023-10-16 | Davis Vanguard | California Becomes First State to Ban Four Toxic Additives ... |
| jg-03267 | ws-02926 | 2023-10-12 | Sacramento Business Journal | Newsom signed 56 bills aimed at addressing the housing ... |
| jg-03303 | ws-02955 | 2023-10-09 | Orange County Register, The | In Norway, OC legislators study potential prison reform ... |
| jg-03318 | ws-02968 | 2023-09-28 | GV Wire | Will CA Gunmakers Go Extinct in a State Where Democrats Don't ... |
| jg-03326 | ws-02975 | 2023-09-26 | Bloomberg Tax | Newsom Enacts Excise Tax on Firearm and Ammunition Purchases |
| jg-03333 | ws-02988 | 2023-09-26 | Wall Street Journal | California Enacts First Statewide Gun and Ammunition Tax ... |
| jg-03380 | ws-03036 | 2023-09-10 | Borneo Bulletin | Elon Musk's social media site X sues California over state's ... |
| jg-03404 | ws-03063 | 2023-09-07 | Orange County Register, The | California lawmakers approve 11% tax for guns and ammunition |
| jg-03405 | ws-03067 | 2023-09-07 | Wall Street Journal | Guns and Ammunition Tax Passed by California Legislature |
| jg-03406 | ws-03068 | 2023-09-07 | GV Wire | Will Newsom Sign California Bill Approving 11% Gun and ... |
| jg-03407 | ws-03069 | 2023-09-05 | Orange County Register, The | How much has Orange County spent this year to lobby ... |
| jg-03415 | ws-03084 | 2023-08-23 | J. The Jewish News of Northern California | State schools chief hears from Jewish leaders about antisemitism in schools |
| jg-03422 | ws-03092 | 2023-07-26 | Recorder, The | Misjudging Mediators: AB 924 Might Cast Too Wide a Net |
| jg-03428 | ws-03103 | 2023-07-17 | GV Wire | CA's Proposed 11% Gun and Ammo Tax Moves Step ... |
| jg-03436 | ws-03111 | 2023-07-06 | Orange County Register, The | California to audit its regulation of addiction treatment ... |
| jg-03457 | ws-03130 | 2023-05-31 | San Francisco Chronicle | California Bills 2023 - Vehicle charging (AB591 bill tracker page) |
| jg-03487 | ws-03164 | 2023-05-08 | J. The Jewish News of Northern California | JIMENA: halt school grants until antisemitism ed is included in plans |
| jg-03512 | ws-03189 | 2023-04-13 | New York Times, The | California and New York Could Ban 5 Food Additives ... |
| jg-03525 | ws-03203 | 2023-04-07 | Daily News | San Fernando Valley lawmaker wants Peeps to change its |
| jg-03595 | ws-03283 | 2023-03-02 | Bloomberg Law | Top California Lawmaker to Focus on Privacy for Abortion, Kids |
| jg-03644 | ws-03327 | 2022-10-06 | J. The Jewish News of Northern California | State legislative roundup: Jewish priorities secured in '21-'22 session |
| jg-03654 | ws-03335 | 2022-09-22 | Local News Matters | Cal State system says it can't afford a staff wage hike even if ... |
| jg-03657 | ws-03338 | 2022-09-19 | JPAC | Governor Signs Community Security Bill |
| jg-03658 | ws-03339 | 2022-09-19 | ABC10 | Cal State says it can't afford a staff wage hike |
| jg-03666 | ws-03346 | 2022-09-14 | Univision | Gobernador Gavin Newsom firma ley AB 587 de “transparencia” para redes sociales en Califor |
| jg-03682 | ws-03363 | 2022-09-07 | Daily News | Sitemap |
| jg-03684 | ws-03365 | 2022-09-07 | Orange County Register, The | Sitemap |
| jg-03690 | ws-03371 | 2022-08-31 | J. The Jewish News of Northern California | ADL urges Newsom to sign hate bill opposed by tech companies |
| jg-03693 | ws-03373 | 2022-08-30 | Davis Vanguard | New CA Measure to Expand California's Gun Violence ... |
| jg-03698 | ws-03378 | 2022-08-15 | J. The Jewish News of Northern California | Sierra Club opens up Israel trips, after canceling under pressure |
| jg-03719 | ws-03398 | 2022-06-11 | Davis Vanguard | Wide Support for Constitutional Amendment to Enshrine ... |
| jg-03720 | ws-03399 | 2022-06-08 | J. The Jewish News of Northern California | $36 million on the table for Holocaust survivors in California |
| jg-03734 | ws-03414 | 2022-05-19 | J. The Jewish News of Northern California | Matt Haney's Jewish roots: public service and doing his grandpa proud |
| jg-03735 | ws-03415 | 2022-05-19 | J. The Jewish News of Northern California | Hundreds descend on Sacramento to lobby for Jewish interests |
| jg-03748 | ws-03427 | 2022-04-18 | J. The Jewish News of Northern California | California earmarks $1.9M for Holocaust and genocide ... |
| jg-03778 | ws-03463 | 2022-03-15 | J. The Jewish News of Northern California | Sierra Club reverses course after canceling trips to Israel |
| jg-03782 | ws-03467 | 2022-02-19 | San Francisco Chronicle | SB1341 |
| jg-03791 | ws-03476 | 2022-01-25 | J. The Jewish News of Northern California | Bay Area Jewish orgs get $4.2M from state's 'target hardening ... |
| jg-03792 | ws-03477 | 2022-01-20 | Press-Enterprise, The | CSU adds ban on caste-based discrimination to system |
| jg-03813 | ws-03497 | 2021-10-26 | Daily News | When ideology collides with reality |
| jg-03838 | ws-03521 | 2021-09-30 | Davis Vanguard | Governor Signs Legislation Attacking Homelessness |
| jg-03839 | ws-03522 | 2021-09-29 | Spectrum News 1 | Newsom signs seven bills aimed at addressing ... |
| jg-03847 | ws-03533 | 2021-09-24 | ABC10 | California 'Al Fresco' dining could be here to stay |
| jg-03849 | ws-03535 | 2021-09-22 | J. The Jewish News of Northern California | Ethnic studies battle has given us insight, and resolve for the long run |
| jg-03853 | ws-03539 | 2021-09-13 | Davis Vanguard | Legislation Would Create Statewide Eviction Defense ... |
| jg-03854 | ws-03540 | 2021-09-11 | Davis Vanguard | Measure Passes Expanding CalFresh Food Benefits for ... |
| jg-03879 | ws-03566 | 2021-07-07 | Crime Stop News | Accused of Murder 2021/3 |
| jg-03887 | ws-03574 | 2021-06-07 | Davis Vanguard | Assembly OK's Bill to Require Courts, Prosecutors to State ... |
| jg-03919 | ws-03605 | 2021-04-01 | J. The Jewish News of Northern California | Ethnic studies: A meaningful victory in a complicated fight |
| jg-03933 | ws-03619 | 2021-02-26 | J. The Jewish News of Northern California | 'Liberated' ethnic studies group launches with help from original California curriculum dr |
| jg-03942 | ws-03627 | 2021-02-03 | GV Wire | Council Hopeful Rakes in Nearly 75 Times More Than ... |
| jg-03949 | ws-03634 | 2021-01-15 | J. The Jewish News of Northern California | Bay Area Jewish orgs urge Congress to protect 'targeted ... |
| jg-03950 | ws-03635 | 2021-01-06 | J. The Jewish News of Northern California | Jewish elected officials react to pro-Trump mobs in D.C. and Sacramento |
| jg-03973 | ws-03660 | 2020-11-03 | CALmatters | Live: California election results 2020 |
| jg-03998 | ws-03685 | 2020-07-24 | J. The Jewish News of Northern California | ADL 'disappointed' by response to alleged anti-Semitic assault on lake |
| jg-04007 | ws-03694 | 2020-06-03 | Politico | Is Hotel California a permanent answer to homelessness? |
| jg-04024 | ws-03708 | 2020-02-24 | J. The Jewish News of Northern California | Driven by values, Jewish legislators get it done in Sacramento |
| jg-04039 | ws-03722 | 2019-10-13 | Politico Pro | Newsom rejects Medi |
| jg-04040 | ws-03723 | 2019-10-13 | Politico Pro | Newsom vetoes bill to put reproductive health info, sex assault ... |
| jg-04055 | ws-03738 | 2019-08-14 | J. The Jewish News of Northern California | Jews 'must be included' in ethnic studies, says state schools ... |
| jg-04068 | ws-03755 | 2019-07-03 | Politico Pro | Bill adding hotlines to student IDs sparks Planned Parenthood debate |
| jg-04080 | ws-03764 | 2019-05-10 | J. The Jewish News of Northern California | Jewish advocates get face-to-face time with Sacramento legislators |
| jg-04085 | ws-03773 | 2019-04-30 | GV Wire | Newsom Aims to Boost Security Grants After Poway Attack |
| jg-04154 | ws-03839 | 2018-04-08 | Sierra Sun Times | Meet Heather Bernikoff Mariposa County District 3 ... |
