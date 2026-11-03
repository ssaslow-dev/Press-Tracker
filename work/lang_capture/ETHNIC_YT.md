# Ethnic-language station YouTube sweep (2026-11-03)

Searches: 45 or fewer TinyFish calls (include_domains youtube.com), about 40 used. Hits found only in Chinese (Latin "Jesse Gabriel" plus 眾議員 or 天下衛視) and Spanish (asambleísta). Pure native-script Korean, Armenian, Persian, Russian and Vietnamese queries, and channel-name queries (NTD, ETTV, SBTN, Iran International, Manoto, KBS America, MBC, Arirang, SBS, Univision/Estrella/LATV), returned nothing relevant or noise. Korean "제시 가브리엘 주하원의원" did hit (KBS, VOA Korean). native_add.json appeared only after the sweep and was not used.
Channels read by YouTube oEmbed only; dates are from titles or snippets (oembed has no date).

## Counts (14 videos reviewed)
- new: 3 (KBS News; Sky Link TV Cantonese gun-law segment; VOA Korean, unverified because the snippet doesn't name him)
- same_segment: 5 (4 CA Today vs NTD Television rows 09007, 08974, 08262, 08036; 1 Sky Link Mandarin copy of tracked 10667)
- in_tracker: 4 (10667, 08480, 08470, 10668)
- dropped: 1 (邓洪说法 lawyer channel)
- Not counted: Telemundo eñe/tildes video (ZHs1KqjYRFs) never named him in the snippet.

## Findings
1. The real gaps are channel mappings, not missed stories: `Noticias Telemundo` (the network channel; only "Telemundo 52" is mapped) and CA Today are absent from youtube.channels, so yesterday's sweep left CA Today as NEW although each video matches an NTD row.
2. Truly new stories: KBS News 2024-12-03 (Korea Times 08059 and Korea Economic Daily 08031 run the same item, so only the KBS row is missing); Sky Link Cantonese gun-law segment (date needs a watch-page check).
3. Sky Link TV has two channels (Cantonese, Mandarin); the same segment is uploaded to both.
4. No Armenian, Persian, Russian or Vietnamese station videos surfaced; YouTube search by native-script name returns music/noise.

## Add to recall_sources youtube.channels
| channel name (author_name) | handle | outlet | medium | language |
|---|---|---|---|---|
| Noticias Telemundo | noticias | Noticias Telemundo | TV | Spanish |
| CA Today 今日加州 | catoday4157 | NTD Television | TV | Chinese |
| Sky Link TV Mandarin News 天下衛視 國語新聞頻道 | SkyLinkTVnewsM | Sky Link TV | TV | Chinese |
| KBS News | newskbs | KBS News | TV | Korean |
| VOA 한국어 | VOAKorea | VOA Korean | TV/online | Korean (add only after the Gabriel mention is confirmed) |

The existing Sky Link Cantonese key has a trailing space in the oEmbed author_name; match after trimming.
Do not add 邓洪说法 (@DengLaw, lawyer commentary).

CSV: ethnic_yt.csv (same folder).
