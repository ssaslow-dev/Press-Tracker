# Press release = Yes rows, re-checked against the new rule (read-only; nothing in the workbook was changed)

For Sammy. Rule applied (PRJUDGE-v1 follow-up): a row is a press release only if (a) its text is a release AND (b) the outlet is a wire or an official site. A community or local news outlet running a release, even word for word, is coverage. AP, Reuters, CNS and Bloomberg are news unless the item is itself a release.

**Data.** Workbook copy dated 2026-11-03 (sha256 starts 0bccc1fc); saved text from the library snapshot dated 2026-10-31 (a few of the newest rows have none); overlap with his office releases from the live tracker's `release_texts.json`. Verdicts rest on the outlet type plus the opening of the text; they are my judgment, not a bulk-edit list.

## Counts

- Rows marked Yes: **527**
- **Keep Yes** (wire or official site, release text): **280**
- **Should be No** (news outlet, or reported text, or not a release): **228**
- **Unsure** (no saved text): **19**

Of the 228 "should be No": 215 are news or community outlets (180 of them carry release text, word for word or release-style; 35 read as reported or rewritten news), and 13 are official sites whose text is a news or blog post rather than a release (California Apartment Association 10, Common Sense Media 2, Jewish World Watch 1).

## What un-marking would do

Press release = Yes rows are hidden in the tracker. Clearing the mark on the 228 rows would make them visible: those rows join the story and reprint counts, and each story shown goes up by its rows. Stories whose rows are all news-outlet reprints of a release would appear as new stories (their Story ID is unchanged). Because the sheet only fills blanks, un-marking is a deliberate edit and needs your say; the purple row colour (PRCOLOR-v1) would be removed for those rows too. The 280 "keep Yes" rows and the 19 unsure rows stay as they are until you decide.

## Should be No (228), grouped by outlet

### Sierra Sun Times (39), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 00039 | s00013 | O | 2026-10-09 | California Legislative Central Coast Caucus on Presiden | news/community outlet running a release (coverage under the rule); "issued the following" wording: issued the following statement regarding the comments made by President Trump regarding Los Angeles |
| 00105 | s00034 | O | 2026-09-27 | Governor Gavin Newsom Signs Comprehensive Package Of Bi | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO – Yesterday, Governor Gavin Newsom announced his signature on a comprehensive package of |
| 07196 | s02017 | O | 2026-08-31 | Assemblymember Jesse Gabriel Says California Refuses to | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (99%): Assemblymember Jesse Gabriel Says California Refuses to Let Hate Win, Legislation Pass |
| 00361 | s00086 | O | 2026-07-04 | California Landmark Legislation Closing DIY Machine Gun | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (97%): California Landmark Legislation Closing DIY Machine Gun Loophole Goes Into Effect, Tru |
| 00366 | s00088 | O | 2026-07-01 | Governor Newsom Says, “Donald Trump Wants Taxpayers To  | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO – In response to President Donald Trump’s $1.776 billion fund benefiting individuals connected |
| 00439 | s04310 | O | 2026-06-23 | California Governor Gavin Newsom Says, “Putting Money A | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (59%): California Governor Gavin Newsom Says, “Putting Money Aside To Protect Ourselves From  |
| 07445 | s02228 | O | 2026-02-11 | California State Democrats Fight Back Against President | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO — As Trump and Republicans in Congress cut federal dollars that support women’s |
| 00982 | s00250 | R | 2025-10-09 | California Governor Gavin Newsom Signs Legislation Cutt | news/community outlet running a release (coverage under the rule); release dateline opening: LOS ANGELES – Continuing ongoing efforts to make opening and running small businesses in |
| 01144 | s00308 | O | 2025-08-14 | California Jewish Leaders Support UCLA and the Universi | news outlet, reported or rewritten text, no release signal; "California Jewish Leaders Support UCLA and the University of California System as President Trump" |
| 07938 | s02659 | O | 2025-02-04 | Assembly Democrats Pass Legal Defense Fund to Protect C | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO – Assemblymember Wicks and fellow Assembly Democrats moved with urgency on Monday to |
| 01697 | s04379 | O | 2024-12-03 | Governor Gavin Newsom Announces Special California Legi | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO — On Monday, following Governor Newsom’s proclamation, the California Legislature convened the f |
| 01866 | s00525 | O | 2024-09-28 | California Governor Gavin Newsom Signs Eight Bipartisan | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO — Governor Gavin Newsom on Friday announced he signed a bipartisan package of |
| 01870 | s04394 | O | 2024-09-28 | California Attorney General Bonta Issues Statement on L | news/community outlet running a release (coverage under the rule); "issued the following" wording: issued the following statement in response to Governor Gavin Newsom signing into law Assembly |
| 01875 | s00530 | R | 2024-09-25 | Governor Gavin Newsom Signs Bipartisan Legislation to S | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO — Building on California’s nation-leading gun laws, Governor Gavin Newsom on Tuesday signed |
| 01879 | s00532 | O | 2024-09-23 | California Governor Gavin Newsom Signs Bipartisan Housi | news/community outlet running a release (coverage under the rule); release dateline opening: SAN FRANCISCO — Last week, Governor Gavin Newsom signed a new bipartisan legislative package |
| 01885 | s04396 | O | 2024-09-17 | California Governor Gavin Newsom Signs Legislation to H | news outlet, reported or rewritten text, no release signal; "California Governor Gavin Newsom Signs Legislation to Help Holocaust Survivors Recover Art Stolen by" |
| 08217 | s02890 | O | 2024-08-31 | Assemblymember Jesse Gabriel Announces California Passe | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (99%): Assemblymember Jesse Gabriel Announces California Passes First-in-the-Nation Legislati |
| 01986 | s00564 | O | 2024-08-28 | California Assemblymember Jesse Gabriel Announces Gover | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (99%): California Assemblymember Jesse Gabriel Announces Governor Gavin Newsom Signs Legislat |
| 08268 | s02927 | O | 2024-08-16 | Assemblymember Jesse Gabriel Says California Passes Leg | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (99%): Assemblymember Jesse Gabriel Says California Passes Legislation to Help Holocaust Surv |
| 02019 | s00578 | O | 2024-07-30 | California Governor Gavin Newsom Announces $76 Million  | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO — California Governor Gavin Newsom today announced that California is expediting the deployment |
| 08304 | s02961 | O | 2024-07-02 | Assemblymember Jesse Gabriel Announces Historic New Tax | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (99%): Assemblymember Jesse Gabriel Announces Historic New Tax on Gun Industry Goes Into Effe |
| 08378 | s03016 | O | 2024-05-21 | Assemblymember Jesse Gabriel Announces Morgan Freeman,  | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (99%): Assemblymember Jesse Gabriel Announces Morgan Freeman, Superintendent Tony Thurmond, D |
| 02323 | s04430 | O | 2024-04-27 | California Attorney General Bonta Highlights Resources  | news/community outlet running a release (coverage under the rule); release dateline opening: OAKLAND, CA – As part of National Crime Victims’ Rights Week, California Attorney General |
| 02341 | s04431 | R | 2024-04-10 | California Attorney General Bonta, Assemblymember Gabri | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (92%): California Attorney General Bonta, Assemblymember Gabriel Announce Legislation to Incr |
| 02391 | s00690 | R | 2024-04-01 | California Assemblymember Jesse Gabriel with Lieutenant | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (99%): California Assemblymember Jesse Gabriel with Lieutenant Governor Eleni Kounalakis Anno |
| 08561 | s03178 | O | 2023-12-31 | U.S. District Judge Finds that X Corp. — Formerly Known | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (100%): U.S. District Judge Finds that X Corp. — Formerly Known as Twitter — Is |
| 02850 | s00819 | O | 2023-10-19 | California Governor Gavin Newsom Doubles Funding to Bol | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO — Amid heightened fears and concerns among California’s faith communities stemming from the |
| 02909 | s00840 | O | 2023-10-12 | Governor Gavin Newsom Signs Bills to Streamline Housing | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO – Governor Gavin Newsom on Wednesday announced that he has signed 56 bills |
| 08914 | s03472 | O | 2023-05-20 | California State Assembly Passes Legislation to Provide | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (98%): California State Assembly Passes Legislation to Provide Greater Oversight of Private J |
| 09066 | s03597 | O | 2023-02-21 | California Assemblymember Jesse Gabriel Introduces the  | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (99%): California Assemblymember Jesse Gabriel Introduces the Electric Vehicle Charging for A |
| 09102 | s03630 | O | 2022-11-05 | With California Governor’s Signature, Ryan’s Law Become | news outlet, reported or rewritten text, no release signal; "With California Governor’s Signature, Ryan’s Law Becomes Reality - Pushes Criminal Prosecution Of Extreme" |
| 09120 | s03648 | O | 2022-09-29 | California Is Making It Cheaper to Replace Your Lawn to | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO – Conserving water has become a way of life in California, and one |
| 04069 | s01163 | O | 2022-09-25 | Governor Gavin Newsom Announces California IDs For All  | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO – As other states cruelly target migrants and vilify immigration, Governor Gavin Newsom |
| 04080 | s04547 | O | 2022-09-19 | California Governor Newsom Announces New State Sites Id | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO – Governor Gavin Newsom today announced that the California Department of Housing and |
| 04471 | s01338 | O | 2021-09-28 | California Governor Gavin Newsom Signs Legislation to I | news/community outlet running a release (coverage under the rule); release dateline opening: OAKLAND – Today, Governor Gavin Newsom signed a suite of bills to boost housing |
| 04756 | s01451 | R | 2020-09-29 | Governor Gavin Newsom Signs Legislation Boosting Housin | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO — Governor Gavin Newsom on Monday signed legislation that will help California make |
| 04762 | s01454 | O | 2020-09-28 | Governor Gavin Newsom Takes Action on Legislation to Su | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO – Governor Gavin Newsom on Sunday took action on several bills that continue |
| 09489 | s03989 | O | 2020-08-31 | California Governor Gavin Newsom Signs Landmark Legisla | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO – Governor Gavin Newsom signed SB 793 on Friday, making California the leader |
| 04874 | s01512 | O | 2019-10-07 | California Governor Gavin Newsom Signs Bills to Increas | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO – Building on the state’s historic investment in two years of free community |

### San Diego Jewish World (36), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 07019 | s01875 | O | 2026-10-01 | All 6 Jewish priority bills signed by Governor Newsom | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (86%): All 6 Jewish priority bills signed by Governor Newsom San Diego Jewish World · |
| 07096 | s01937 | O | 2026-09-25 | Newsom signs 2 bills to protect congregants and sites | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (92%): Newsom signs 2 bills to protect congregants and sites San Diego Jewish World · |
| 07213 | s02031 | O | 2026-08-14 | Six Jewish California priority bills advance in Legisla | news/community outlet running a release (coverage under the rule); release category tag: Press Release) –The Senate and Assembly Appropriations Committees held their final hearings Thursday afternoon. |
| 07245 | s02058 | O | 2026-07-02 | Policy committees approve 3 bills sponsored by Jewish C | news/community outlet running a release (coverage under the rule); release category tag: Press Release) – Jewish California (formerly JPAC), the nation’s largest statewide coalition of Jewish |
| 07248 | s02061 | O | 2026-07-01 | State budget includes annual $80m for security of vulne | news/community outlet running a release (coverage under the rule); release category tag: Press Release) — This week, the California Legislative Jewish Caucus secured $80 million in |
| 07282 | s02089 | O | 2026-06-23 | Two bills directly impacting Jews advance in California | news/community outlet running a release (coverage under the rule); release category tag: Press Release) — Two priority bills sponsored by Jewish California – the nation’s largest |
| 07347 | s02140 | O | 2026-05-18 | Rabbi Devorah Marcus, 13 others, honored at California  | news/community outlet running a release (coverage under the rule); release category tag: Press Release) — San Diego Reform Rabbi Devorah Marcus was among a group honored |
| 07368 | s02158 | O | 2026-04-28 | Legislative Jewish Caucus furious over candidate's anti | news/community outlet running a release (coverage under the rule); "issued the following" wording: issued the following statement: “During my 27 years as a county elections official, I |
| 07418 | s02202 | O | 2026-03-25 | Five bills to pass and one to defeat: Jewish California | news/community outlet running a release (coverage under the rule); release category tag: Press Release) –After a historic year – including passing AB 715, California’s landmark antisemitism |
| 07436 | s02219 | O | 2026-02-25 | Jewish Public Affairs Committee renames itself 'Jewish  | news/community outlet running a release (coverage under the rule); release category tag: Press Release) — JPAC, Jewish Public Affairs Committee of California, announced on Wednesday a |
| 07638 | s02394 | O | 2025-10-07 | Newsom Signs Bill Protecting K-12 Students from Antisem | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (63%): Newsom Signs Bill Protecting K-12 Students from Antisemitism – San Diego Jewish World  |
| 07822 | s02549 | O | 2025-05-11 | Minority Caucuses Team to Fight Hatred in K-12 Schools | news/community outlet running a release (coverage under the rule); "issued the following" wording: issued the following joint statement that included the following: The California Legislative Diversit |
| 07915 | s02637 | O | 2025-02-14 | Jewish Caucus in State Capitol Expresses Solidarity wit | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (83%): Jewish Caucus in State Capitol Expresses Solidarity with Refugees and Immigrants San D |
| 08164 | s02844 | O | 2024-09-28 | Gov. Newsom Signs Three Education Bills Sought by Jewis | news/community outlet running a release (coverage under the rule); release category tag: Press Release) – California Governor Gavin Newsom announced on Saturday, Sept. 28, that he |
| 08200 | s02873 | O | 2024-09-06 | Four Bills to Curb Antisemitism Await Governor Newsom's | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (98%): Four Bills to Curb Antisemitism Await Governor Newsom's Signature San Diego Jewish Wor |
| 08428 | s03058 | O | 2024-04-10 | S.D. Jewish Institutions to Receive $1.39 Million in St | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO, California – The California Office of Emergency Services (CalOES) announced on Wednesday $40 |
| 02390 | s00690 | R | 2024-03-28 | Legislation Would Aid Victims of Nazi Art Thefts | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (93%): Legislation Would Aid Victims of Nazi Art Thefts – San Diego Jewish World California |
| 08693 | s03298 | O | 2023-10-09 | Newsom Directs State Funds to Jewish Federations, Other | news/community outlet running a release (coverage under the rule); release category tag: Press Release) – On Sunday, Governor Gavin Newsom signed into law Assembly Bill 1185, |
| 09155 | s03681 | O | 2022-09-13 | Gov. Newsom Signs Gabriel Bill to Fight Internet Hate | news/community outlet running a release (coverage under the rule); release category tag: Press Release) –Governor Gavin Newsom on Tuesday signed Assembly Bill (AB) 587 into law. |
| 09206 | s03729 | O | 2022-06-02 | California Legislature's Budget Agreement Includes $36  | news/community outlet running a release (coverage under the rule); release category tag: Press Release) On Wednesday, the California Assembly and Senate released their joint budget agreement, |
| 09277 | s03790 | O | 2022-01-25 | California Legislative Jewish Caucus Announces Nearly $ | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (86%): California Legislative Jewish Caucus Announces Nearly $50 Million in Security Funding  |
| 09310 | s03823 | O | 2021-10-12 | Gov. Newsom Signs Bill for Better Reporting of Hate Cri | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (96%): Gov. Newsom Signs Bill for Better Reporting of Hate Crime incidents – San Diego |
| 04511 | s04582 | O | 2021-09-09 | California Legislature Approves Anti-Hate-Crime Legisla | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (95%): California Legislature Approves Anti-Hate-Crime Legislation – San Diego Jewish World C |
| 09348 | s03857 | O | 2021-09-08 | California Ethnic Studies Legislation Passes | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (89%): California Ethnic Studies Legislation Passes San Diego Jewish World · 2021-09-08 https |
| 09358 | s03867 | O | 2021-08-10 | Restored Breed Street Shul Will Be a Multi-Ethnic Commu | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (93%): Restored Breed Street Shul Will Be a Multi-Ethnic Community Center – San Diego Jewish |
| 09375 | s03884 | O | 2021-06-14 | Legislature approves Nearly $80 Million for Jewish-inte | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (93%): Legislature approves Nearly $80 Million for Jewish-interest Causes – San Diego Jewish  |
| 09386 | s03893 | O | 2021-06-03 | California Assembly Passes Measure to Hold Social Media | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (94%): California Assembly Passes Measure to Hold Social Media Companies Accountable for Onli |
| 04577 | s01381 | O | 2021-06-01 | California Bill Calls for Better Documentation of Hate  | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (94%): California Bill Calls for Better Documentation of Hate Crimes – San Diego Jewish World |
| 09399 | s03906 | O | 2021-05-06 | California Legislative Jewish Caucus Tells Priorities | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (94%): California Legislative Jewish Caucus Tells Priorities – San Diego Jewish World State S |
| 09408 | s03914 | O | 2021-04-08 | Global Holocaust Remembrance Goes Virtual | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (99%): Global Holocaust Remembrance Goes Virtual – San Diego Jewish World Marchers are posed  |
| 09416 | s03922 | O | 2021-03-29 | Legislator seeks to control social media's impact on ha | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (97%): Legislator seeks to control social media’s impact on hate – San Diego Jewish World |
| 09463 | s03965 | O | 2020-11-18 | Jesse Gabriel new chair of Legislative Jewish Caucus | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (99%): Jesse Gabriel new chair of Legislative Jewish Caucus San Diego Jewish World · 2020-11- |
| 09464 | s03966 | O | 2020-11-17 | Jewish Legislator Says Progressive Group Anti-Semitic | news/community outlet running a release (coverage under the rule); release category tag: Press Release) — Assemblymember Marc Levine (D – Marin County) on Tuesday, Nov. 17, |
| 09606 | s04088 | O | 2019-04-29 | State allocates $15m to protect groups against hate | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (97%): State allocates $15m to protect groups against hate – San Diego Jewish World State |
| 09634 | s04112 | O | 2019-02-04 | Gun violence prevention group created in Legislature | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (88%): Gun violence prevention group created in Legislature – San Diego Jewish World Gabielle |
| 09643 | s04122 | O | 2018-12-13 | Editor’s E-Mail Box: December 13, 2018 (3 items) | news outlet, reported or rewritten text, no release signal; "Editor’s E-Mail Box: December 13, 2018 (3 items) – San Diego Jewish World Ten" |

### Contra Costa News (22), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 07097 | s04641 | O | 2026-09-26 | California Legislative Jewish Caucus Celebrates Signing | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (97%): California Legislative Jewish Caucus Celebrates Signing of Two Priority Bills Protecti |
| 00629 | s00164 | O | 2026-02-19 | Governor Signs Legislation Authorizing $590 Million Eme | news/community outlet running a release (coverage under the rule); release category tag: Press Release by CC News 02/19/2026 written by CC News 02/19/2026 Image from Governors |
| 00981 | s00250 | O | 2025-10-09 | New Laws Aim to Help Restaurant Owners Keep California  | news/community outlet running a release (coverage under the rule); release category tag: Press Release by CC News 10/09/2025 written by CC News 10/09/2025 861 LOS ANGELES |
| 01032 | s00272 | O | 2025-10-07 | Bills to Crack Down on Hate and Antisemitism in Califor | news/community outlet running a release (coverage under the rule); release category tag: Press Release by CC News 10/07/2025 written by CC News 10/07/2025 856 SACRAMENTO — |
| 01874 | s00530 | O | 2024-09-24 | Governor Newsom Signs Legislation to Strengthen Califor | news/community outlet running a release (coverage under the rule); release category tag: Press Release by CC News 09/24/2024 written by CC News 09/24/2024 Image by San |
| 01878 | s04395 | O | 2024-09-20 | Governor Newsom Signs Housing Package | news/community outlet running a release (coverage under the rule); release category tag: Press Release by CC News 09/20/2024 written by CC News 09/20/2024 Image by Office |
| 01977 | s04402 | O | 2024-08-27 | Newsom Signs New Laws to Help Address Homelessness | news/community outlet running a release (coverage under the rule); release category tag: Press Release by CC News 08/27/2024 written by CC News 08/27/2024 1.6K Governor Newsom |
| 08332 | s02987 | O | 2024-06-19 | Committees Approve Restaurant Fees Bill | outlet is a news outlet; no saved text |
| 02389 | s00690 | O | 2024-03-28 | Legislation Aims to Help Holocaust Survivors Recover St | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (100%): Legislation Aims to Help Holocaust Survivors Recover Stolen Art California Legislatio |
| 08605 | s03218 | O | 2023-11-19 | Jewish Caucus Condemns Storming of Democratic Party Con | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (100%): Jewish Caucus Condemns Storming of Democratic Party Convention by Anti-Israel Protest |
| 03166 | s00887 | O | 2023-09-26 | Governor Newsom Strengthens California's Nation-Leading | news/community outlet running a release (coverage under the rule); release category tag: Press Release by CC News 09/26/2023 written by CC News 09/26/2023 Photo by Office |
| 08784 | s03370 | O | 2023-09-12 | California Senate Passes Legislation Banning Dangerous  | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (79%): California Senate Passes Legislation Banning Dangerous Food Additives California Calif |
| 08851 | s04674 | O | 2023-08-24 | State Superintendent Hosts Conversation on Ways to Coun | news/community outlet running a release (coverage under the rule); release category tag: Press Release by CC News 08/24/2023 written by CC News 08/24/2023 Tony Thurmond 2.5K |
| 08902 | s03460 | O | 2023-05-26 | Firearm Tax to Fund School Safety and Gun Violence Prev | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (93%): Firearm Tax to Fund School Safety and Gun Violence Prevention Efforts Moves Forward Ca |
| 08917 | s03474 | O | 2023-05-19 | Bill to Sustain Outdoor Dining Across California Advanc | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (96%): Bill to Sustain Outdoor Dining Across California Advances California Bill to Sustain O |
| 03578 | s04510 | O | 2023-05-16 | Assembly Passes Legislation to Ban Use of Dangerous Che | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (94%): Assembly Passes Legislation to Ban Use of Dangerous Chemicals in Food and Beverages Ca |
| 08967 | s03516 | O | 2023-04-12 | Bill to Ban the Sale of Processed Foods Containing Dang | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (100%): Bill to Ban the Sale of Processed Foods Containing Dangerous Chemicals Passes Critica |
| 09037 | s03570 | O | 2023-03-20 | Bill Would Ban the Sale of Processed Foods Containing D | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (100%): Bill Would Ban the Sale of Processed Foods Containing Dangerous Chemicals California  |
| 09070 | s03601 | O | 2023-02-01 | Governor Newsom Takes Action to Strengthen California’s | news/community outlet running a release (coverage under the rule); release category tag: Press Release by CC News 02/01/2023 written by CC News 02/01/2023 Photo by Office |
| 03995 | s01125 | R | 2022-12-08 | New Firearm Tax Measure Introduced as Part of Trio of G | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (98%): New Firearm Tax Measure Introduced as Part of Trio of Gun Violence Prevention Bills |
| 04068 | s04545 | O | 2022-09-25 | Governor Newsom Signs California IDs For All Bill | news/community outlet running a release (coverage under the rule); release category tag: Press Release by CC News 09/25/2022 written by CC News 09/25/2022 11.9K Undocumented Californians |
| 04077 | s01167 | R | 2022-09-23 | Bill to Crack Down on Street Racing and Illegal Sidesho | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (99%): Bill to Crack Down on Street Racing and Illegal Sideshows Signed by Governor Californi |

### Lassen County Times (13), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 02826 | s00812 | O | 2023-10-22 | Newsom announces $30 million in additional state funds  | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (71%): Following the terrorist attacks against Israel and heightened concerns in the United S |
| 02859 | s00823 | R | 2023-10-18 | Newsom signs legislation to expedite housing services f | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (91%): This past week, Governor Gavin Newsom signed Assembly Bill 1386, by Assemblymember Jes |
| 03304 | s00935 | O | 2023-09-08 | California legislature passes landmark tax on firearm m | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (75%): Yesterday, the California Legislature passed Assembly Bill 28, a landmark measure that |
| 03345 | s00940 | O | 2023-09-05 | New tax on gun manufacturers and dealers advances to Se | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (75%): Today, the California State Senate Appropriations Committee voted to advance Assembly  |
| 03441 | s00969 | O | 2023-07-05 | Governor signs bill to strengthen domestic violence res | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (80%): Last week, Governor Gavin Newsom signed into law Assembly Bill 467, a bipartisan measu |
| 03926 | s01093 | R | 2023-03-18 | Bill to sustain outdoor dining across California would  | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (86%): Assemblymember Jesse Gabriel has introduced legislation to sustain outdoor dining acro |
| 03994 | s01125 | O | 2022-12-06 | New gun violence prevention bill introduced in Sacramen | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (79%): A new measure would impose excise taxes on the sale of guns and ammunition, |
| 04055 | s01157 | O | 2022-09-29 | Governor signs new law to strengthen California's water | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (88%): Against the backdrop of California's driest period in at least 1,200 years, Governor G |
| 04111 | s01179 | O | 2022-09-16 | Governor signs bill to strengthen California's response | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (80%): Governor Gavin Newsom signed legislation authored by Assemblymember Jesse Gabriel to h |
| 04139 | s01190 | O | 2022-08-31 | Legislature advances bill to combat homelessness by mak | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (90%): Last week, the California State Legislature approved a measure authored by Assemblymem |
| 04156 | s01196 | O | 2022-08-24 | Governor Newsom signs legislation to strengthen proacti | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (79%): Today, Governor Gavin Newsom signed into law a bill authored by Assemblymember Jesse G |
| 04161 | s01198 | O | 2022-08-23 | State legislature approves measure to strengthen Califo | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (76%): Today, the California state legislature passed legislation authored by Assemblymember  |
| 04468 | s01337 | O | 2021-09-30 | State officials hold virtual press conference on effort | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (84%): Today, as small restaurants across California struggle to remain open, Assemblymember  |

### East County Today (12), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 04070 | s04545 | R | 2022-09-25 | Governor Newsom Signs California IDs For All Bill | news/community outlet running a release (coverage under the rule); release category tag: Press Release by ECT Sep 25, 2022 written by ECT Sep 25, 2022 2K |
| 04078 | s04546 | O | 2022-09-23 | Bill to Crack Down on Street Racing and Illegal Sidesho | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (95%): Bill to Crack Down on Street Racing and Illegal Sideshows Signed by Governor East |
| 09149 | s03675 | O | 2022-09-13 | Governor Newsom Signs Landmark Social Media Transparenc | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (100%): Governor Newsom Signs Landmark Social Media Transparency Bill California Governor New |
| 09189 | s03714 | O | 2022-06-22 | Legislators and Community Leaders Call For Social Media | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (99%): Legislators and Community Leaders Call For Social Media Transparency Regarding Its Rol |
| 09207 | s03730 | O | 2022-05-25 | Senate Approves Increase toRenters Tax Credit On Overwh | news/community outlet running a release (coverage under the rule); release category tag: Press Release written by ECT May 25, 2022 SACRAMENTO – California’s poorest renters and |
| 09216 | s03738 | O | 2022-05-18 | State Assembly Advances Bill to Crack Down on Street Ra | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (100%): State Assembly Advances Bill to Crack Down on Street Racing and Illegal Sideshows Cal |
| 09270 | s03783 | O | 2022-02-16 | Bill Seeks to Strengthen and Equalize Penalties For Usi | news/community outlet running a release (coverage under the rule); release category tag: Press Release by ECT Feb 16, 2022 written by ECT Feb 16, 2022 2K |
| 04581 | s04588 | O | 2021-06-07 | California Assembly Passes Bill Requiring Prosecutors a | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (96%): California Assembly Passes Bill Requiring Prosecutors and Judges to Consider Costs of  |
| 04603 | s01392 | O | 2021-05-26 | State Superintendent Tony Thurmond, Senator Henry Stern | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO—State Superintendent of Public Instruction Tony Thurmond and Senator Henry Stern (D-Los Angeles) |
| 04760 | s01453 | O | 2020-09-30 | Governor Newsom Signs Legislation to Provide Affordable | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (92%): Governor Newsom Signs Legislation to Provide Affordable Housing for Teachers and Schoo |
| 09531 | s04031 | O | 2020-02-04 | Legislation Aims to Combat Imminent Loss of Affordable  | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (91%): Legislation Aims to Combat Imminent Loss of Affordable Housing - East County Today Cal |
| 05166 | s01614 | R | 2018-12-28 | Speaker Rendon Announces Assembly Leadership and Commit | news outlet, reported or rewritten text, no release signal; "Speaker Rendon Announces Assembly Leadership and Committee Assignments - East County Today California Speaker" |

### California Apartment Association (10), official

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 08624 | s03236 | O | 2023-10-26 | Package of CAA-supported housing bills signed by Gov. N | official site, but the text is the group's own news/blog post, not a release; "Package of CAA-supported housing bills signed by Gov. Newsom Gov. Gavin Newsom this month" |
| 09316 | s03828 | O | 2021-10-09 | Gov. Newsom vetoes eviction-delay legislation | official site, but the text is the group's own news/blog post, not a release; "Gov. Newsom vetoes eviction-delay legislation California Apartment Association · 2021-10-09 https://caanet.org/gov-newsom |
| 09353 | s03862 | O | 2021-08-18 | CAA members urge lawmakers to reject eviction-delay leg | official site, but the text is the group's own news/blog post, not a release; "CAA members urge lawmakers to reject eviction-delay legislation California Apartment Association · 2021-08-18 https://caa |
| 09367 | s03876 | O | 2021-07-15 | Eviction-defense bill on Senate floor, vote expected af | official site, but the text is the group's own news/blog post, not a release; "Eviction-defense bill on Senate floor, vote expected after summer recess Believe it or not," |
| 09370 | s03878 | O | 2021-07-09 | CAA-cosponsored housing appeal bill advances in Senate | official site, but the text is the group's own news/blog post, not a release; "CAA-cosponsored housing appeal bill advances in Senate Continuing its march toward the governor’s desk" |
| 09387 | s03894 | O | 2021-06-02 | CAA-cosponsored housing bill wins approval in Assembly | official site, but the text is the group's own news/blog post, not a release; "CAA-cosponsored housing bill wins approval in Assembly The state Assembly on Tuesday approved a" |
| 09400 | s03907 | O | 2021-04-28 | CAA-sponsored housing bills move unanimously out of com | official site, but the text is the group's own news/blog post, not a release; "CAA-sponsored housing bills move unanimously out of committees A key Assembly committee this week" |
| 09407 | s03913 | O | 2021-04-13 | CAA objects to eviction | official site, but the text is the group's own news/blog post, not a release; "CAA objects to eviction-defense fund in new legislation A bill introduced this year would" |
| 09527 | s04027 | O | 2020-02-18 | Bill would create tax credit aimed at keeping housing a | official site, but the text is the group's own news/blog post, not a release; "Bill would create tax credit aimed at keeping housing affordable A bill working its" |
| 09618 | s04096 | O | 2019-03-20 | Bill would authorize tenants to shelter families facing | official site, but the text is the group's own news/blog post, not a release; "Bill would authorize tenants to shelter families facing homelessness A newly introduced bill would" |

### Del Norte Triplicate (8), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 02770 | s00802 | O | 2023-11-03 | Newsom signs legislation to expedite housing services f | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (92%): This past week, Governor Gavin Newsom signed Assembly Bill (AB) 1386, by Assemblymembe |
| 02858 | s00823 | O | 2023-10-18 | Governor Newsom signs Legislation to expedite housing s | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (92%): This past week, Governor Gavin Newsom signed Assembly Bill (AB) 1386, by Assemblymembe |
| 02894 | s00833 | O | 2023-10-13 | Newsom signs tax on gun manufacturers | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (71%): California Governor Gavin Newsom signed into law the Gun Violence Prevention and Schoo |
| 03453 | s00974 | O | 2023-06-29 | California State Senate advances legislation to ban use | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (75%): Yesterday, the California State Senate Health Committee advanced first-of-its-kind leg |
| 03517 | s00991 | O | 2023-06-08 | California State Assembly advances bill to regulate vol | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (96%): Last week, the California State Assembly passed legislation that would establish new r |
| 03577 | s01007 | O | 2023-05-17 | CA state assembly passes legislation to ban use of dang | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (82%): Recently, the California State Assembly passed first-of-its-kind legislation that woul |
| 04325 | s01275 | O | 2022-01-10 | Newsom highlights new laws taking effect | news outlet, reported or rewritten text, no release signal; "Governor Gavin Newsom recently highlighted new bills signed into law in 2021 that went" |
| 04372 | s01299 | O | 2021-10-18 | Newsom signs K-12, broadband bills | news outlet, reported or rewritten text, no release signal; "Governor Gavin Newsom recently signed a suite of bills to increase K-12 student supports," |

### California Courier, The (6), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 02846 | s00816 | O | 2023-10-19 | CA Armenian Legislative Caucus Foundation Calls on Bide | news outlet, reported or rewritten text, no release signal; "The California Armenian Legislative Caucus Foundation sent a letter to President Joe Biden asking" |
| 04314 | s01266 | O | 2022-02-17 | California Establishes a Sister State Relationship with | news outlet, reported or rewritten text, no release signal; "The California State Senate passed resolution ACR 105, a resolution to establish sister-state relationship" |
| 04516 | s01352 | O | 2021-09-09 | California Legislators Announce Essay and Visual Arts S | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO-The California Armenian Legislative Caucus awarded six scholarships to California high school st |
| 04844 | s01495 | O | 2019-12-12 | At CSUN, ANI Exhibit features YMCA achievements to save | news/community outlet running a release (coverage under the rule); release dateline opening: LOS ANGELES-With coverage on local television stations, the Armenian National Institute (ANI) exhibit, high |
| 05122 | s01589 | O | 2019-03-14 | Assembly members Gabriel, Nazarian Unite Armenian & Jew | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (67%): LOS ANGELES-In response to recent hate incidents targeting Armenian and Jewish institu |
| 05264 | s01662 | O | 2018-04-19 | SCAD Announces Endorsements for 2018 Election Cycle | news/community outlet running a release (coverage under the rule); release dateline opening: GLENDALE, Calif.-Last week, the Southern California Armenian Democrats (SCAD) announced its official endors |

### Lake County News (6), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 01695 | s00470 | O | 2024-12-03 | State Legislature holds special session to jumpstart ef | news outlet, reported or rewritten text, no release signal; "The California State Senate, led by Senate President pro Tempore Mike McGuire (D-North Coast)," |
| 04109 | s01177 | O | 2022-09-17 | Governor signs sweeping climate measures; package aims  | news outlet, reported or rewritten text, no release signal; "On Friday, California enacted some of the nation's most aggressive climate measures in history" |
| 04332 | s01280 | O | 2021-12-29 | Governor's Office highlights new laws taking effect Jan | news outlet, reported or rewritten text, no release signal; "Gov. Gavin Newsom is highlighting a host of new bills he signed into law" |
| 04463 | s01334 | O | 2021-09-30 | Governor signs legislation to address homelessness and  | news outlet, reported or rewritten text, no release signal; "On Wednesday, Gov. Gavin Newsom signed a suite of bills to help address the" |
| 04754 | s01451 | O | 2020-09-29 | Governor signs 15 bills aimed at increasing housing pro | news outlet, reported or rewritten text, no release signal; "Gov. Gavin Newsom on Monday signed legislation that will help California make significant progress" |
| 04869 | s01510 | O | 2019-10-12 | Governor signs more than a dozen bills meant to protect | news outlet, reported or rewritten text, no release signal; "Gov. Gavin Newsom on Friday signed a package of 15 bills aimed at strengthening" |

### San Fernando Valley Sun, The (6), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 02905 | s00837 | O | 2023-10-12 | Landmark Legislation Banning Dangerous Food Additives S | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (52%): Gov. Gavin Newsom signed first-of-its-kind legislation Oct. 7 to prohibit the use of f |
| 02906 | s00838 | O | 2023-10-12 | Gov. Newsom Signs First-in-the-Nation Bill to Regulate  | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (60%): This past weekend, Gov. Gavin Newsom signed legislation to establish first-in-the-nati |
| 03092 | s00878 | O | 2023-09-28 | Gov. Newsom Signs Historic Tax on Gun Manufacturers | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (65%): Gov. Gavin Newsom signed into law the Gun Violence Prevention and School Safety Act |
| 04342 | s01286 | O | 2021-11-18 | Assemblymember Recognizes Valley Honorees for Positive  | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (82%): State Assemblymember Jesse Gabriel (D-Woodland Hills) hosted a special awards ceremony |
| 04377 | s01304 | O | 2021-10-14 | Governor Signs New Law Addressing Student Mental Health | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (50%): Amid continued concerns about the impact of the COVID-19 pandemic on youth mental heal |
| 04538 | s01362 | O | 2021-08-12 | Assemblymember Gabriel Secures $3.5 Million in State Fu | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (67%): State Assemblymember Jesse Gabriel (D-Woodland Hills) presented a check to the West Va |

### Van Nuys News Press (6), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 10653 | s04932 | O | 2026-10-27 | California Steps Up for Faith Communities, Enacts Law t | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (94%): California Steps Up for Faith Communities, Enacts Law to Prevent Public Meetings and G |
| 07020 | s01875 | R | 2026-10-04 | Governor Newsom Signs Six Jewish Caucus Priority Bills  | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (85%): Governor Newsom Signs Six Jewish Caucus Priority Bills Into Law Van Nuys News Press |
| 00052 | s00018 | O | 2026-10-02 | Amid Youth Mental Health Crisis, California and NBA Cha | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (95%): Amid Youth Mental Health Crisis, California and NBA Champion Team Up on New Law |
| 07059 | s01904 | O | 2026-09-29 | California Adopts Comprehensive Strategy to Prevent Hom | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (97%): California Adopts Comprehensive Strategy to Prevent Homelessness Before It Starts – Va |
| 00107 | s00035 | O | 2026-09-27 | Building on Success, California Strengthens Its Flagshi | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (100%): Building on Success, California Strengthens Its Flagship Violence Intervention Progra |
| 07812 | s02541 | O | 2025-05-14 | Speaker Robert Rivas, Budget Chair Jesse Gabriel Issue  | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (89%): Speaker Robert Rivas, Budget Chair Jesse Gabriel Issue Statements on Governor's May Re |

### Asbarez (5), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 07777 | s02515 | O | 2025-06-06 | ANCA-WR Provides Update on Legislative Efforts in Sacra | news outlet, reported or rewritten text, no release signal; "ANCA-WR Provides Update on Legislative Efforts in Sacramento - Asbarez.com Wednesday, October 21, 2026" |
| 08696 | s03301 | O | 2023-10-09 | California Legislators Call on President Joe Biden to S | news outlet, reported or rewritten text, no release signal; "California Legislators Call on President Joe Biden to Support Artsakh - Asbarez.com Wednesday, October" |
| 09615 | s04093 | O | 2019-04-02 | Divest Turkey Movement Gains New Momentum | news/community outlet running a release (coverage under the rule); release dateline opening: GLENDALE—The Divest Turkey movement, originally founded in 2014 by the Armenian Youth Federation-Western US |
| 09636 | s04114 | O | 2019-01-31 | Ferrahian, Manoogian Principals Thank Community for Sup | news outlet, reported or rewritten text, no release signal; "Ferrahian, Manoogian Principals Thank Community for Support after Hate Crimes - Asbarez.com Ferrahian, Manoogian" |
| 09649 | s04128 | O | 2018-10-12 | 1,000 Strong Capacity Crowd Celebrates the Armenian Cau | news/community outlet running a release (coverage under the rule); release dateline opening: LOS ANGELES—More than 1,000 activists, community leaders, public officials, supporters, and generous donors |

### Asian Journal (4), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 02020 | s00578 | R | 2024-08-01 | Governor Newsom announces $76M in grants to bolster saf | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO — California Governor Gavin Newsom on Tuesday, July 30 announced that California is |
| 02340 | s04431 | O | 2024-04-11 | Assemblymember Gabriel, Attorney General Bonta announce | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (95%): Assemblymember Gabriel, Attorney General Bonta announce legislation to increase penalt |
| 08868 | s03427 | O | 2023-07-19 | Governor signs bill to strengthen domestic violence res | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (99%): Governor signs bill to strengthen domestic violence restraining orders — SACRAMENTO —  |
| 08904 | s03462 | O | 2023-05-24 | California State Assembly passes landmark legislation t | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (89%): California State Assembly passes landmark legislation to ban use of dangerous chemical |

### Davis Vanguard (4), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 08402 | s03035 | O | 2024-05-02 | Jewish Caucus Condemns Total Failure by UCLA Leadership | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (99%): Jewish Caucus Condemns Total Failure by UCLA Leadership - Davis Vanguard Skip to conte |
| 08616 | s03228 | O | 2023-11-08 | Following Antisemitic Incidents on Campuses, California | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (97%): Following Antisemitic Incidents on Campuses, California Legislative Jewish Caucus Call |
| 09344 | s03853 | O | 2021-09-13 | Legislation Would Create Statewide Eviction Defense Pro | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO, CA — COVID-19 has exacerbated already concerning rates of eviction and homelessness, with |
| 09345 | s03854 | O | 2021-09-11 | Measure Passes Expanding CalFresh Food Benefits for Tho | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (95%): Measure Passes Expanding CalFresh Food Benefits for Thousands of California Students - |

### HeySoCal (4), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 02913 | s00842 | R | 2023-10-10 | Newsom signs bill to regulate voluntary carbon offsets | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (73%): Newsom signs bill to regulate voluntary carbon offsets Hey SoCal · 2023-10-10 https:// |
| 03306 | s04490 | O | 2023-09-08 | California legislature passes tax on gun manufacturers, | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (73%): California legislature passes tax on gun manufacturers, dealers Politics San Fernando  |
| 04378 | s04566 | O | 2021-10-08 | Gov. Newsom signs new law addressing student mental hea | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (77%): Gov. Newsom signs new law addressing student mental health crisis News Politics Top Po |
| 09432 | s03938 | O | 2021-02-18 | Proposed Legislation Aims to Support Restaurants Throug | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (67%): Proposed Legislation Aims to Support Restaurants Through More Outdoor Dining and Deliv |

### Oragark (4), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 07351 | s02143 | R | 2026-05-19 | ANCA-WR Announces 2026 Primary Endorsements | news/community outlet running a release (coverage under the rule); release dateline opening: LOS ANGELES – The Armenian National Committee of America, Western Region on Monday announced |
| 00692 | s00189 | R | 2026-01-15 | California Armenian Legislative Caucus Foundation New M | news outlet, reported or rewritten text, no release signal; "California Armenian Legislative Caucus Foundation New Member Announcement: Assemblymember Damon Connolly – Oragark Sacramento," |
| 01384 | s00373 | O | 2025-04-06 | California Armenian Legislative Caucus Foundation Annou | news outlet, reported or rewritten text, no release signal; "California Armenian Legislative Caucus Foundation Announces New Members: Assembly Speaker Robert Rivas and Senate" |
| 01424 | s00387 | R | 2025-03-14 | ANCA-WR and Northern California Chapter Advocate for Le | news outlet, reported or rewritten text, no release signal; "ANCA-WR and Northern California Chapter Advocate for Legislation in Sacramento – Oragark Oragark ·" |

### Lake County Record Bee (3), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 04085 | s01172 | O | 2022-09-20 | Legislation - Newsom signs bill to extend grant program | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (82%): SACRAMENTO >> Over the weekend, Gov. Gavin Newsom signed a bipartisan measure authored |
| 04509 | s01349 | O | 2021-09-11 | News briefs | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (71%): LAKEPORT Climate change ranks first in poll at Democratic Party’s County Fair booth Cl |
| 04580 | s01384 | O | 2021-06-04 | Criminal cases in California - Assembly passes bill req | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (77%): SACRAMENTO >> This week, the California State Assembly passed Assembly Bill (AB) 1474, |

### Santa Barbara Independent (3), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 00034 | s04297 | R | 2026-10-11 | State Approves $2.5 Million for Goleta Community Center | news/community outlet running a release (coverage under the rule); release dateline opening: GOLETA, CA, October 9, 2026 – The City of Goleta is pleased to announce |
| 01014 | s00266 | O | 2025-10-08 | California Governor Newsom Signs First-in-the-Nation Bi | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO, CA – California Governor Gavin Newsom signed legislation today that bans unhealthy ultra-proces |
| 08785 | s04672 | O | 2023-09-12 | California Legislature Passes First-in-the | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (96%): California Legislature Passes First-in-the-Nation Ban on Dangerous Additives Press rel |

### Common Sense Media (2), official

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 08621 | s03233 | O | 2023-10-30 | Five Major Legislative Wins for Kids in California | official site, but the text is the group's own news/blog post, not a release; "Five Major Legislative Wins for Kids in California Browse all articles Five Major Legislative" |
| 09115 | s03643 | O | 2022-10-06 | California Continues Its Leadership with Online Protect | official site, but the text is the group's own news/blog post, not a release; "California Continues Its Leadership with Online Protections for Kids and Families Common Sense Media" |

### Desert Review, The (2), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 03518 | s00991 | R | 2023-06-06 | California State Assembly advances bill to regulate vol | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (86%): California State Assembly advances bill to regulate voluntary carbon offsets SACRAMENT |
| 03928 | s01093 | O | 2023-03-19 | Bill to sustain outdoor dining across California | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (87%): Bill to sustain outdoor dining across California Jaime Honold, owner of Burgers & Beer |

### Edhat (2), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 00033 | s04297 | O | 2026-10-12 | California Awards $2.5 Million to Upgrade Goleta Commun | news outlet, reported or rewritten text, no release signal; "The City of Goleta is pleased to announce that $2.5 million in state funding" |
| 04233 | s01229 | O | 2022-05-26 | California Assembly Advances Gun Violence Prevention Pa | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (99%): Source: Office of Assemblymember Steve Bennett In the wake of another tragedy and inac |

### Encino Enterprise (2), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 00103 | s04299 | O | 2026-10-01 | Official State Seal for Non-Ultraprocessed Foods | outlet is a news outlet; no saved text |
| 08411 | s03045 | O | 2024-04-19 | Gabriel Applauds $6 Million in Security Grants for the  | outlet is a news outlet; no saved text |

### Noozhawk (2), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 00032 | s00009 | O | 2026-10-10 | State Approves $2.5 Million for Goleta Community Center | news outlet, reported or rewritten text, no release signal; "The city of Goleta has secured $2.5 million in state funding to support improvements" |
| 05099 | s01583 | O | 2019-04-23 | American Cancer Society Action Network Names Monique Li | news outlet, reported or rewritten text, no release signal; "Assemblywoman Monique Limón, D-Santa Barbara, has been named Legislator of the Year, by the" |

### Times-Herald (2), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 02169 | s00616 | R | 2024-06-07 | LEGISLATION - Dodd introduces restaurant fees bill | news/community outlet running a release (coverage under the rule); release dateline opening: LEGISLATION - Dodd introduces restaurant fees bill June 7, 2024 / Times-Herald (Vallejo, CA) |
| 04582 | s01385 | O | 2021-06-04 | Criminal cases in CALIFORNIA - Assembly passes bill req | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (52%): The California State Assembly passed assembly member Jesse Gabriel’s (D-Woodland Hills |

### Armenian Mirror-Spectator, The (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 01528 | s00423 | R | 2025-01-23 | California Armenian Legislative Caucus Requests Montebe | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO, Calif. — A January 23 letter signed by 36 members of the California |

### Beverly Press (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 01884 | s04917 | O | 2024-09-18 | Newsom signs legislation at Holocaust Museum LA | news outlet, reported or rewritten text, no release signal; "Newsom signs legislation at Holocaust Museum LA Beverly Press · 2024-09-19 https://beverlypress.com/2024/09/newsom-signs-legislation-at-hol |

### Culver City Observer (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 01883 | s00534 | O | 2024-09-19 | Governor Newsom signs legislation to help Holocaust sur | news outlet, reported or rewritten text, no release signal; "Governor Gavin Newsom visited the Holocaust Museum LA on Monday with David Cassirer and" |

### Daily Record, The (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 00287 | s00078 | O | 2026-07-13 | Play Equity Fund Secures $4 Million in State Funding fo | news/community outlet running a release (coverage under the rule); wire tag: GLOBE NEWSWIRE) -- Cheers and excitement filled the room as dozens of children and |

### Gethsemane, The (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 07169 | s01996 | O | 2026-09-06 | California Passes 'Non-Ultra-Processed' Food Label Bill | news/community outlet running a release (coverage under the rule); release dateline opening: SACRAMENTO – Today the California Legislature took a major step toward protecting public health |

### Highpoint Digest (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 01978 | s04402 | R | 2024-08-29 | California Governor Signs New Laws to Help Communities  | news outlet, reported or rewritten text, no release signal; "California Governor Signs New Laws to Help Communities Address Homelessness Highpoint Digest · 2024-08-29" |

### Jewish Times (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 03962 | s01112 | O | 2023-01-27 | California Jewish Caucus Statement on International Hol | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (85%): Today, we mark International Holocaust Remembrance Day, and the anniversary of the lib |

### Jewish World Watch (1), official

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 09096 | s03624 | O | 2022-12-02 | JWW’s Serena Oberstein named Activist of the Year by As | official site, but the text is the group's own news/blog post, not a release; "JWW’s Serena Oberstein named Activist of the Year by Asm. Jesse Gabriel JWW’s Serena" |

### Los Angeles Daily News (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 04995 | s04611 | O | 2019-07-24 | News | news outlet, reported or rewritten text, no release signal; "“Many of these veterans continued to serve after they hung up the uniform —" |

### Madera Tribune (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 04076 | s01167 | O | 2022-09-21 | Governor signs to crack down on street racing | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (87%): SACRAMENTO - Governor Gavin Newsom signed Assembly Bill (AB) 2000, which will prohibit |

### Organic & Non-GMO Report, The (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 07653 | s02404 | O | 2025-09-24 | California lawmakers pass first-in-nation bill to prote | news outlet, reported or rewritten text, no release signal; "California lawmakers pass first-in-nation bill to protect kids from harmful ultra-processed foods in schools" |

### Our Weekly (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 00253 | s00068 | O | 2026-08-31 | California Advances Comprehensive Strategy to PreventHo | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (95%): Today, the California State Legislature passed Assembly Bill (AB) 1924, statewide legi |

### PanARMENIAN.Net (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 04907 | s01521 | O | 2019-09-12 | California Senate passes Turkish Divestment Bill | news outlet, reported or rewritten text, no release signal; "The California State Senate passed the Turkish Divestment Bill, AB 1320, on September 11," |

### Pasadena Independent (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 02912 | s00842 | O | 2023-10-12 | Newsom signs first-in-the-nation bill to regulate volun | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (64%): This past weekend, Governor Gavin Newsom signed legislation to establish firstin-the-n |

### Precinct Reporter (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 02827 | s04467 | O | 2023-10-19 | Funding to Protect Vulnerable Amid Mideast Violence | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (92%): Funding to Protect Vulnerable Amid Mideast Violence Precinct Reporter Group News · 202 |

### Press, The (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 09927 | s04748 | O | 2025-03-26 | Newsom announces record $76 million to safeguard local  | news outlet, reported or rewritten text, no release signal; "Newsom announces record $76 million to safeguard local faith communities and nonprofits Brentwood News" |

### Redlands Community News (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 02339 | s00674 | O | 2024-04-13 | Legislation calls for penalties for corporate malfeasan | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (69%): Assemblymember Jesse Gabriel (D-Encino) joined California Attorney General Rob Bonta a |

### Reporter, The (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 02170 | s00616 | O | 2024-06-07 | LEGISLATION - Bill Dodd introduces Restaurant Fees Bill | news/community outlet running a release (coverage under the rule); release dateline opening: LEGISLATION - Bill Dodd introduces Restaurant Fees Bill June 7, 2024 / Reporter, The |

### Riverbank News, The (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 04759 | s01453 | R | 2020-09-30 | Affordable Teacher Housing Gets Legislative Assistance | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (68%): Governor Gavin Newsom on Sept. 28 signed into law Assembly Bill (AB) 3308, by |

### Shooting News Weekly (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 01175 | s00317 | O | 2025-07-18 | Has Gavin Newsom Undergone a Miraculous Road to Damascu | news outlet, reported or rewritten text, no release signal; "Has Gavin Newsom Undergone a Miraculous Road to Damascus Gun Rights Conversion? California Gov." |

### Southern California Record, The (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 01869 | s00527 | O | 2024-09-27 | Attorney General Bonta Issues Statement on Legislation  | news/community outlet running a release (coverage under the rule); "issued the following" wording: issued the following statement in response to Governor Gavin Newsom signing into law Assembly (Publis |

### True North Radio Network (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 00288 | s00078 | R | 2026-07-13 | Play Equity Fund Secures $4 Million in State Funding fo | news/community outlet running a release (coverage under the rule); wire tag: GLOBE NEWSWIRE) -- Cheers and excitement filled the room as dozens of children and |

### Ukiah Daily Journal (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 04510 | s01349 | R | 2021-09-11 | News Briefs | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (71%): LAKEPORT Climate change ranks first in poll at Democratic Party’s County Fair booth Cl |

### Valley News Group (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 08413 | s03046 | O | 2024-04-19 | Day of Service Creates "World's Biggest Lasagna" for An | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (85%): Day of Service Creates "World's Biggest Lasagna" for Angelenos in Need Valley News Gro |

### Willits News, The (1), news

| Article | Story | O/R | Date | Headline | Reason |
|---|---|---|---|---|---|
| 04576 | s01381 | R | 2021-06-05 | LEGISLATION - Assembly passes legislation to strengthen | news/community outlet running a release (coverage under the rule); word-for-word match with a release text (92%): Last week, the California State Assembly passed legislation that aims to significantly |

## Unsure (19)

| Article | Story | O/R | Date | Outlet | Headline | Reason |
|---|---|---|---|---|---|---|
| 04556 | s01372 | R | 2021-07-07 | California Alcohol Policy Alliance | MEDIA ADVISORY: Los Angeles Says: Too Much Alcohol on T | official outlet but no saved text to check |
| 07180 | s02003 | O | 2026-09-03 | Inner City Law Center | ICLC به عنوان حامی مشترک لایحه پیشگیری از بی‌خانمانی AB | official outlet but no saved text to check |
| 09129 | s03657 | O | 2022-09-19 | JPAC | Governor Signs Community Security Bill | official outlet but no saved text to check |
| 07354 | s02146 | O | 2026-05-14 | PublicNow | Budget Chair Jesse Gabriel, Speaker Robert Rivas | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |
| 07313 | s02112 | O | 2026-06-04 | PublicNow | California State Assembly Democratic Caucus | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |
| 07284 | s02091 | O | 2026-06-23 | PublicNow | California State Leaders Announce Historic Constitution | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |
| 07285 | s02092 | O | 2026-06-23 | PublicNow | California leaders announce Save for California's Futur | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |
| 07272 | s02081 | O | 2026-06-26 | PublicNow | California Leaders Announce Balanced Budget Agreement . | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |
| 07273 | s02082 | O | 2026-06-26 | PublicNow | California Legislature Places Constitutional Amendment  | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |
| 07253 | s02065 | O | 2026-07-01 | PublicNow | California Legislative Central Coast Caucus Announces . | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |
| 07219 | s02036 | O | 2026-08-11 | PublicNow | Equality California Condemns Final CMS Rule Blocking .. | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |
| 07094 | s01935 | O | 2026-09-26 | PublicNow | Building on Success, California Strengthens Its Flagshi | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |
| 07092 | s01933 | O | 2026-09-28 | PublicNow | California Becomes First State to Create an Official .. | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |
| 07082 | s01923 | O | 2026-09-29 | PublicNow | California Adopts Comprehensive Strategy to Prevent ... | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |
| 07083 | s01924 | O | 2026-09-29 | PublicNow | New Laws: Assembly Democrats are Leading the Nation in  | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |
| 07038 | s01893 | O | 2026-09-30 | PublicNow | New California Law Protects Affordable Housing from ... | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |
| 07029 | s01884 | O | 2026-10-01 | PublicNow | Governor signs Pacheco bill to strengthen mental health | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |
| 07018 | s01874 | O | 2026-10-02 | PublicNow | Amid Youth Mental Health Crisis, California and NBA ... | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |
| 07002 | s01859 | O | 2026-10-07 | PublicNow | California Legislative Central Coast Caucus Issues ... | wire (mirrors releases) but no saved text (page was blocked); headline reads like a release |

## Keep Yes: one line per outlet

- **Targeted News Service** (161, wire): wire + release text; "issued the following" wording: issued the following news release: *** Sep 30, 2026 Governor Newsom issues legislative update
- **US Fed News** (40, wire): wire + release text; "issued the following" wording: issued the following news release: The City of Goleta is pleased to announce that
- **TendersInfo - News** (13, wire): wire + release text; "issued the following" wording: issued the following statement in response to Governor Gavin Newsom signing Assembly Bill (AB) [12 weaker calls]
- **PR Newswire** (11, wire): wire + release text; wire tag: PRNewswire/ -- Today, Anheuser-Busch [NYSE: BUD], a leading American manufacturer and maker of Michelob
- **Hispanic PR Newswire** (9, wire): wire + release text; wire tag: PRNewswire-HISPANIC PR WIRE/ -- Décadas de evidencia demuestran que la venta de alcohol a
- **ForeignAffairs** (7, wire): wire + release text; release category tag: MIL-OSI USA: Congressman Sherman Hosts 2nd Telephone Town Hall of 2022 February 9, 2022
- **Yahoo News** (4, aggregator): wire release syndicated on Yahoo News; wire tag: PRNewswire/ -- Today, Anheuser-Busch [NYSE: BUD], a leading American manufacturer and maker of Michel
- **ANCA Western Region** (3, official): official site + release-style text (statement or dateline); "Calif. Armenian Legislative Caucus Welcomes 2 New Members Email Donate Take action Armeni
- **Jewish California** (3, official): official + release text; release dateline opening: LOS ANGELES, CA – Less than a year after a protest outside Wilshire Boulevard
- **Business Wire** (2, wire): wire; release text from the issuer (no explicit tag, weaker call); "Holocaust Museum LA, the first survivor founded and oldest Holocaust Museum in the [2 weaker calls]
- **California Newswire** (2, wire): wire + release text; release category tag: Section: Office of the Calif. Governor 1016 Words OpenURL Link SACRANEBTO, Calif. /California Newswire/ [1 weaker calls]
- **Consumer Reports** (2, official): official + release text; release category tag: Press Release California Governor Newsom signs first-in-the-nation bill banning harmful ultra-processed
- **ENP Newswire** (2, wire): wire + release text; wire tag: ENPNEWSWIRE-September 18, 2026--Anheuser-Busch Invests $21 Million in Los Angeles, CA Facilities, Expands Local Manufac
- **Financial Services Monitor Worldwide** (2, wire): wire + release text; wire tag: (GlobeNewswire) - Cheers and excitement filled the room as dozens of children and supporters
- **Targeted News Service: U.S. Business** (2, wire): wire + release text; "issued the following" wording: issued the following news release: *** Anheuser-Busch Invests $21 Million in Los Angeles, CA
- **U.S. Newswire** (2, wire): wire + release text; wire tag: PRNewswire/ -- The Ricardo Lara for Insurance Commissioner Campaign is proud to announce endorsements
- **AOL** (1, aggregator): wire release syndicated on AOL; wire tag: PRNewswire/ -- Today, Anheuser-Busch [NYSE: BUD], a leading American manufacturer and maker of Michelob
- **California Environmental Voters** (1, official): official + release text; FOR IMMEDIATE RELEASE: FOR IMMEDIATE RELEASE CONTACT: Stefanie Lao, [email protected] | 424.282.0922 Oakland, CA – California
- **Contify Energy News** (1, wire): wire + release text; "issued the following" wording: issued the following news release: Clean Power Alliance board directors and staff joined trade
- **GlobeNewswire** (1, wire): wire + release text; wire tag: GLOBE NEWSWIRE) -- Gov. Gavin Newsom today signed AB 2142, which will reinstate the
- **Jewish Federation of the Greater East Bay** (1, official): official site + release-style text (statement or dateline); "Federation and JCRC Joint Statement on Colleyville and our Communal Efforts | Jewish Fede
- **Jewish World Watch** (1, official): official + release text; release category tag: Press Release: Gala honoring Uyghur leader Nury Turkel raises money for anti-genocide work Press
- **Liberty Counsel** (1, official): official + release text; release dateline opening: SACRAMENTO, CA -- California State Assemblyman Jesse Gabriel has proposed a bill that would
- **M2 Presswire** (1, wire): wire + release text; wire tag: M2 PRESSWIRE-March 12, 2024-: Eretz Cultural Center Hosts Inaugural Luncheon to Celebrate Community Heroes
- **PR.com** (1, wire): wire + release text; wire tag: ( PR.com)-- Feel The Bern San Fernando Valley Democratic Club will co- sponsor a
- **Real Estate Monitor Worldwide** (1, wire): wire; release text from the issuer (no explicit tag, weaker call); "This morning Metro broke ground on an early utility relocation phase for planned l [1 weaker calls]
- **Steinberg Institute** (1, official): official site + release-style text (statement or dateline); "Assemblymembers Advance Long-Term Solutions to Address Homelessness Steinberg Institute ·
- **Targeted News Service: Public Colleges and Universities** (1, wire): wire + release text; "issued the following" wording: issued the following news release: *** What they're saying: California Jewish Leaders support the
- **Targeted News Service: U.S. House of Representatives** (1, wire): wire + release text; "issued the following" wording: issued the following news release on March 26, 2021: Last night, over 3,800 Valley
- **Targeted News Service: U.S. Senate** (1, wire): wire + release text; "issued the following" wording: issued the following news release: On Sunday, Congressman Brad Sherman hosted a Valley Town
- **UCSF Undocumented Student Program** (1, official): official + release text; FOR IMMEDIATE RELEASE: FOR IMMEDIATE RELEASE Media Contact: Dan Loeterman, 617-921-7025, dan@cerrell.com Dreamers Sue to Bloc

All rows with verdicts, signals and overlap scores: `work/localapp/PRESS_RELEASE_YES_REVIEW.csv`.
