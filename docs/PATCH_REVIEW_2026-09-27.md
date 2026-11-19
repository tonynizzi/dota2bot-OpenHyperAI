# Targeted patch maintenance, September 27, 2026

Valve's latest listed gameplay patch is 7.41f, announced September 15, after our September 13 playtest review. This pass repairs the specific compatibility and reliability issues below. It is not a full compatibility sign-off for every hero or for the outstanding 7.41b–e changes.

## Implemented

- **Treant Leech Seed:** removed ground-target selection and dispatch. Combat, retreat, Roshan, and Tormentor paths return a unit and dispatch a unit-target cast. The spell is an attack: decisions use the bot's live attack range and decline while disarmed, unaffordable/on cooldown, or lacking unit-target behavior. Its new mana cost is handled by `IsFullyCastable()`. The old healing-area radius is no longer used to choose a ground location.
- **Bounty Hunter:** removed the obsolete talent-slot reference and historical slot table. Shuriken damage decisions read the live `bonus_damage` once. No unrelated talent value or separately hardcoded +190 is added. The current Valve ability data associates the +190 bonus with `special_bonus_unique_bounty_hunter_2`, now at level 20. Whether the bot API's live special includes that bonus must still be verified in-game; the cast trace records the relevant value and named-talent state.
- **Roshan:** nearby-fight checks use `J.GetCurrentRoshanLocation()` for both day and night. Ordinary readiness now follows each executed DPS check and can become false again, then recover. Invalid cached Roshan handles are discarded and nearby Roshan is reacquired. The existing early low-health finish path and underlying DPS formula are unchanged.
- **Diagnostics:** optional sampled cast attempts with script revision/path, configured client patch, hero, ability/item, order and target type, inventory slot, and suspected mismatches. See [ACTION_DIAGNOSTICS.md](ACTION_DIAGNOSTICS.md). This does not claim to attribute the old engine errors conclusively.

## Talent/build review

Checked Bounty Hunter and Earth Spirit against Valve's current talent data and the actual `GetTalentBuild()` mapping, rather than assuming that a pair's visual left/right label establishes its slot.

- Bounty Hunter's existing builds select talent-list entries 6 and 8 at levels 20 and 25: Jinada gold steal and no cooldown on Jinada. They do not select the moved Shuriken/Track-vision talents at those levels. The damage fix is still needed for later leveling or user-customized builds. No speculative build change was made.
- Earth Spirit's existing level-20/25 choices are entries 5 and 7: Magnetize damage and self-Magnetize. Those preferences remain coherent after 7.41f. No code assumes the old stone-charge progression or manually adds the replaced Rolling Boulder talent in the inspected handler. Damage-special completeness remains part of wider hero validation, not established here.
- Treant's selected level-10 entry is the base-damage talent, so the changed Living Armor duration talent does not require a preference swap. Leech Seed's mana check reads the live cost.

## Evidence

Read on September 27, 2026:

- [Valve patch list](https://www.dota2.com/datafeed/patchnoteslist?language=english) and [7.41f announcement](https://www.dota2.com/newsentry/677383425371407609?l=english).
- [7.41f patch payload](https://www.dota2.com/datafeed/patchnotes?version=7.41f&language=english), plus structural-note review of b–e during the preceding assessment.
- Valve current hero payloads: [Treant](https://www.dota2.com/datafeed/herodata?language=english&hero_id=83), [Bounty Hunter](https://www.dota2.com/datafeed/herodata?language=english&hero_id=62), [Earth Spirit](https://www.dota2.com/datafeed/herodata?language=english&hero_id=107).
- Extracted game definitions cross-check: [Treant](https://raw.githubusercontent.com/dotabuff/d2vpkr/master/dota/scripts/npc/heroes/npc_dota_hero_treant.txt), [Bounty Hunter](https://raw.githubusercontent.com/dotabuff/d2vpkr/master/dota/scripts/npc/heroes/npc_dota_hero_bounty_hunter.txt). These are moving community mirrors, not a pinned installed-client snapshot.
- [Bot API](https://docs.moddota.com/lua_bots/) for action forms, behavior flags, and ability inspection. Liquipedia hero-page requests returned 403; they were not treated as verified evidence.

## Verification and remaining work

All 39 Lua 5.1/Node/Python regression checks pass, including 12 new tests for these repairs and diagnostics. The Roshan readiness test now checks loss and recovery rather than preserving the old permanent latch. The earlier 16 branch scenarios retain their expected first-return reasons; separate tests distinguish the two pit locations. Mocked tests do not establish win rate, actual map coordinates, or live talent-special semantics.

This pass edits hand-written Lua only; it does not change generated TypeScript-owned Lua or the Workshop release version. Existing September working-tree repairs are preserved.

Next playtest: confirm the session header, exercise Treant with clustered enemies and objectives, record Shuriken before/after the damage talent, and inspect Roshan samples across a death/retreat and both day/night pits. Keep FretBots and lobby settings fixed. Larger objective coordination, participant-aware DPS, mode tuning, and complete 7.41b–f compatibility remain separate work.
