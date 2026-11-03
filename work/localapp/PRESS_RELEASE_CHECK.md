# Press release check (read-only; nothing in the workbook was changed)

For Sammy. Question: which rows on release wires, or that are plainly release text, are NOT marked Press release = Yes?

**Data used.** Workbook copy dated 2026-11-03 (sha256 starts 0bccc1fc). Saved text came from the library snapshot dated 2026-10-31, with the live tracker's article files as a fallback, so a few of the newest rows may have no text (marked "no saved text"). Each row was judged from its own text (PRJUDGE-v1), not from the outlet name alone. Verdicts rest on the opening text and release signals; open a few before bulk-marking.

## Counts

- Coverage rows: 8222. Marked Yes: 527. Marked No: 24. Blank: 7671.
- Not-Yes rows I examined (wire-type outlet, release web host, release wording in the text, copy of his office's release, or an outlet that already has many Yes rows): **414**.
- **Likely releases not marked: 82** (18 of them flagged "less certain"; give those a second look).
- **Unsure: 28** (no saved text, or a mixed item).
- **Articles, correctly unmarked: 304** (173 on wire-type outlets, 131 on other outlets that carry release rows too).
- Already Yes on non-wire outlets (count only): 261. Already Yes on wire outlets or release hosts: 266.

## What I found

1. **The real wires are nearly clean.** Only one US Fed News item (01759) and one PR Newswire item on Yahoo (01190) are unmarked. Two more Yahoo copies of a GlobeNewswire and a PR Newswire release (00290, 01364) sit next to Yes rows for the same story.
2. **Most misses are release text reposted by small outlets as-is**: California Armenian Legislative Caucus Foundation and ANCA-WR announcements (California Courier, Asbarez, Oragark, Massis Post), GIFFORDS and EWG releases in Lassen County Times, Governor's Office and legislator releases in Lake County News and the Record Bee "News Briefs", and unsigned items on Contra Costa News, Van Nuys News Press and SFV Sun. For these the sheet already marks sibling rows Yes (same story or same outlet pattern), so the unmarked ones look inconsistent.
3. **Wire-type names that are really news**: U-Wire / University Wire (student papers), CE Noticias Financieras (rewritten news), News From The States, TCA, Governing, Government Technology, JNS, CNN Wire. They have reporter bylines or reported text, so they are articles.
4. **A local paper running a release as its own story stays press** (Beverly Press, Times-Herald, Turlock Journal, Acorn): left as articles or "unsure".
5. **Same-story pairs unmarked beside a Yes row** (20 rows; most are in the list below) are the easiest to settle.

## Likely releases not marked (82)

| Article | Story | O/R | Outlet | Date | Headline | Reason (from the text) | Now |
|---|---|---|---|---|---|---|---|
| 00014 | s00003 | O | Asbarez | 2026-10-20 | ANCA-WR Announces 2026 General Election Endorsements | Slate of 61 candidates spans Congress, Governor and California statewide offices, | (blank) |
| 01359 | s00365 | O | Asbarez | 2025-04-23 | Armenian Genocide Commemoration, Policy Advocacy Take C | SACRAMENTO—The Armenian National Committee of America – Western Region on Monday | (blank) |
| 01423 | s00387 | R | Asbarez | 2025-03-17 | ANCA-WR and Northern California Chapter Advocate for Le | SACRAMENTO—Representatives from the Armenian National Committee of America – Western Region joined the ANCA | (blank) |
| 01527 | s00423 | O | Asbarez | 2025-01-23 | Armenian Legislative Caucus Requests Montebello Martyrs | de Martyrs Monument in Montebello be officially designated as a California State Historical Landmark. | (blank) |
| 04559 | s01374 | O | Asbarez | 2021-06-21 | Assemblymember Vince Fong Joins California Armenian Leg | Assemblymember Vince Fong SACRAMENTO—Assemblymember Vince Fong has become the latest state | (blank) |
| 07350 | s02143 | O | Asbarez | 2026-05-18 | ANCA-Western Region Announces 2026 Primary Endorsements | LOS ANGELES – The Armenian National Committee of America, Western Region | (blank) |
| 07760 | s02499 | O | Asbarez | 2025-06-19 | Assemblymembers Davies and Wallis Join Armenian Legisla | Assemblymembers Laurie Davies and Greg Wallis SACRAMENTO—The California Armenian Legislative Caucus | (blank) |
| 07852 | s02577 | O | Asbarez | 2025-04-07 | State Assembly Speaker, Senate President Join Armenian  | SACRAMENTO—The California Armenian Legislative Caucus Foundation announced the addition of two new members, Speaker | (blank) |
| 07949 | s02668 | O | Asbarez | 2025-01-24 | John Harabedian Named California Armenian Legislative C | New State Legislatures Join Caucus SACRAMENTO—The California Armenian Legislative Caucus Foundation | (blank) |
| 08417 | s03049 | O | Asbarez | 2024-04-17 | Assemblymembers Pellerin, Ta Join Armenian Legislatuve  | Assemblymembers Gail Pellerin (left) and Tri Ta SACRAMENTO—The California Armenian Legislative | (blank) |
| 08535 | s03153 | O | Asbarez | 2024-02-02 | Ahead of 2024 Primary Elections, ANCA-WR Issues L.A.-Ar | Candidates endorsed by the ANCA-WR for the Greater Los Angeles Area | (blank) |
| 09058 | s03589 | O | Asbarez | 2023-03-13 | Rubio, Carrillo Join California Armenian Legislative Ca | SACRAMENTO—The California Armenian Legislative Caucus Foundation announced that Senator Susan Rubio | (blank) |
| 09104 | s03632 | O | Asbarez | 2022-10-27 | ANCA-WR Announces Endorsements for California State and | LOS ANGELES — The Armenian National Committee of America–Western Region has | (blank) |
| 09215 | s03737 | O | Asbarez | 2022-05-18 | ANCA-WR Announces Endorsements Ahead of 2022 Primaries | A list of the ANCA-WR’s 2022 Congressional Endorsements A list of | (blank) |
| 09354 | s03863 | O | Asbarez | 2021-08-17 | Assemblymember Holden Introduces Bill to Establish Sist | SACRAMENTO—Assemblymember Chris Holden introduced a resolution, ACR 105 on Tuesday that | (blank) |
| 09422 | s03928 | O | Asbarez | 2021-03-16 | More Lawmakers Join California Armenian Legislative Cau | California Armenian Legislative Caucus SACRAMENTO—The California Armenian Legislative Caucus announced that | (blank) |
| 09584 | s04075 | O | Asbarez | 2019-06-05 | California Armenian Legislative Caucus Welcomes New Mem | r members from the California Senate and Assembly to identify key issues affecting Armenian | (blank) |
| 09667 | s04145 | O | Asbarez | 2018-05-23 | ANCA-WR Announces Endorsements Ahead of Primaries | GLENDALE – With just weeks left until the primary elections, the | (blank) |
| 10680 | s04952 | O | Asbarez | 2021-09-15 | California Legislators Announce Essay and Visual Arts S | SACRAMENTO—The California Armenian Legislative Caucus announced the winners of this year’s 2021 California Armenian | (blank) |
| 00013 | s00003 | R | California Courier, The | 2026-10-22 | ANCA-WR Announces 2026 General Election Endorsements | Slate of 61 candidates spans Congress, Governor and California statewide offices, the State Legislature | (blank) |
| 00204 | s00056 | O | California Courier, The | 2026-09-08 | CALIFORNIA ARMENIAN LEGISLATIVE CAUCUS FOUNDATION NEW M | Sacramento, CA – The California Armenian Legislative Caucus Foundation announced new members Senator Jesse | (blank) |
| 00620 | s00160 | O | California Courier, The | 2026-03-19 | CALIFORNIA ARMENIAN LEGISLATIVE CAUCUS FOUNDATION ANNOU | Sacramento, CA – The California Armenian Legislative Caucus Foundation announced new member Senate President | (blank) |
| 00634 | s00166 | O | California Courier, The | 2026-02-16 | CALIFORNIA ARMENIAN LEGISLATIVE CAUCUS FOUNDATION ANNOU | Sacramento, CA – The California Armenian Legislative Caucus Foundation announce new member Assemblymember Isaac | (blank) |
| 00691 | s00189 | O | California Courier, The | 2026-01-14 | CALIFORNIA ARMENIAN LEGISLATIVE CAUCUS FOUNDATION NEW M | Sacramento, CA – The California Armenian Legislative Caucus Foundation announced the joining of a | (blank) |
| 01139 | s00306 | O | California Courier, The | 2025-08-19 | CALIFORNIA ARMENIAN LEGISLATIVE CAUCUS FOUNDATION ADDS  | Sacramento, CA – The California Armenian Legislative Caucus Foundation added a new member: Assemblymember | (blank) |
| 01183 | s00323 | O | California Courier, The | 2025-07-02 | SENATOR DAVE CORTESE JOINS CALIFORNIA ARMENIAN LEGISLAT | Sacramento, CA – The California Armenian Legislative Caucus Foundation announced new member Senator Dave | (blank) |
| 01244 | s00335 | O | California Courier, The | 2025-06-20 | CALIFORNIA ARMENIAN LEGISLATIVE CAUCUS FOUNDATION NEW M | Sacramento, CA – The California Armenian Legislative Caucus Foundation announced new member Assemblymember Laurie | (blank) |
| 01358 | s00365 | R | California Courier, The | 2025-04-25 | Armenian Genocide Commemoration, Policy Advocacy Take C | SACRAMENTO—The Armenian National Committee of America – Western Region on Monday led a delegation | (blank) |
| 01383 | s00373 | R | California Courier, The | 2025-04-07 | ALIFORNIA ARMENIAN LEGISLATIVE CAUCUS FOUNDATION ANNOUN | Sacramento, CA – The California Armenian Legislative Caucus Foundation announcedthe addition of two new | (blank) |
| 01422 | s00387 | O | California Courier, The | 2025-03-17 | ANCA-WR and Northern California Chapter Advocate for Le | acramento, CA – On March 10th and 11th, representatives from the Armenian National Committee | (blank) |
| 01526 | s00423 | R | California Courier, The | 2025-01-24 | Armenian Legislative Caucus Council Request Montebello  | Monument in Montebello be officially designated as a California State Historical Landmark. The Armenian | (blank) |
| 01573 | s00433 | O | California Courier, The | 2025-01-22 | Harabedian named chair of California Armenian Legislati | Sacramento — The California Armenian Legislative Caucus Foundation announced the new Chair Assemblymember John | (blank) |
| 01816 | s00501 | O | California Courier, The | 2024-10-08 | ANCA Western Region Announces Endorsements for November | GLENDALE—The Armenian National Committee of America-Western Region announced its list of endorsed candidates for | (blank) |
| 02336 | s00672 | O | California Courier, The | 2024-04-17 | The California Armenian Legislative Caucus Foundation a | menian Americans and develop and empower the Armenian American community throughout California. The Caucus | (blank) |
| 03404 | s00956 | O | California Courier, The | 2023-07-20 | Assemblyman Rick Zbur Joins CA Armenian Legislative Cau | announcement-style headline, no byline: Assemblyman Rick Zbur Joins CA Armenian Legislative Caucus | (blank) |
| 03693 | s01034 | O | California Courier, The | 2023-04-20 | Assemblymember Rick Zbur joins California Armenian Legi | announcement-style headline, no byline: Assemblymember Rick Zbur joins California Armenian Legislati | (blank) |
| 03938 | s01100 | O | California Courier, The | 2023-03-16 | CA Armenian Legislative Caucus Foundation Announces New | The California Armenian Legislative Caucus Foundation added new members Senator Susan Rubio (D-Baldwin Park) | (blank) |
| 04177 | s01205 | O | California Courier, The | 2022-08-04 | Assemblyman Cottie Petrie-Norris Joins CA Armenian Legi | announcement-style headline, no byline: Assemblyman Cottie Petrie-Norris Joins CA Armenian Legislati | (blank) |
| 04203 | s01218 | O | California Courier, The | 2022-06-09 | Jim Wood Joins California Armenian Legislative Caucus F | announcement-style headline, no byline: Jim Wood Joins California Armenian Legislative Caucus Founda | (blank) |
| 04508 | s01348 | O | California Courier, The | 2021-09-16 | Policy Committee Approves California-Syunik Sister Stat | announcement-style headline, no byline: Policy Committee Approves California-Syunik Sister State Res | (blank) |
| 04534 | s01359 | O | California Courier, The | 2021-08-26 | Holden Introduces Resolution Establishing Sister State  | SACRAMENTO-Last week, Assemblymember Chris Holden introduced a resolution, ACR 105, that establishes a sister | (blank) |
| 04558 | s01374 | R | California Courier, The | 2021-06-24 | Assemblymember Vince Fong Joins CA Armenian Caucus | announcement-style headline, no byline: Assemblymember Vince Fong Joins CA Armenian Caucus | (blank) |
| 04604 | s01393 | O | California Courier, The | 2021-05-13 | Assembly Speaker Pro Tem Mullin Joins CA Armenian Caucu | announcement-style headline, no byline: Assembly Speaker Pro Tem Mullin Joins CA Armenian Caucus | (blank) |
| 04634 | s01406 | O | California Courier, The | 2021-03-25 | Nine Assembly members Join California Armenian Legislat | SACRAMENTO-The California Armenian Legislative Caucus added new members: Senate President pro Tempore Tony G. | (blank) |
| 05246 | s01655 | O | California Courier, The | 2018-05-31 | ANCA-WR Announces Primary Election Endorsements | GLENDALE, Calif. - The Armenian National Committee of America - Western Region released its | (blank) |
| 07688 | s02336 | R | California News Beep | 2025-10-14 | Governor Newsom Signs Law Banning Glock Pistols in Cali | California News Beep / NewsBeep.com 3 Californians will no longer be able to buy | (blank) |
| 02171 | s04415 | O | Contra Costa News | 2024-06-06 | Sen. Dodd Introduces Restaurant Fees Bill | SACRAMENTO – Sen. Bill Dodd, D-Napa, introduced legislation today to enhance consumer protection for | (blank) |
| 03927 | s04537 | O | Contra Costa News | 2023-03-17 | Bill Seeks to Sustain Outdoor Dining Across California | Legislation Would Preempt Local Ordinances and Preserve Regulatory Flexibility for Struggling Neighborhood Restaurants SACRAMENTO, | (blank) |
| 07564 | s02336 | O | Contra Costa News | 2025-10-14 | Governor Newsom Signs Law Banning Glock Pistols in Cali | (less certain) Californians will no longer be able to buy a new Glock gun in the | (blank) |
| 08650 | s03259 | O | Contra Costa News | 2023-10-14 | Bill to Sustain Outdoor Dining in California Signed by  | (less certain) A bill was signed this week by Governor Gavin Newsom that would allow for | (blank) |
| 09117 | s03645 | O | Contra Costa News | 2022-10-04 | New Water Year Begins Amid Preparations for Continued D | SACRAMENTO, Calif. – Conserving water has become a way of life in California, especially | (blank) |
| 09095 | s03623 | O | Jewish World Watch | 2022-12-02 | December 2, 2022 | (less certain) Jewish World Watch JWW’s Serena Oberstein named Activist of the Year by Asm. Jesse | (blank) |
| 01154 | s00312 | O | Lake County News | 2025-08-02 | California expands historic commitment to local journal | (less certain) California is expanding its historic commitment to local journalism with a $15 million budget | (blank) |
| 04311 | s01264 | O | Lake County News | 2022-03-01 | Bipartisan coalition of legislators introduce bill to d | (less certain) State Senate Majority Leader Mike McGuire and a broad, bipartisan coalition of California state | (blank) |
| 09773 | s04739 | O | Lake County News | 2023-10-21 | Governor doubles funding to bolster safety and security | By GOVERNOR’S OFFICE / Oct. 21, 2023 Amid heightened fears and concerns among California’s | (blank) |
| 02756 | s00793 | O | Lake County Record Bee | 2023-11-15 | News Briefs | (less certain) "issued the following statement" ; SACRAMENTO Author of AB 587 issues statement on District Court hearing regarding Twitter’s challenge | (blank) |
| 02978 | s00859 | O | Lake County Record Bee | 2023-10-10 | News Briefs | (less certain) SACRAMENTO McGuire’s landmark Offshore Wind Expediting Act Signed by Gov. Newsom Senate President Designee | (blank) |
| 04231 | s01228 | O | Lake County Record Bee | 2022-05-28 | State Briefs | (less certain) State Assembly advances bill to strengthen California’s water conservation tools SACRAMENTO >> Against the | (blank) |
| 00226 | s00061 | O | Lassen County Times | 2026-09-01 | GIFFORDS celebrates major wins for gun safety in Califo | GIFFORDS, the national gun violence prevention organization led by former Congresswoman Gabrielle Giffords, released | (blank) |
| 00284 | s00075 | O | Lassen County Times | 2026-07-23 | EWG-sponsored California bills to boost consumer safety | California, the world's fourth-largest economy, could soon prove – once again – its status | (blank) |
| 00549 | s00141 | O | Lassen County Times | 2026-04-14 | Setting a gold standard in the Golden State: Five EWG-s | As the world's fourth largest economy, California doesn't just pass laws, it helps reshape | (blank) |
| 03172 | s00891 | O | Lassen County Times | 2023-09-26 | Newsom signs groundbreaking gun violence prevention fun | Today, GIFFORDS, the gun violence prevention organization founded by former Congresswoman Gabby Giffords, applauded | (blank) |
| 04189 | s01208 | O | Lassen County Times | 2022-07-06 | Giffords applauds California lawmakers for robust actio | (less certain) Giffords, the gun safety organization co-founded by former Congresswoman Gabby Giffords, applauded California lawmakers | (blank) |
| 04310 | s01263 | O | Lassen County Times | 2022-03-03 | Following president's call to action, Assembly announce | (less certain) On the heels of President Joe Biden's call to strengthen privacy protections and online | (blank) |
| 10664 | s01521 | R | Massis Post | 2019-09-13 | California State Senate Passes Turkish Divestment Bill | Pinterest 0 Mail 0 SACRAMENTO – The California State Senate passed the Turkish Divestment | (blank) |
| 07892 | s02615 | O | Oragark | 2025-03-14 | Արևմտեան Ամերիկայի Շրջանային Հայ Դատի  Յանձնախմբի եւ Հի | առաւարութեան հարցերով համակարգող Սոնեա Մերոյեանը եւ Հիւսիսային Կալիֆորնիայի Հայ Դատի Յանձնախմբի համակարգող Հենրի Աղաջանովը: | (blank) |
| 08703 | s03308 | O | Oragark | 2023-10-09 | CA Armenian Legislative Caucus Foundation Calls on Pres | Oragark The California Armenian Legislative Caucus Foundation (Sacramento, CA)- Sent a letter to President | (blank) |
| 08269 | s02928 | O | San Diego Jewish World | 2024-08-16 | JPAC's 'Highest Priority' Bills Still Alive in Californ | (less certain) JPAC’s ‘Highest Priority’ Bills Still Alive in California Legislature – San Diego Jewish World | (blank) |
| 08328 | s02983 | O | San Diego Jewish World | 2024-06-23 | $80 Million in California State Budget Will Help Protec | (less certain) San Diego Jewish World By David Bocarsly David Bocarsly SACRAMENTO, California – Governor Gavin | (blank) |
| 00202 | s00054 | O | San Fernando Valley Sun, The | 2026-09-10 | AB 1626 Wins Final Passage and Heads to the Governor's  | (less certain) Last week, the California State Legislature passed AB 1626, key legislation that will put | (blank) |
| 04237 | s01232 | O | San Fernando Valley Sun, The | 2022-05-19 | State Assembly Advances Bill to Crack Down on Street Ra | (less certain) In response to the continued rise in illegal street racing in the state, the | (blank) |
| 01444 | s00395 | R | Santa Barbara Independent | 2025-02-25 | Assembly Holds Hearing on Federal Funding in California | Indy Staff Press releases are posted on Independent.com as a free community service. Credit: | (blank) |
| 09922 | s04743 | O | UCLA Newsroom | 2015-11-23 | UCLA Anderson professor and family are honored for effo | (less certain) The family received Jewish World Watch’s annual Global Soul Award Carolyn Gray Anderson November | (blank) |
| 01759 | s00485 | O | US Fed News | 2024-11-20 | SPEAKER ROBERT RIVAS URGES FISCAL RESTRAINT IN RESPONSE | announcement-style headline, no byline: SPEAKER ROBERT RIVAS URGES FISCAL RESTRAINT IN RESPONSE TO L | (blank) |
| 02757 | s04462 | O | Ukiah Daily Journal | 2023-11-15 | News Briefs | (less certain) "issued the following statement" ; SACRAMENTO Author of AB 587 issues statement on District Court hearing regarding Twitter’s challenge | (blank) |
| 04232 | s01228 | R | Ukiah Daily Journal | 2022-05-29 | California - State Briefs | (less certain) State Assembly advances bill to strengthen California’s water conservation tools SACRAMENTO >> Against the | (blank) |
| 07741 | s02487 | O | Van Nuys News Press | 2025-06-29 | Governor Newsom Signs Balanced State Budget | Van Nuys News Press Signing of landmark package to cut red tape, fast-track housing, | (blank) |
| 09534 | s04033 | O | Van Nuys News Press | 2020-01-12 | Assemblymember Jesse Gabriel Calls For Greater Accounta | "issued the following statement" ; response to Governor Newsom’s proposed 2020-2021 Budget: Buy Maps “I applaud Governor Newsom’s commitment | (blank) |
| 10651 | s04930 | O | Van Nuys News Press | 2026-10-28 | Assembly Budget Chair Jesse Gabriel Delivers $2.5 Milli | (less certain) improve accessibility, and help expand its positive impact on our community for years to | (blank) |
| 00290 | s00078 | R | Yahoo News | 2026-07-13 | Play Equity Fund Secures $4 Million in State Funding fo | LA84 Foundation July 13, 2026 4 min read LA84 Foundation Youth Sports For All | (blank) |
| 01190 | s00326 | R | Yahoo News | 2025-06-30 | Reentry Orgs Secure $10M in CA Budget | "Contact:" ; PR Newswire June 30, 2025 2 min read SACRAMENTO, Calif., June 30, 2025 /PRNewswire/ | (blank) |
| 01364 | s00367 | R | Yahoo News | 2025-04-24 | Public Health & Safety Advocates Condemn California Ass | PR Newswire April 24, 2025 3 min read Dangerous 4 a.m. Bar Bill Advances | (blank) |

## Unsure (28)

| Article | Story | O/R | Outlet | Date | Headline | Reason (from the text) | Now |
|---|---|---|---|---|---|---|---|
| 05129 | s01595 | O | Acorn, The | 2019-02-21 | New labeling proposed for medications | mixed or short item; Law to prevent taking wrong drugs on February 21, 2019 Assemblymember Jesse Gabriel (D-San | (blank) |
| 08541 | s03156 | R | Alston & Bird | 2024-01-23 | Environment, Land Use & Natural Resources / Securities  | mixed or short item; me effective January 1, 2024 The law’s sponsor declared his intent in a letter | (blank) |
| 00652 | s00175 | O | Asbarez | 2026-01-27 | Over 400 Celebrate Grand Opening and Dedication of ACF  | mixed or short item; Top Stories 0 15-Year Community Effort Transforms Former Fire Station 83 into a Permanent | (blank) |
| 00651 | s00175 | R | California Courier, The | 2026-01-29 | Over 400 Celebrate Grand Opening and Dedication of ACF  | mixed or short item; -Year Community Effort Transforms Former Fire Station 83 into a Permanent Home for Youth, | (blank) |
| 08819 | s03399 | O | Contra Costa News | 2023-09-08 | Bill to Add 11% Tax on Firearms and Ammunition Moves Fo | mixed or short item; California Bill That Adds 11% Tax on Firearms and Ammunition Moves Forward by CC | (blank) |
| 06980 | s01827 | O | Encino Enterprise | 2026-10-15 | Jesse Gabriel Garners $22 Million to Clean Up Sepulveda | mixed or short item; California Assemblymember and Assembly Budget Chair Jesse Gabriel was instrumental in garnering a $22 | (blank) |
| 06917 | s01777 | O | Jewish California | 2026-05-15 | Jewish California Capitol Summit 2026 / AB 715 Lawsuit  | no saved text | (blank) |
| 06984 | s01829 | O | Jewish Federation of the Greater East Bay | 2026-02-27 | Jewish community convenes for 2026 California governor  | mixed or short item; Jewish Federation of the Greater East Bay · 2026-10-15 https://jewishfed.org/news/jewish-community-convenes-for-2026-california-governor-candidate-forum/ Saved 2026-10-20 Jewish Community | (blank) |
| 09576 | s04067 | O | Jewish Federation of the Greater East Bay | 2019-07-10 | Effective Advocacy for our Jewish Community | mixed or short item; Jewish Federation Bay Area The summer is an exciting time for state politics in | (blank) |
| 10693 | s00373 | R | Massis Post | 2025-04-07 | California Armenian Legislative Caucus Foundation Annou | no saved text | (blank) |
| 10665 | s01521 | R | News.am | 2019-09-12 | California state senate passes Turkish divestment bill | mixed or short item; make preferable SACRAMENTO, CA – The California State Senate passed the Turkish Divestment Bill, | (blank) |
| 07098 | s04641 | R | NewsBreak |  |  | no saved text | (blank) |
| 07197 | s02017 | R | NewsBreak |  |  | no saved text | (blank) |
| 10658 | s04937 | O | Newsroom America | 2026-09-28 | Newsom Signs First-in-Nation Non-Ultraprocessed Food La | mixed or short item; Sep 2026 2:45 p.m. · Source: California Governors Office California Governor Gavin Newsom signed | (blank) |
| 04537 | s01361 | O | PanARMENIAN.Net | 2021-08-18 | Sister state ties between California and Syunik could b | announcement-style headline, no byline: Sister state ties between California and Syunik could be est | (blank) |
| 04813 | s01481 | O | PanARMENIAN.Net | 2020-02-25 | Armenian Committee announces endorsements ahead of 2020 | mixed or short item; With just over a week left until the March 3 primary elections, the Armenian | (blank) |
| 07731 | s02478 | O | San Diego Jewish World | 2025-07-08 | Showdown Delayed on Bill to Curb Antisemitism in School | mixed or short item; San Diego Jewish World By David Bocarsly David Bocarsly SACRAMENTO, California — State Senate | (blank) |
| 08523 | s03142 | O | San Diego Jewish World | 2024-02-19 | California Legislators Visit Sites of Oct. 7 Massacre | mixed or short item; San Diego Jewish World By David Bocarsly David Bocarsly SACRAMENTO, California — I just | (blank) |
| 07548 | s02322 | R | Shooting News Weekly | 2025-10-17 | Newsom Signs Another 'Do Something' Gun Control Bill Th | mixed or short item; Shooting News Weekly · 2025-10-17 https://www.shootingnewsweekly.com/gun-control/newsom-signs-another-do-something-gun-control-bill-that-will-surprise-do-nothing/ Saved 2026-10-20 Newsom Signs Another ‘Do Something’ Gun | (blank) |
| 07665 | s02416 | O | Shooting News Weekly | 2025-09-16 | How California Government Created the Pretense For the  | mixed or short item; The GLOCK sales ban that seems about to become law in California (AB 1127) | (blank) |
| 07722 | s02469 | O | Shooting News Weekly | 2025-07-20 | California Bill That Would Ban GLOCK Pistols Advances i | mixed or short item; While gun rights advocates are calling the legislation the “Glock ban bill” because Glock | (blank) |
| 09677 | s04154 | O | Sierra Sun Times | 2018-04-08 | Meet Heather Bernikoff Mariposa County District 3 ... | no saved text | (blank) |
| 05130 | s01595 | R | Simi Valley Acorn | 2019-02-22 | New labeling proposed for medications | mixed or short item; Assemblymember Jesse Gabriel (D-San Fernando Valley) recently introduced legislation to protect patients by requiring | (blank) |
| 08089 | s02786 | O | Southern California Record, The | 2024-11-05 | New California food dye ban: Is it protection for kids  | no saved text; wire/aggregator outlet name only | (blank) |
| 09230 | s03751 | O | Steinberg Institute | 2022-03-22 | Our Legislation | mixed or short item; Steinberg Institute This year, the Steinberg Institute’s sponsored bills are aligned with Vision 2030, | (blank) |
| 08466 | s03096 | O | U.S. Newswire | 2024-03-18 | Alcohol Justice / In the News | mixed or short item; Alcohol tax Skip to main content Many news outlets frequently use research, quotes, and | (blank) |
| 08522 | s03141 | O | U.S. Newswire | 2024-02-23 | Alcohol Justice / Legislative activity | mixed or short item; state and federal legislative activity Skip to main content Alcohol Justice monitors state and | (blank) |
| 00641 | s04319 | O | UCLA Newsroom | 2026-02-06 | Jewish Leaders and Students Define Resilience at UCLA H | mixed or short item; Jewish leaders and students define resilience at UCLA Hillel event — and more media | (blank) |

## Articles on wire-type outlets, correctly unmarked (173)

| Article | Story | O/R | Outlet | Date | Headline | Reason (from the text) | Now |
|---|---|---|---|---|---|---|---|
| 00573 | s00151 | R | Africa Newswire | 2026-03-28 | State pushes 'first in the nation' grocery label for hi | reported story, no release signals | (blank) |
| 01388 | s00377 | R | Africa Newswire | 2025-03-28 | 'Excessive' state taxes on guns, ammunition sales are t | reported story, no release signals | (blank) |
| 00049 | s00044 | R | CE Noticias Financieras: English | 2026-10-06 | Two new lawsuits reignite the debate over Nazi-looted a | reported story, no release signals | (blank) |
| 00127 | s00044 | R | CE Noticias Financieras: English | 2026-09-20 | New laws spark legal battle in the United States over a | reported story, no release signals | (blank) |
| 00986 | s00252 | R | CE Noticias Financieras: English | 2025-10-10 | Newsom signs new law that will forever change restauran | reported story, no release signals | (blank) |
| 01533 | s00430 | R | CE Noticias Financieras: English | 2025-01-24 | California to allocate $2.5 billion dollars to Los Ange | reported story, no release signals | (blank) |
| 01534 | s00430 | R | CE Noticias Financieras: English | 2025-01-24 | California Congress approves $2.5 billion to respond to | reported story, no release signals | (blank) |
| 01581 | s00436 | O | CE Noticias Financieras: English | 2025-01-21 | Industry reformulates food after red dye No. 3 ban | reported story, no release signals | (blank) |
| 01616 | s00445 | O | CE Noticias Financieras: English | 2025-01-11 | Curfew in Los Angeles due to looting after fires | reported story, no release signals | (blank) |
| 01846 | s00519 | R | CE Noticias Financieras: English | 2024-09-30 | California injects oxygen into the fight for the Thysse | reported story, no release signals | (blank) |
| 01926 | s00546 | R | CE Noticias Financieras: English | 2024-09-04 | No more "Hot-Cheetos": California bans them | reported story, no release signals | (blank) |
| 01948 | s00553 | O | CE Noticias Financieras: English | 2024-08-30 | Controversial NEW law banned by the state of California | reported story, no release signals | (blank) |
| 02079 | s00591 | O | CE Noticias Financieras: English | 2024-07-01 | New laws in the U.S.: wage increases, rights for undocu | reported story, no release signals | (blank) |
| 02885 | s00827 | R | CE Noticias Financieras: English | 2023-10-14 | California passes law to ban food additives in the U.S. | reported story, no release signals | (blank) |
| 02895 | s00834 | O | CE Noticias Financieras: English | 2023-10-13 | Misunderstanding cleared up: Skittles not banned in Cal | reported story, no release signals | (blank) |
| 02914 | s00853 | R | CE Noticias Financieras: English | 2023-10-11 | California bans red dye 3 and other harmful chemicals f | reported story, no release signals | (blank) |
| 02977 | s00858 | O | CE Noticias Financieras: English | 2023-10-10 | California bans red dye No. 3 and other harmful substan | reported story, no release signals | (blank) |
| 03850 | s01070 | O | CE Noticias Financieras: English | 2023-03-24 | Legislator introduces bill to ban sale of candies conta | reported story, no release signals | (blank) |
| 00991 | s00252 | R | CE Noticias Financieras: Portuguese | 2025-10-10 | Newsom assinou uma nova lei que mudará para sempre os r | reported story, no release signals | (blank) |
| 01531 | s00430 | R | CE Noticias Financieras: Portuguese | 2025-01-24 | Congresso da Califórnia aprova US$ 2,5 bilhões para res | reported story, no release signals | (blank) |
| 01532 | s00430 | R | CE Noticias Financieras: Portuguese | 2025-01-24 | A Califórnia alocará US$ 2,5 bilhões para o alívio do i | reported story, no release signals | (blank) |
| 02960 | s00853 | R | CE Noticias Financieras: Portuguese | 2023-10-11 | A Califórnia proíbe o corante vermelho 3 e outros produ | reported story, no release signals | (blank) |
| 00984 | s00252 | R | CE Noticias Financieras: Spanish | 2025-10-10 | Newsom firmó una nueva ley que modificará para siempre  | reported story, no release signals | (blank) |
| 01507 | s00430 | R | CE Noticias Financieras: Spanish | 2025-01-24 | California destinará 2 mil 500 mdd a Los Ángeles por in | reporter byline: Sophie Austin | (blank) |
| 01508 | s00430 | R | CE Noticias Financieras: Spanish | 2025-01-24 | Congreso de California aprueba $2,500 millones para res | reporter byline: Sophie Austin | (blank) |
| 02962 | s00853 | R | CE Noticias Financieras: Spanish | 2023-10-11 | California prohíbe el colorante rojo 3 y otros químicos | reporter byline: Josep Rodríguez | (blank) |
| 03686 | s01030 | R | CE Think Tank Newswire: English | 2023-04-21 | Cities should maintain flexible outdoor dining programs | reporter byline: Sal Rodriguez | (blank) |
| 04931 | s01538 | O | CE Think Tank Newswire: English | 2019-08-20 | Proposed Mandatory Ethnic Studies Curriculum is Too Lib | reporter byline: Kara Zupkus | (blank) |
| 02966 | s00855 | O | CNN Wire Service | 2023-10-09 | California becomes first US state to ban 4 potentially  | reporter byline: Chris Boyette, Kristen Rogers and Andi B | (blank) |
| 03836 | s04534 | O | CNN Wire Service | 2023-03-23 | California bill aims to ban sale of popular candies con | reporter byline: Andi Babineau and Kristen Rogers | (blank) |
| 07617 | s02381 | R | CNN Wire Service |  |  | reporter byline: Sandee LaMotte | (blank) |
| 07790 | s02523 | R | CNN Wire Service |  |  | reporter byline: Sandee LaMotte | (blank) |
| 08227 | s02896 | R | CNN Wire Service |  |  | reporter byline: Kristen Rogers | (blank) |
| 09186 | s03711 | O | CNN Wire Service | 2022-06-28 | Californians will vote on adding women's reproductive r | reporter byline: Cheri Mossburg | (blank) |
| 03261 | s00923 | O | Ecns.cn - China News Service (CNS): English | 2023-09-11 | California Legislature approves tax on guns, ammunition | reported story, no release signals | (blank) |
| 00594 | s00154 | R | Governing | 2026-03-25 | A California Pilot Could Reshape How Governments Tackle | reporter byline: Marisa Kendall | (blank) |
| 01051 | s00276 | R | Governing | 2025-10-02 | States Join Bipartisan Push to Curb Ultra | reporter byline: Carl Smith | (blank) |
| 01620 | s04375 | R | Governing | 2025-01-10 | California Lawmakers Consider Expediting Insurance Clai | reporter byline: Anabel Sosa | (blank) |
| 02703 | s00776 | R | Governing | 2023-12-08 | California Considers Everything, Even Fiscal Emergency, | reporter byline: Lindsey Holden | (blank) |
| 02842 | s04468 | O | Governing | 2023-10-24 | California Moves Ahead of the FDA and Bans Food Additiv | no saved text; reporter byline Annie Sciacca (outlet name only) | (blank) |
| 03466 | s00976 | R | Governing | 2023-06-26 | Who Is Robert Rivas, California’s New Assembly Speaker? | reporter byline: Lindsey Holden, Mathew Miranda and Steph | (blank) |
| 04262 | s01246 | R | Governing | 2022-03-24 | Who Should Get California’s Proposed Inflation Relief C | reporter byline: Lindsey Holden | (blank) |
| 09152 | s03678 | O | Governing | 2022-09-14 | “Social media has created incredible opportunities, but | reported story, no release signals | (blank) |
| 09381 | s03890 | R | Governing | 2021-06-04 | Lawmakers Fail to Pass Violence Prevention Gun Tax Bill | reporter byline: Patrick McGreevy | (blank) |
| 00451 | s00111 | R | Government Technology | 2026-06-16 | California Democrats Back Budget Plan That Pushes Back  | reporter byline: Stephen Hobbs and Andrew Graham | (blank) |
| 00474 | s00115 | R | Government Technology | 2026-06-12 | Legislature Aligns on Spending Plan as Deadline Looms | reporter byline: Stephen Hobbs and Andrew Graham | (blank) |
| 01097 | s00295 | R | Government Technology | 2025-09-02 | Bills Targeting Social Media, AI Chatbots Clear Hurdle  | reporter byline: Nicole Nixon and Stephen Hobbs | (blank) |
| 01371 | s00369 | R | Government Technology | 2025-04-15 | Calif. Law Allocates $180M for Wildfire Prevention | reporter byline: Grant Stringer | (blank) |
| 04195 | s01214 | O | Government Technology | 2022-06-24 | California Policy Takes Aim at Social Media Transparenc | reported story, no release signals | (blank) |
| 04347 | s01289 | R | Government Technology | 2021-11-05 | Employee Data Collection Sparks Labor Advocate Concern | reporter byline: Chase DiFeliciantonio | (blank) |
| 04615 | s01398 | R | Government Technology | 2021-04-02 | California Lawmakers Want to Hold Big Tech More Account | reporter byline: Chase DiFeliciantonio | (blank) |
| 08684 | s03289 | O | Government Technology | 2023-10-10 | Newsom Signs Cybersecurity, Data Bills | reporter byline: Theo Douglas | (blank) |
| 09050 | s03582 | O | Government Technology | 2023-03-17 | Assembly Committee to Discuss Proposed Security, Privac | reporter byline: Theo Douglas | (blank) |
| 00077 | s00022 | O | JNS | 2026-10-01 | Newsom draws criticism of 'asymmetry' for signing expan | reporter byline: Jessica Russak-Hoffman | (blank) |
| 00264 | s00071 | O | JNS | 2026-08-13 | California state legislature to decide on six bills 'cr | reporter byline: Aaron Bandler | (blank) |
| 00622 | s00161 | O | JNS | 2026-03-18 | New bill would ‘gut’ key protections in state law for J | reporter byline: Aaron Bandler | (blank) |
| 00627 | s00163 | O | JNS | 2026-03-02 | At Jewish forum for California governor candidates, a r | reporter byline: Aaron Bandler | (blank) |
| 01150 | s00310 | O | JNS | 2025-08-13 | State Jewish legislators denounce Trump admin's $1b set | reported story, no release signals | (blank) |
| 02013 | s00576 | O | JNS | 2024-07-31 | California boosts Nonprofit Security Grant Program to $ | reporter byline: Etgar Lefkovits | (blank) |
| 02231 | s00633 | O | JNS | 2024-05-23 | At JPAC California summit, state leaders vow support fo | reporter byline: Ryan Torok | (blank) |
| 03496 | s00986 | O | JNS | 2023-06-13 | Uyghur activists: 'We will never forget' Jewish support | reporter byline: Karmel Melamed | (blank) |
| 03613 | s01015 | O | JNS | 2023-05-10 | California's Jewish Caucus pursues 'tikkun olam' with n | reporter byline: Bill Motchan | (blank) |
| 04132 | s01186 | O | JNS | 2022-09-02 | California legislature passes bill aiming to combat hat | reporter byline: Jonathan S. Tobin | (blank) |
| 04361 | s01295 | O | JNS | 2021-10-21 | Los Angeles Holocaust museum secures $2.5 million in ne | reported story, no release signals | (blank) |
| 04513 | s01350 | O | JNS | 2021-09-10 | Watchdog urges Newsom to veto ethnic-studies mandate af | reported story, no release signals | (blank) |
| 04564 | s01376 | O | JNS | 2021-06-17 | Jewish Caucus secures nearly $80 in California state bu | reported story, no release signals | (blank) |
| 04681 | s01415 | O | JNS | 2021-03-19 | Jewish, pro-Israel groups express mixed reactions to ad | reported story, no release signals | (blank) |
| 04689 | s01421 | O | JNS | 2021-02-24 | California Jewish Caucus joins lawmakers to promote sla | reporter byline: Jonathan S. Tobin | (blank) |
| 04769 | s01459 | O | JNS | 2020-09-01 | Ethnic-studies requirement for high | reported story, no release signals | (blank) |
| 04987 | s01553 | O | JNS | 2019-08-02 | Proposed anti-Israel ethnic-studies curriculum in Calif | reporter byline: Sean Savage and Jackson Richman | (blank) |
| 05119 | s01587 | O | JNS | 2019-03-19 | 11th annual IAC gala in LA shares interwoven stories of | reported story, no release signals | (blank) |
| 07603 | s02368 | O | JNS | 2025-10-09 | Newsom signs bills against 'hate in all its forms,' inc | reporter byline: Aaron Bandler | (blank) |
| 07671 | s02422 | O | JNS | 2025-09-13 | California lawmakers vote 106-0 to pass K-12 Jew-hatred | reporter byline: Aaron Bandler | (blank) |
| 09265 | s03777 | O | JNS | 2022-03-15 | Sierra Club reverses course, reinstating Israel trips a | reported story, no release signals | (blank) |
| 09388 | s03895 | O | JNS | 2021-05-30 | California Officially Honors Israeli-Americans | reporter byline: JNS Staff | (blank) |
| 01110 | s00297 | O | Jewish News Syndicate | 2025-08-26 | Jew-Hatred as Bad in Us as Ever, California Jewish Poli | reporter byline: Joseph Feldman | (blank) |
| 02760 | s00795 | O | Jewish News Syndicate | 2023-11-10 | California Legislative Jewish Caucus outraged at antise | reporter byline: Jessamyn Dodd | (blank) |
| 04562 | s04587 | O | Jewish News Syndicate | 2021-06-17 | Jewish Caucus secures $80 million in California state b | reported story, no release signals | (blank) |
| 07215 | s02033 | O | Jewish News Syndicate | 2026-08-14 | California legislature passes two ‘critically important | reported story, no release signals | (blank) |
| 00189 | s00049 | R | News From The States |  |  | reporter byline: Yue Stella Yu | (blank) |
| 00283 | s00074 | R | News From The States | 2026-08-03 | Keep an eye on these 5 deals as California lawmakers cl | reporter byline: Yue Stella Yu and Maya C. Miller | (blank) |
| 00466 | s00113 | R | News From The States |  |  | reporter byline: Yue Stella Yu and Kate Wolffe | (blank) |
| 00593 | s00154 | R | News From The States | 2026-03-25 | A new homelessness strategy is sweeping California | reporter byline: Marisa Kendall | (blank) |
| 00624 | s00162 | R | News From The States | 2026-03-06 | A podcaster gave Newsom a gun. Are California laws keep | reporter byline: Ryan Sabalow | (blank) |
| 00784 | s00219 | R | News From The States | 2025-11-07 | California lawmakers found money for these pet projects | reporter byline: Ryan Sabalow | (blank) |
| 01084 | s00290 | R | News From The States |  |  | reporter byline: Yue Stella Yu and Jeanne Kuang | (blank) |
| 01091 | s00292 | R | News From The States | 2025-09-08 | How California legislators got more than ... | reporter byline: Jeremia Kimelman | (blank) |
| 01169 | s00315 | R | News From The States | 2025-07-28 | California may soon ban selling new Glocks like the one | reporter byline: Ryan Sabalow | (blank) |
| 01219 | s00330 | R | News From The States | 2025-06-27 | A 'poison pill' in California's budget deal ties state  | reporter byline: Alexei Koseff | (blank) |
| 01224 | s00331 | R | News From The States | 2025-06-27 | Will California ban ultra | reporter byline: Kristen Hwang | (blank) |
| 01644 | s00449 | R | News From The States | 2025-01-06 | Five things to watch as California’s Legislature return | reporter byline: Alexei Koseff | (blank) |
| 01813 | s00499 | R | News From The States | 2024-10-10 | California pledged $500 million to help tenants preserv | reporter byline: Felicia Mello | (blank) |
| 02147 | s00611 | R | News From The States | 2024-06-13 | Gavin Newsom and top Democrats are deciding ... | reporter byline: Alexei Koseff | (blank) |
| 02251 | s04421 | R | News From The States |  |  | reporter byline: Sameea Kamal | (blank) |
| 02287 | s00652 | R | News From The States | 2024-05-10 | Big cuts, no new taxes: Gov. Newsom's plan to fix Calif | reporter byline: Alexei Koseff | (blank) |
| 07364 | s02155 | O | Political Transcript Wire | 2026-04-30 | House Energy and Commerce Health Subcommittee hearing:  | reported story, no release signals | (blank) |
| 02094 | s00597 | O | Religion News Service | 2024-06-27 | LA mayor considers buffer zones at houses of worship af | reported story, no release signals | (blank) |
| 03574 | s01005 | O | Religion News Service | 2023-05-19 | Religious broadcasters seek to reverse California law a | reporter byline: Alejandra Molina | (blank) |
| 04539 | s01363 | O | Religion News Service | 2021-08-11 | Jewish and Latino legislators announce funding to renov | reporter byline: Alejandra Molina | (blank) |
| 00316 | s00082 | R | TCA News Service | 2026-07-08 | Feds to decide fate of $2 billion California plan to fu | reporter byline: Grant Stringer | (blank) |
| 00915 | s00236 | R | TCA News Service | 2025-10-14 | Glock ban, slavery reparations, ICE agent masks, more h | reporter byline: Paul Rogers and Grant Stringer | (blank) |
| 01053 | s00276 | R | TCA News Service |  |  | reporter byline: Claudia Boyd-Barrett | (blank) |
| 01134 | s00304 | R | TCA News Service | 2025-08-19 | Bill to remove ultra-processed foods from school meals  | reporter byline: Jia H Jung | (blank) |
| 01213 | s00327 | R | TCA News Service | 2025-06-30 | California approves most significant environmental law  | reporter byline: Grant Stringer | (blank) |
| 01378 | s00369 | R | TCA News Service | 2025-04-14 | Newsom signs $180 million more for fire prevention, plu | reporter byline: Grant Stringer | (blank) |
| 01633 | s00447 | R | TCA News Service |  |  | reporter byline: Grant Stringer | (blank) |
| 01799 | s00496 | R | TCA News Service | 2024-10-19 | California continues progressive policies, with restrai | reporter byline: Don Thompson | (blank) |
| 02026 | s00579 | R | TCA News Service | 2024-07-22 | 2 new laws crack down on sexual harassment at Californi | reporter byline: Molly Gibbs | (blank) |
| 02128 | s00609 | R | TCA News Service |  |  | reporter byline: Vanessa G. Sánchez | (blank) |
| 02191 | s04417 | O | TCA News Service | 2024-06-06 | Last-minute law aims to protect California restaurants  | reporter byline: Kate Bradshaw | (blank) |
| 02327 | s00667 | R | TCA News Service | 2024-04-23 | California Legislators Debate Froot Loops and Free Cond | reporter byline: Don Thompson | (blank) |
| 02496 | s00724 | R | TCA News Service | 2024-03-13 | On the heels of ‘Skittles ban,’ California moves to ban | reporter byline: John Woolfolk | (blank) |
| 02796 | s00806 | R | TCA News Service |  |  | reporter byline: Don Thompson | (blank) |
| 02841 | s00815 | R | TCA News Service | 2023-10-20 | California moves ahead of the FDA in banning common can | reporter byline: Annie Sciacca | (blank) |
| 03673 | s01025 | R | TCA News Service | 2023-04-26 | California bill to make internet platforms pay for news | reporter byline: John Woolfolk | (blank) |
| 03684 | s04515 | O | TCA News Service | 2023-04-24 | Commentary: New Bill Could Raise Standards for Processe | reporter byline: Tanya Jogee | (blank) |
| 07110 | s01947 | O | TCA News Service | 2026-09-22 | Tuesday, September 22, 2026 | reported story, no release signals | (blank) |
| 07111 | s01948 | O | TCA News Service | 2026-09-22 | First Death Reported In Dengue Outbreak Spread By Mosqu | reported story, no release signals | (blank) |
| 07112 | s01949 | O | TCA News Service | 2026-09-22 | California Weekly Roundup: Wednesday, Sept. 23, 2026 | reported story, no release signals | (blank) |
| 07308 | s02107 | O | TCA News Service | 2026-06-15 | Wyoming Abortion Restrictions Ruled Unconstitutional By | reported story, no release signals | (blank) |
| 07309 | s02108 | O | TCA News Service | 2026-06-15 | First Edition: Monday, June 15, 2026 | reported story, no release signals | (blank) |
| 07609 | s02374 | O | TCA News Service | 2025-10-09 | First Edition: Thursday, Oct. 9, 2025 | reported story, no release signals | (blank) |
| 08910 | s03468 | O | TCA News Service | 2023-05-23 | Michigan's Red Flag Gun Violence Bills Become Law | reported story, no release signals | (blank) |
| 08911 | s03469 | O | TCA News Service | 2023-05-23 | First Edition: May 23, 2023 | reported story, no release signals | (blank) |
| 00496 | s00122 | R | TCA Regional News | 2026-05-29 | Two District 1 races for Congress in Northern Californi | reporter byline: Austin Murphy | (blank) |
| 00643 | s00171 | R | TCA Regional News | 2026-02-02 | Philp: California needs more teamwork to solve homeless | reporter byline: Tom Philp | (blank) |
| 01689 | s00464 | R | TCA Regional News | 2024-12-09 | Newsom said he's going to 'Trump-proof' California. Wha | reporter byline: Alec Regimbal | (blank) |
| 01930 | s00547 | R | TCA Regional News | 2024-09-04 | California moves to crack down on snacks like Flamin' H | reporter byline: Alec Regimbal | (blank) |
| 02181 | s00620 | R | TCA Regional News |  |  | reporter byline: Sara Edwards | (blank) |
| 02213 | s00631 | R | TCA Regional News | 2024-05-29 | Valley leaders ask state legislators to avoid cutbacks  | reporter byline: John Cox | (blank) |
| 02424 | s00713 | R | TCA Regional News | 2024-03-14 | Could California schools really ban Takis and Flamin' H | reporter byline: Jessica Yadegaran | (blank) |
| 03237 | s00912 | R | TCA Regional News | 2023-09-13 | California Legislature passes food chemicals bill once  | reporter byline: Alex Shultz | (blank) |
| 03439 | s00967 | R | TCA Regional News |  |  | reporter byline: Phil Barber | (blank) |
| 03923 | s01091 | R | TCA Regional News | 2023-03-20 | Is California really about to ban Skittles? | reporter byline: Madeline Wells | (blank) |
| 04609 | s01396 | R | TCA Regional News | 2021-04-05 | After the pandemic ends, will the Bay Area get to keep  | reporter byline: Susana Guerrero | (blank) |
| 02557 | s00741 | O | Tribune Content Agency News Service Special Sections | 2024-02-14 | News briefs | reported story, no release signals | (blank) |
| 03242 | s00916 | O | Tribune Content Agency News Service Special Sections | 2023-09-12 | News briefs | reported story, no release signals | (blank) |
| 03680 | s01029 | R | Tribune Content Agency News Service Special Sections | 2023-04-24 | Commentary: New bill could raise standards for processe | reporter byline: Tanya Jogee | (blank) |
| 03871 | s01074 | O | Tribune Content Agency News Service Special Sections | 2023-03-23 | News briefs | reported story, no release signals | (blank) |
| 05389 | s01735 | O | U-Wire | 2004-07-29 | UC-Berkeley freshman takes on Democratic National Conve | reporter byline: Kim-Mai Cutler | (blank) |
| 05395 | s01741 | O | U-Wire | 2003-06-17 | COLUMN: Achieving diversity can be problematic | reporter byline: Michael Ward | (blank) |
| 05396 | s01743 | O | U-Wire | 2003-02-28 | UC-Berkeley chancellor waives 1/3 of student government | reporter byline: Stephanie Lee | (blank) |
| 05402 | s01745 | O | U-Wire | 2003-02-25 | UC-Berkeley plan to aid recycling 'one cup at a time' | reporter byline: Amelia Heagerty | (blank) |
| 05403 | s01746 | O | U-Wire | 2003-02-14 | UC-Berkeley forums to foster discussions of war in Iraq | reporter byline: Tami Abdollah | (blank) |
| 05404 | s01747 | O | U-Wire | 2003-02-13 | Official says bookstore's owner owes $150K | reporter byline: Jay Kapp and Stephanie Lee | (blank) |
| 05406 | s01749 | O | U-Wire | 2002-11-26 | Post-big game activities may incur disciplinary action | reporter byline: Sara Zaidi | (blank) |
| 05407 | s01750 | O | U-Wire | 2002-11-26 | Search begins for new UC president | reporter byline: Maren Lane | (blank) |
| 05408 | s01751 | O | U-Wire | 2002-11-07 | UC student assoc. expected to pay UC-Berkeley | reporter byline: Jay Kapp | (blank) |
| 05409 | s01752 | O | U-Wire | 2002-11-06 | Student assoc. scrambles for money to pay liability to  | reporter byline: Jay Kapp | (blank) |
| 05411 | s01754 | O | U-Wire | 2002-10-01 | First UC-Berkeley protester hearing gets under way | reporter byline: Millie Lapidario | (blank) |
| 05412 | s01755 | O | U-Wire | 2002-09-12 | UC-Berkeley campus community reminisces together | reporter byline: Yalda Afshar and Emma Schwartz | (blank) |
| 05415 | s01757 | O | U-Wire | 2002-09-10 | UC-Berkeley students planning Sept. 11 memorial receive | reporter byline: Emma Schwartz | (blank) |
| 05416 | s01758 | O | U-Wire | 2002-09-06 | UC-Berkeley reverses decision not to distribute ribbons | reporter byline: Jay Kapp, Emma Schwartz and Tina Nguyen | (blank) |
| 05417 | s01759 | O | U-Wire | 2002-08-23 | UC-Berkeley chancellor denounces Racial Privacy Initiat | reporter byline: Millie Lapidario | (blank) |
| 05418 | s01760 | O | U-Wire | 2002-08-15 | Daily Cal to stay on UC-Berkeley campus | reporter byline: Mike Meyers | (blank) |
| 05419 | s01761 | O | U-Wire | 2002-08-13 | Board may rule on Daily Cal's campus lease | reporter byline: Jennifer Kline | (blank) |
| 05420 | s01762 | O | U-Wire | 2002-05-15 | UC-Berkeley campus paper lease jeopardized | reporter byline: Wendy Lee | (blank) |
| 05422 | s01764 | O | U-Wire | 2001-11-09 | UC-Berkeley student gov't calls on UC Regents to end nu | reporter byline: Wendy Lee | (blank) |
| 00798 | s00225 | R | University Wire | 2025-10-24 | New gun law angers second amendment die-hards | reporter byline: Daniel | (blank) |
| 01126 | s00303 | R | University Wire |  |  | reporter byline: Josephine Murphy | (blank) |
| 01415 | s04365 | R | University Wire | 2025-03-21 | New Bill Targets Harmful Ingredients in California Scho | reported story, no release signals | (blank) |
| 01788 | s00493 | R | University Wire | 2024-10-23 | El gobernador Newsom firma nueva legislación bipartidis | reported story, no release signals | (blank) |
| 01791 | s00495 | R | University Wire | 2024-10-17 | Governor Newsom signs new bipartisan legislation suppor | reported story, no release signals | (blank) |
| 01991 | s00566 | R | University Wire | 2024-08-20 | Championed by ASUC EAVP, AB 2608 will update sexual vio | reported story, no release signals | (blank) |
| 03678 | s01028 | R | University Wire | 2023-04-25 | End of the rainbow? New bill seeks to ban food additive | reporter byline: Christie Counts | (blank) |
| 04403 | s04569 | R | University Wire | 2021-10-09 | New law targets student hunger with extended qualificat | reporter byline: Emily Calix | (blank) |
| 04419 | s01325 | R | University Wire | 2021-10-08 | CA legislation passed to address homelessness, housing  | reported story, no release signals | (blank) |
| 04773 | s01461 | R | University Wire | 2020-08-27 | California senate signs bill to help housing-insecure s | reporter byline: Jess Magill | (blank) |
| 04835 | s01490 | R | University Wire | 2020-02-05 | Campaign for College Opportunity celebrates 2019 Legisl | reporter byline: Liz Jacobson | (blank) |
| 04871 | s04605 | O | University Wire | 2019-10-07 | CA Gov. Gavin Newsom signs AB 1278 addressing student n | reporter byline: Kaleo Mark | (blank) |
| 05128 | s01594 | R | University Wire | 2019-02-21 | California college activists rally together for financi | reported story, no release signals | (blank) |
| 06926 | s00427 | R | University Wire |  |  | reporter byline: Sameea Kamal | (blank) |
| 07851 | s02576 | O | University Wire | 2025-04-07 | Legislating a better future: UC Student Association tak | reporter byline: Abby Offenhauser | (blank) |

## Other candidates judged articles (131)

These are on outlets that also carry release rows (San Diego Jewish World, Contra Costa News, Asbarez and similar) or showed one release-like phrase. They are in the CSV, not repeated here.

All rows, all groups, same columns plus the reason each was a candidate: `work/localapp/PRESS_RELEASE_CHECK.csv`.
