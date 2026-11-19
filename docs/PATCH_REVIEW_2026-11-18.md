# Patch review: 7.42 (and leftover 7.41b–f), November 18, 2026

Valve released **7.42 on November 18, 2026**, a major patch. The bots were last fully updated for 7.41a; the [September 27 pass](PATCH_REVIEW_2026-09-27.md) only repaired a few 7.41f issues. Findings are grouped by severity, and each one cites the file and line to change. Line numbers refer to the code before the fixes.

## Status (same day): P0 and P1 implemented

Everything in P0 and P1 below has been implemented and checked with `luac -p` and the test suite (81 tests, including 11 new ones in `tests/test_patch_742.py`). **None of it has been run in-game.** P2 (new abilities, the remaining new items' logic, minion abilities, talent re-picks) is still open.

How the implementation differs from the text below, or goes beyond it:
- **Replacement items:**
  - Khanda → Caduceus for Bounty Hunter and Zeus (both already buy Phylactery).
  - Khanda → Eye of Skadi for Luna and Morphling pos 1.
  - Khanda → Daedalus for Morphling pos 2.
  - Khanda → Ethereal Blade for Tinker.
  - Helm of the Overlord → Ristul's Devotion for Beastmaster and Lycan. For Lycan this replaces the Vladmir's line.
  - Beastmaster's farm milestone (`aba_site`, Lua and TS) now checks Helm of the Dominator.
- **New 7.42 items:** all six new items are registered in `aba_item.lua`, so they expand into components. Caduceus reuses the Force Staff handler and Skypiercer the Halberd handler. Bloodslinger, Ristul's Devotion, Sabatons and Starforge have no active logic yet.
- **Aether Lens:** the cast-range bonus used by item logic changed from 250 to 200.
- **Greater Horn of Battle:** picked up by a nearby bot (`mode_team_roam_generic.lua`). It is used while pushing or defending, or after it has been held for 60s. It is only used from the main inventory.
- **Roshan:** the first kill keeps the 11-minute worst case, then each kill shortens it by a minute, down to 8 (5 + 3). Turbo stays at 6 minutes (unverified).
- **Tormentor:** first spawn at 15:00, and 7.5 in turbo (assumed half).
- **Dire fountain:** moved by an estimated 300 units toward the Ancient, in `jmz_func.lua`, `ability_item_usage_generic.lua`, `utils.lua` and `utils.ts`. **Verify these coordinates in-game.**
- **Neutral items:**
  - Buff tiers come out at 0/15/30/50 min (turbo 0/7.5/15/25).
  - FretBots `timings` = `{0, 420, 1020, 2400}` is a judgment call.
  - `FretBots/BonusTimers.lua` was also made 4-tier, otherwise it would compare against nil.
  - Both award paths now skip any item that `CreateItem` returns nil for.
- **Doom:** ancient Devour now comes from Aghanim's Shard (7.42 KV `can_target_ancient`), as well as the nil-guarded talent.
- **Leshrac Nihilism:** cast to disarm right-clickers near him, or to self-dispel when he is rooted or slowed.
- **Invoker:** both orb builds now have 24 entries. `aba_skill.lua` learns the three bonus orb points before the level-25 talent.

Still to check in-game: the fountain coordinates; turbo Roshan and Tormentor timers; whether `weaver_time_lapse_ally` is trained automatically with Scepter; Float specials (Medusa, Disruptor, Nyx); the ward and site vectors near the moved mid towers; Glyph charges. README/CLAUDE.md still say 7.41a and should be updated once in-game testing confirms this pass.

**Sources:** Valve datafeed (`patchnoteslist`, `patchnotes?version=7.42` and `7.41b`–`7.41f`, `itemlist`, `abilitylist`, `herodata`) and d2vpkr hero KV at the 7.42 commit (`5efc826`). Liquipedia returned 403 and was not used. Note that Valve's `itemlist`/`abilitylist` still contain removed entries (e.g. `item_angels_demise`, `meepo_megameepo`), so presence there does not prove something still exists; the patch notes do.

**Talent slots:** `GetTalentBuild` (`bots/FunLib/aba_skill.lua:135`) maps `{0,10}` → slots 1/3/5/7 and `{10,0}` → 2/4/6/8. The talent picks below assume `GetTalentList`'s slot order matches herodata's order. Confirm that in-game before changing preferences.

---

## P0: crashes or broken core behavior

| # | Area | Problem | Fix |
|---|---|---|---|
| 1 | **Meepo** | MegaMeepo was removed in 7.42. `hero_meepo.lua:161-162,186-187` get nil, and `MegaMeepo:IsTrained()` at `:704` errors every tick in `SkillsComplement` (`:212`), so Earthbind (`:219`) is never reached. | Delete the MegaMeepo/Fling handles, the calls (`:212-217`, `:228-232`), the functions (`:703-776`), and `FunLib/spell_list.lua:477-478`. |
| 2 | **Juggernaut** | Swiftslash was removed; Scepter now upgrades Blade Fury. `hero_juggernaut.lua:133` `abilityD = sAbilityList[4]`; `X.ConsiderD` (`:510-575`) runs first once Jugg has Scepter (Jugg buys it at `:56`). It either errors on nil or targets the wrong ability. | Remove `abilityD` and ConsiderD (`:166-175`, `:510-575`), plus `spell_list.lua:341`. Optional: cast Fury more readily with Scepter, since it can now attack while moving. |
| 3 | **Chen** *(pre-7.42)* | `chen_summon_convert` no longer exists. `hero_chen.lua:149` gets nil, and `:492` `SummonConvert:IsFullyCastable()` errors, which blocks Holy Persuasion and Divine Favor. | Remove `:149`, `:181-186`, `:491+`, and `spell_list.lua:130`. |
| 4 | **Doom** *(pre-7.42)* | `special_bonus_unique_doom_2` (`hero_doom_bringer.lua:130`) no longer exists. `:311` `:IsTrained()` errors whenever an ancient creep is the Devour pick. | Nil-guard it, or drop the branch. |
| 5 | **Removed items in builds** | Khanda (`item_angels_demise`) is in the builds for Bounty Hunter `:67,90,113`, Luna `:42`, Morphling `:60,74`, Tinker `:38,58` and Zeus `:49,85`. Helm of the Overlord is in Beastmaster `:76` and Lycan `:92`. `Item.GetComponentList` falls back to treating them as basic items, so purchases fail (spam or skip, depending on `GetItemStockCount`). | Replace them. Khanda → e.g. `item_devastator`/`item_caduceus`/`item_kaya_and_sange` per hero. Overlord → `item_helm_of_the_dominator` or `item_ristuls_devotion`. Also clean up `aba_item.lua:154` (Javelin), `:785`, `:810`; `aba_site.lua:1104` **and** `typescript/bots/FunLib/aba_site.ts`; the dead handler at `ability_item_usage_generic.lua:2988`; and the `aba_chat.lua` entries. |
| 6 | **Neutral items (both systems)** | Tiers went from 5 to 4 (T1 0:00, T2 15:00, T3 30:00, T4 50:00). 13 cycled-out items are still awarded, 12 new ones are missing, and about 20 items have the wrong tier (details below). If `CreateItem` returns nil for a removed item, FretBots may error. | Rebuild `Buff/NeutralItems.lua` **and** `FretBots/SettingsNeutralItemTable.lua` from the 7.42 pools. Make `FretBots/SettingsDefault.lua:63,68,70` (`maxPerTier`, `timings`, `timingsDefault`) 4-tier, and remove the Buff tier-5 block (`Buff/NeutralItems.lua:123+`, `:299-312`), retiming the others. |
| 7 | **Weaver** | Scepter Time Lapse on an ally is now a separate ability, `weaver_time_lapse_ally`. `hero_weaver.lua:112-114,499-501` casts the self-only base ability on an ally, so the save never works. | Get `weaver_time_lapse_ally` and use it in the HasScepter branch (it shares a cooldown with the base ability). |
| 8 | **Leshrac** | Nihilism was reworked: it no longer makes Leshrac ethereal, and now disarms and basic-dispels in 550. `ConsiderNihilism` (`hero_leshrac.lua:943-970`) still fires as an "ethereal save" against incoming attacks. | Re-trigger it when right-clickers are within the radius, or to self-dispel roots and slows. Fall back to 550 if the `radius` key returns 0. |

### Neutral item details (verified against Valve's `itemlist` `neutral_item_tier`)
- **Cycled out (remove):** Dagger of Ristul, Duelist Gloves, Occult Bracelet, Essence Ring, Medallion of Courage, Poor Man's Shield, Searing Signet, Cloak of Flames, Flayer's Bota, Giant's Maul, Unrelenting Eye, Spider Legs, Stygian Desolator (`item_desolator_2`).
- **New (add):** T1 Red Ledger. T2 Brick, Imp Claw, Safety Bubble. T3 Balmhook, Ceremonial Robe, Revenant's Brooch, Vile Phial. T4 Flicker, Giant's Ring, Helm of the Hivemind, Mind Breaker. Buff is also missing Forager's Kit and Psychic Headband.
- **Retier:**
  - Pogo Stick and Seeds of Serenity: 2→1.
  - Gunpowder Gauntlets, Jidi Pollen Bag, Spellslinger, Partisan's Brand and Psychic Headband: 3→2.
  - Metamorphic Mandible: 4→2.
  - Rattlecage, Idol, Dandelion, Enchanter's Bauble and Prophet's Pendulum: 4→3.
  - Harmonizer: 5→3.
  - Book of the Dead, Fallen Sky, Minotaur Horn, Divine Regalia, Riftshadow Prism, Dezun Bloodrite and Witchbane: 5→4.
- **Enchantments:**
  - Alert, Brawny, Mystical, Quickened and Tough: tiers 1-3.
  - Vital: 1-2.
  - Crude, Keen-eyed, Nimble and Titanic: 2-3.
  - Greedy: 3 only.
  - Evolved, Timeless, Audacious, Feverish, Fleetfooted, Hulking, Manic and Vampiric: 4.

---

## P1: wrong values or behavior (no crash)

### Global / map
- **XP tables are stale.**
  - `Buff/Experience.lua:8-37` (per level): set `[1]=250,[3]=550,[4]=800,[5]=850,[6]=925,[7]=1050,[8]=1150,[9]=1225,[10]=1300,[11]=1375,[12]=1450,[13]=1525,[14]=1600,[15]=1675,[16]=1750,[17]=1825`. The rest is unchanged.
  - `FretBots/AwardBonus.lua:23-54` (cumulative) was already outdated before 7.42. Its 7.42 values are `0,250,650,1200,2000,2850,3775,4825,5975,7200,8500,9875,11325,12850,14450,16125,17875,19700,21600,23600,25800,28200,30800,33600,36600,40600,45600,51600,58600,66600`.
- **Roshan respawn:** the base timer now drops 1 minute per kill, to a minimum of 5. `J.IsRoshanAlive` (`jmz_func.lua:4971-4983`) always waits 11 minutes, so bots will be late to later Roshans. Count kills and shorten the window (verify the turbo values in-game).
- **Tormentor:** first spawn moved from 20:00 to 15:00. Update `mode_side_shop_generic.lua:65` (check the turbo value in-game). Tormentor now drops a **Greater Horn of Battle** (`item_horn_of_battle_greater`). Nothing picks it up (`mode_team_roam_generic.lua:1445+` only handles aegis, cheese and refresher shard) or uses it (it is no-target, global, and summons mega creeps in every lane).
- **Dire fountain moved about 300 units toward the Ancient.** The hardcoded `jmz_func.lua:9` `DireFountain` and `utils.lua:708` `DireFountainTpPoint` are now stale. `utils.lua` is TS-generated, so edit `typescript/bots/FunLib/utils.ts`. Prefer a runtime lookup.
- **Mid T1/T2 towers moved** (about 260-350 units) and the safelane camp boxes changed. The hardcoded ward and site vectors (`aba_ward_utility.lua`: 192 vectors, `aba_site.lua`: 47) near mid and safelane need an in-game spot check.
- **Glyph** now has 2 charges and a 7s cooldown between uses. `UseGlyph` (`ability_item_usage_generic.lua:8308`) probably still works; check it doesn't burn both charges at once.

### Item actives with hardcoded ranges
- Heaven's Halberd: `ability_item_usage_generic.lua:2884` uses 700; the real range is 500.
- Essence Distiller: about `:4544` uses 950; the real range is 850.
- Witchbane (7.41d): `:6494` uses 500; the real range is 700.

Use `hItem:GetCastRange()` for all three.

### Heroes
- **Kez:**
  - `hero_kez.lua:309`: `echo_hero_damage` no longer exists. Use `echo_base_damage`.
  - `:503`: Raptor Dance is now **Physical**, not Pure.
  - `:494,502`: `GetSpecialValueInt('max_health_damage_pct')` truncates the decimal percentage and is never divided by 100. Use Float/100, and drop `GetAttackDamage()`, since the attacks now deal fixed damage.
- **Medusa:** Gorgon's Grasp is now magical, so change `DAMAGE_TYPE_PHYSICAL` at `hero_medusa.lua:248`. The 0.8s `delay` (`:225`) and the `duration` read need `GetSpecialValueFloat`.
- **Disruptor:** `hero_disruptor.lua:507` reads `formation_time` (now 0.5) as an Int, which gives 0. Use Float.
- **Nyx:** `hero_nyx_assassin.lua:197` reads Impale `duration` (1.25-1.75) as an Int. Also check that `max_mana_as_damage_pct` (`:381`) still exists.
- **Brewmaster:** `hero_brewmaster.lua:199` casts Liquid Courage on a *location* with an ally handle. Use `UseAbilityOnEntity`. Unrelated bug at `:204-207`: it casts PrimalSplit where it should cast PrimalCompanion.
- **Monkey King:** with Shard, Boundless Strike now jumps to the target point. The retreat branch (`hero_monkey_king.lua:268-287`) would land him on the chaser. Skip that branch when he has Shard.
- **Lone Druid Bear:** the Scepter disarm range is now 1300, no longer global. Remove the Scepter exemption at `hero_lone_druid_bear.lua:107-110`, and consider `mode_roam_generic.lua:21` (1100).
- **Abaddon:**
  - `hero_abaddon.lua:208`: `self_damage` no longer exists. The variable is unused, so delete it.
  - `:207`: `target_damage` was already invalid and returns 0, which disables the kill-secure branch. Use `damage_heal`.
- **Talent-value bugs** (`talentN:GetSpecialValueInt("value")` now reads an unrelated talent, or 0):
  - Shadow Fiend `hero_nevermore.lua:391` (and `:206`).
  - Phantom Lancer `hero_phantom_lancer.lua:171`.
  - Lina `hero_lina.lua:213-214,225,237,250,517`.
  - **Dazzle** `hero_dazzle.lua:389`: now adds the Nothl cooldown talent to Poison Touch damage.
  - Ogre Magi `:212,246`, which uses slot 8 for a level-20 talent.

  Delete these, or look the talent up by name. Linked talents are usually already folded into the ability's value.
- **Primal Beast:** Rock Throw is now `base_damage` + 100% Strength (`damage_str_pct`). Update `hero_primal_beast.lua:517`.
- **Crystal Maiden:** Crystal Clone radius 450→425 (`hero_crystal_maiden.lua:933`).
- **Phantom Assassin:** Blur vanish radius 500→600 (`hero_phantom_assassin.lua:723` uses 740; use about 840). Existing bugs at `:734-736`: `nAllies` is fetched with the enemy flag, and the table `nEnemyTowers` is compared with `== 0`.
- **Shadow Fiend:** Requiem now has a base fear of 1.2-1.8s. The 10-soul gate (`hero_nevermore.lua:325-328`) can be relaxed. Tuning only.
- **Leftover 7.41b–f:**
  - Spectre Shadow Step's range is a flat 1000, but `hero_spectre.lua:570,591-625` searches 1600.
  - Tusk Drinking Buddies (`hero_tusk.lua:298`) and Underlord Fiend's Gate (`hero_abyssal_underlord.lua:384`) need `bot:IsRooted()` guards.
  - Invoker gets 3 bonus ability points (levels 6/12/18), which the 21-entry orb builds (`hero_invoker.lua:24-25`) don't account for.

---

## P2: new content the bots don't use (feature gaps)

- **New items** (no build or active logic yet):
  - Bloodslinger: point AoE, shares cooldown with Blood Grenade.
  - Caduceus: Force Staff active plus empowered unit-target spells.
  - Ristul's Devotion: aura, the Vladmir upgrade.
  - Sabatons of Mordiggian (`item_berserkers_sabatons`): Armlet-style toggle.
  - Skypiercer: Halberd disarm.
  - Starforge: Meteor Hammer active.

  Quarterstaff is back as a component; it is already listed at `aba_item.lua:164`. Recipes changed for Bloodthorn, Butterfly, Crimson Guard, Abyssal, Harpoon, Halberd, Maelstrom, MoM, MKB, Corrosion and Witch Blade. These resolve through `GetItemComponents()`, so no change is needed. Solar Crest can now self-cast at 50% effect (`:4418` only targets allies).
- **New neutral actives:** Red Ledger (no target), Brick (unit target). Flicker already has a handler (`:6191`).
- **New or castable hero abilities that are never cast:**
  - Beastmaster `beastmaster_summon_thunderhide` (Scepter).
  - Chaos Knight `chaos_knight_armageddon` (innate, point, needs a Phantasm illusion).
  - Undying `undying_bite` (Shard).
  - Chen Zealot active.
  - Meepo Divided We Stand (Shard) and its fling.
  - Dazzle `dazzle_through_the_realm` (Shard).
  - Lone Druid Bear `lone_druid_spirit_bear_summon_druid` (Scepter).
  - Venomancer `venomancer_snakebite` (since 7.41c; Venomous Gale still exists and is handled. `PATCH_UPDATE_GUIDE.md:493` is wrong to call Snakebite a summary error).
  - Pugna Scepter Oblivion Savant charges: avoid replacing a live Nether Ward, and avoid re-draining the same target.
- **Dominated and summoned creeps** (`FunLib/minion_lib/minion_with_skill.lua`):
  - Mud Golem now has `mud_golem_hurl_big_boulder`.
  - `black_dragon_fireball` is now the arcing Searing Swoop.
  - Kobold Soldier Steal Weapon is now an active line attack.
  - New creeps aren't handled: Radigull, Odobenus, Eimermole, Ogre Seal.
  - Warpine and the medium Centaur camp are gone, which is harmless in the Chen (`:334-339`), Enchantress (`:377-382`) and `jmz_func.lua:6360` lists.
- **Talent preferences to re-pick** (no crash; slot contents changed):
  - Anti-Mage t10.
  - Lion t15.
  - Invoker build 1 t20 (`{0,10}`).
  - Naga t20/t25: she may now take both cooldown talents or both illusion talents.
  - Death Prophet, Pugna, Dazzle and Ancient Apparition: most tiers.
  - Leshrac t20/t25.
  - Venomancer, Nature's Prophet t15/t20, Gyrocopter t15/t25, Nyx t25, Medusa t10/t15.
  - Abaddon t15/t25, Techies t10, Arc Warden t20, Meepo t15.

---

## Incidental pre-existing bugs
- `hero_tidehunter.lua:77`: `item_great_scepter` is not a real item. Delete it.
- `hero_beastmaster.lua:163,201`: `beastmaster_summon_raptors` should be `beastmaster_summon_raptor`. The `sAbilityList` fallback currently rescues it.

## Not covered / needs runtime verification
- Nothing here has been run in-game. Mocked tests cannot confirm talent slot order, new ability names on the live client, Float vs Int specials, or turbo timers.
- Global 7.42 changes the API absorbs automatically and that need no code: Item Potency, pip health, spell power reduction, BKB magic resistance on piercing spells, bounty and gold changes.

## Docs to update after fixes
- Set `PATCH_UPDATE_GUIDE.md` "Last updated for" to 7.42, and correct its Snakebite note (`:493`).
- Update `ARCHITECTURE.md` neutral tier count (5→4).
