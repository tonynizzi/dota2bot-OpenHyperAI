"""Patch 7.42 compatibility checks.

Static checks cover removed abilities/items and the neutral and XP tables. The
Roshan respawn estimate and the Invoker skill-list builder run the production
Lua in Lua 5.1. None of this replaces an in-game check.
"""
import re
import unittest

from test_bot_regressions import ROOT, LuaRuntime, function


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def code_only(text):
    """Strip Lua block comments and line comments (good enough for these files)."""
    text = re.sub(r"--\[\[.*?\]\]", "", text, flags=re.S)
    return "\n".join(line.split("--", 1)[0] for line in text.splitlines())


# 7.42 neutral pools (Valve itemlist neutral_item_tier, 1-based here)
POOLS = {
    1: {"item_chipped_vest", "item_ash_legion_shield", "item_possessed_mask", "item_dormant_curio",
        "item_red_ledger", "item_weighted_dice", "item_polliwog_charm", "item_seeds_of_serenity",
        "item_foragers_kit", "item_kobold_cup", "item_stonefeather_satchel", "item_pogo_stick"},
    2: {"item_psychic_headband", "item_safety_bubble", "item_metamorphic_mandible", "item_jidi_pollen_bag",
        "item_brick", "item_crippling_crossbow", "item_imp_claw", "item_gunpowder_gauntlets",
        "item_defiant_shell", "item_partisans_brand", "item_spellslinger", "item_mana_draught"},
    3: {"item_prophets_pendulum", "item_dandelion_amulet", "item_idol_of_screeauk", "item_balmhook",
        "item_rattlecage", "item_stormcrafter", "item_enchanters_bauble", "item_ceremonial_robe",
        "item_harmonizer", "item_vile_phial", "item_serrated_shiv", "item_revenants_brooch"},
    4: {"item_fallen_sky", "item_flicker", "item_minotaur_horn", "item_mind_breaker",
        "item_divine_regalia", "item_heavy_blade", "item_helm_of_the_hivemind", "item_dezun_bloodrite",
        "item_conjurers_catalyst", "item_giants_ring", "item_demonicon", "item_riftshadow_prism"},
}


class Patch742(unittest.TestCase):
    def test_removed_abilities_not_referenced(self):
        removed = {
            "bots/BotLib/hero_meepo.lua": ["meepo_megameepo"],
            "bots/BotLib/hero_juggernaut.lua": ["juggernaut_swift_slash", "abilityD"],
            "bots/BotLib/hero_chen.lua": ["chen_summon_convert", "SummonConvert"],
            "bots/FunLib/spell_list.lua": ["meepo_megameepo", "juggernaut_swift_slash", "chen_summon_convert"],
        }
        for path, names in removed.items():
            code = code_only(read(path))
            for name in names:
                self.assertNotIn(name, code, f"{path} still uses {name}")

    def test_weaver_ally_time_lapse_uses_new_ability(self):
        code = code_only(read("bots/BotLib/hero_weaver.lua"))
        self.assertIn("weaver_time_lapse_ally", code)
        self.assertNotIn("Action_UseAbilityOnEntity(TimeLapse,", code)

    def test_doom_talent_lookup_is_nil_guarded(self):
        code = code_only(read("bots/BotLib/hero_doom_bringer.lua"))
        uses = len(re.findall(r"DevourAncientTalent:IsTrained\(\)", code))
        guarded = len(re.findall(r"DevourAncientTalent\s*~=\s*nil\s+and\s+DevourAncientTalent:IsTrained\(\)", code))
        self.assertEqual(uses, guarded)

    def test_builds_have_no_removed_items(self):
        gone = ["item_angels_demise", "item_helm_of_the_overlord", "item_javelin", "item_great_scepter"]
        for path in sorted((ROOT / "bots/BotLib").glob("hero_*.lua")):
            code = code_only(path.read_text(encoding="utf-8"))
            for item in gone:
                self.assertNotIn(f'"{item}"', code, f"{path.name} buys {item}")
                self.assertNotIn(f"'{item}'", code, f"{path.name} buys {item}")

    def test_new_items_expand_into_components(self):
        code = code_only(read("bots/FunLib/aba_item.lua"))
        for item in ["item_caduceus", "item_ristuls_devotion", "item_skypiercer", "item_starforge",
                     "item_berserkers_sabatons", "item_bloodslinger"]:
            self.assertRegex(code, r"Item\[\s*[\"']" + item + r"[\"']\s*\]\s*=\s*GetItemComponents")
        for item in ["item_angels_demise", "item_helm_of_the_overlord", "'item_javelin'"]:
            self.assertNotIn(item, code)

    def test_buff_neutral_tiers_match_742(self):
        text = re.sub(r"--\[\[.*?\]\]", "", read("bots/Buff/NeutralItems.lua"), flags=re.S)
        found, tier = {}, None
        for line in text.splitlines():
            m = re.match(r"\s*local Tier(\d)NeutralItems", line)
            if m:
                tier = int(m.group(1))
                continue
            if line.strip().startswith("}"):
                tier = None
            if tier is None or line.strip().startswith("--"):
                continue
            for name in re.findall(r"\"(item_[a-z0-9_]+)\"", line.split("--", 1)[0]):
                found.setdefault(tier, set()).add(name)
        self.assertEqual(found, POOLS)

    def test_fretbots_neutral_tiers_match_742(self):
        found = {}
        for line in read("bots/FretBots/SettingsNeutralItemTable.lua").splitlines():
            m = re.match(r"\s*\{name=\"(item_[a-z0-9_]+)\",\s*tier=(\d)", line)
            if m and "enhancement" not in m.group(1):
                found.setdefault(int(m.group(2)), set()).add(m.group(1))
        self.assertEqual(found, POOLS)

    def test_fretbots_neutral_settings_have_four_tiers(self):
        text = read("bots/FretBots/SettingsDefault.lua")
        for key in ["maxPerTier", "timings", "timingsDefault"]:
            m = re.search(key + r"\s*=\s*\{([^}]*)\}", text)
            self.assertIsNotNone(m, key)
            self.assertEqual(len([v for v in m.group(1).split(",") if v.strip()]), 4, key)

    def test_xp_tables_reach_66600(self):
        buff = read("bots/Buff/Experience.lua")
        per = [int(v) for v in re.findall(r"\[\s*\d+\s*\]\s*=\s*(\d+)", buff)]
        self.assertEqual(sum(per), 66600)
        m = re.search(r"local xpPerLevel =\s*\{(.*?)\}", read("bots/FretBots/AwardBonus.lua"), re.S)
        cumulative = [int(v) for v in re.findall(r"\d+", m.group(1))]
        self.assertEqual((len(cumulative), cumulative[1], cumulative[-1]), (30, 250, 66600))

    def test_roshan_respawn_window_shrinks_with_kills(self):
        source = read("bots/FunLib/jmz_func.lua")
        start = source.index("local killTime = 0.0")
        end = source.index("\nend", source.index("function J.IsRoshanAlive()")) + 4
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute("""
            J = {}; now = 0; kill = 0; turbo = false
            function DotaTime() return now end
            function GetRoshanKillTime() return kill end
            function J.IsModeTurbo() return turbo end
        """ + source[start:end])
        g = lua.globals()
        def alive(kill_time, now):
            g.kill, g.now = kill_time, now
            return g.J.IsRoshanAlive()
        self.assertTrue(alive(0, 100))
        # first kill: 11 minute worst case
        self.assertFalse(alive(600, 600 + 10 * 60))
        self.assertTrue(alive(600, 600 + 11 * 60 + 1))
        # second kill: base 7 min + 3 min variance
        self.assertFalse(alive(2000, 2000 + 9 * 60))
        self.assertTrue(alive(2000, 2000 + 10 * 60 + 1))
        # later kills bottom out at 5 + 3 minutes
        for k in range(3, 8):
            alive(2000 + k * 1000, 2000 + k * 1000)
        self.assertFalse(alive(9000, 9000 + 7 * 60))
        self.assertTrue(alive(9000, 9000 + 8 * 60 + 1))

    def test_invoker_skill_list_spends_three_bonus_orb_points(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute("""
            X = {}
            local name = 'npc_dota_hero_invoker'
            function GetBot() return { GetUnitName = function() return name end } end
        """ + function("bots/FunLib/aba_skill.lua", "X.GetSkillList"))
        g = lua.globals()
        abilities = lua.table("Q", "W", "E", "x", "x", "R")
        talents = lua.table(*["t%d" % i for i in range(1, 9)])
        build = lua.table(*([1, 2, 3] * 8))
        talent_build = lua.table(*range(1, 9))
        skills = g.X.GetSkillList(abilities, build, talents, talent_build)
        out = [skills[i] for i in range(1, len(skills) + 1)]
        self.assertEqual(len(out), 32)
        self.assertEqual(out[9], "t1")
        self.assertEqual(out[27], "t4")  # level-25 talent comes after all 24 orb points
        self.assertEqual(sum(1 for s in out if s in ("Q", "W", "E")), 24)


if __name__ == "__main__":
    unittest.main()
