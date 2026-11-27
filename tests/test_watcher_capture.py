"""Watcher capture in BOT_MODE_OUTPOST, run against the shipped mode file with engine mocks."""
import unittest
from test_bot_regressions import LuaRuntime, ROOT, function, source


MOCKS = """
now = 100
function DotaTime() return now end
BOT_MODE_DESIRE_NONE = 0; BOT_ACTION_DESIRE_NONE = 0
BOT_ACTION_DESIRE_VERYLOW = 0.1; BOT_ACTION_DESIRE_LOW = 0.25
BOT_ACTION_DESIRE_MODERATE = 0.5; BOT_ACTION_DESIRE_HIGH = 0.75
BOT_MODE_DESIRE_MODERATE = 0.5; BOT_MODE_DESIRE_HIGH = 0.75
BOT_MODE_DEFEND_ALLY = 99; BOT_MODE_NONE = 0
TOWER_TOP_2, TOWER_MID_2, TOWER_BOT_2 = 3, 4, 5
UNIT_LIST_ALL = 1
TEAM_RADIANT, TEAM_DIRE, TEAM_NEUTRAL = 2, 3, 4
function GetTeam() return TEAM_RADIANT end
function GetOpposingTeam() return TEAM_DIRE end
function GetTower() return {} end
function GetTeamPlayers() return {5, 6} end
lastSeen = {}
function GetHeroLastSeenInfo(id) return lastSeen[id] end
function RemapValClamped(x, a, b, c, d)
    return c + math.max(0, math.min(1, (x-a)/(b-a))) * (d-c)
end
local function dist(a, b) return math.sqrt((a.x-b.x)^2 + (a.y-b.y)^2) end
function GetUnitToUnitDistance(a, b) return dist(a:GetLocation(), b:GetLocation()) end
function GetUnitToLocationDistance(a, l) return dist(a:GetLocation(), l) end
printed = {}
function print(s) table.insert(printed, s) end
function GetScriptDirectory() return 'bots' end

Unit = {}
Unit.__index = Unit
function Unit:GetUnitName() return self.name end
function Unit:GetLocation() return self.loc end
function Unit:GetTeam() return self.team end
function Unit:IsNull() return self.null or false end
function Unit:IsHero() return self.hero or false end
function Unit:IsBuilding() return self.building or false end
function Unit:IsAlive() return true end
function Unit:IsInvulnerable() return self.invuln or false end
function Unit:IsAttackImmune() return self.attackImmune or false end
function Unit:IsIllusion() return false end
function unit(t) return setmetatable(t, Unit) end

lamp = {name='ability_lamp_use'}
bot = unit({name='npc_dota_hero_lion', hero=true, loc={x=0, y=0}, team=TEAM_RADIANT})
actions = {}; channeling = false; recentlyDamaged = false; activeMode = BOT_MODE_NONE
function bot:GetPlayerID() return 0 end
function bot:GetAbilityByName(n) if n == 'ability_lamp_use' then return lamp end end
function bot:WasRecentlyDamagedByAnyHero() return recentlyDamaged end
function bot:GetActiveMode() return activeMode end
function bot:GetActiveModeDesire() return 0 end
function bot:GetCurrentVisionRange() return 1800 end
function bot:IsChanneling() return channeling end
function bot:Action_MoveToLocation(l) table.insert(actions, {'move', l}) end
function bot:Action_UseAbilityOnEntity(a, t) table.insert(actions, {'cast', a.name, t}) end
function bot:Action_AttackUnit(t) table.insert(actions, {'attack', t}) end
function GetBot() return bot end

units = {}
function GetUnitList() return units end

position = 5; laning = false; hp = 1; enemies = {}; retreating = false
J = {Utils = {}}
function J.Utils.IsTeamPushingSecondTierOrHighGround() return false end
function J.Utils.IsBotThinkingMeaningfulAction() return false end
function J.GetEnemiesAroundAncient() return 0 end
function J.GetPosition() return position end
function J.IsInLaningPhase() return laning end
function J.GetHP() return hp end
function J.IsRetreating() return retreating end
function J.IsDoingRoshan() return false end
function J.IsDoingTormentor() return false end
function J.IsDefending() return false end
function J.IsGoingOnSomeone() return false end
function J.GetProperTarget() return nil end
function J.IsValidTarget() return false end
function J.IsTormentor() return false end
function J.IsRoshan() return false end
function J.IsAttacking() return false end
function J.GetNumOfAliveHeroes() return 5 end
function J.CanNotUseAction() return false end
-- Mirrors the real helper: rejects buildings, which is why the mode must not use it on Watchers.
function J.IsValid(u) return u ~= nil and not u:IsNull() and not u:IsBuilding() end
function J.GetDistance(a, b) return dist(a, b) end
function J.GetEnemiesNearLoc(l, r)
    local out = {}
    for _, e in ipairs(enemies) do if dist(e.loc, l) <= r then table.insert(out, e) end end
    return out
end
Customize = {ThinkLess = 1}
function require(path)
    if string.find(path, 'jmz_func', 1, true) then return J end
    return Customize
end

function watcher(x, team)
    return unit({name='npc_dota_lantern', loc={x=x, y=0}, team=team or TEAM_NEUTRAL,
                 building=true, invuln=true, attackImmune=true})
end
"""


class WatcherCapture(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(MOCKS)

    def load(self):
        self.lua.execute(source("bots/mode_outpost_generic.lua"))

    def run_lua(self, code):
        self.lua.execute(code)

    def test_support_lights_nearby_neutral_watcher_once(self):
        self.run_lua("w = watcher(800); units = {w}")
        self.load()
        self.run_lua("""
            local d = GetDesire(); assert(d > 0 and d <= BOT_ACTION_DESIRE_MODERATE, d)
            Think(); assert(actions[1][1] == 'move', 'walks toward a far Watcher first')
            bot.loc = {x=500, y=0}
            assert(GetDesire() > 0); Think()
            local a = actions[#actions]
            assert(a[1] == 'cast' and a[2] == 'ability_lamp_use' and a[3] == w, 'casts lamp use on the Watcher')
            channeling = true; now = now + 0.2; assert(GetDesire() >= BOT_MODE_DESIRE_HIGH); Think()
            now = now + 1.0; channeling = false; GetDesire(); Think()
            assert(GetDesire() == 0, 'a Watcher we lit is not targeted again')
            now = now + 421
            assert(GetDesire() > 0, 'it becomes a target again after the 420s active window')
        """)
        self.assertTrue(any("lit watcher" in str(p) for p in self.lua.globals().printed.values()))

    def test_unsafe_or_owned_watchers_are_ignored(self):
        self.run_lua("w = watcher(600); units = {w}")
        self.load()
        self.run_lua("""
            enemies = {unit({name='npc_dota_hero_axe', hero=true, loc={x=1500, y=0}})}
            assert(GetDesire() == 0, 'visible enemy near the Watcher')
            enemies = {}
            lastSeen[6] = {{time_since_seen=2, location={x=900, y=0}}}
            assert(GetDesire() == 0, 'enemy seen near the Watcher in the last 5s')
            lastSeen = {}
            retreating = true; assert(GetDesire() == 0, 'retreating'); retreating = false
            recentlyDamaged = true; assert(GetDesire() == 0, 'in a fight'); recentlyDamaged = false
            hp = 0.3; assert(GetDesire() == 0, 'low health'); hp = 1
            activeMode = BOT_MODE_DEFEND_ALLY; assert(GetDesire() == 0, 'defending an ally'); activeMode = BOT_MODE_NONE
            w.team = TEAM_RADIANT; assert(GetDesire() == 0, 'already ours')
            w.team = TEAM_NEUTRAL; assert(GetDesire() > 0, 'safe neutral Watcher is wanted')
        """)

    def test_cores_only_take_watchers_right_next_to_them(self):
        self.run_lua("w = watcher(1500); units = {w}; position = 1")
        self.load()
        self.run_lua("""
            assert(GetDesire() == 0, 'core does not detour 1500 units')
            w.loc = {x=500, y=0}
            laning = true; assert(GetDesire() == 0, 'core keeps laning'); laning = false
            assert(GetDesire() > 0, 'core grabs an adjacent Watcher after laning')
            position = 4; w.loc = {x=1900, y=0}
            assert(GetDesire() > 0, 'support detours further')
        """)

    def test_enemy_watcher_is_turned_off_and_failed_casts_back_off(self):
        self.run_lua("w = watcher(300, TEAM_DIRE); other = unit({name='npc_dota_creep_neutral', loc={x=100, y=0}}); units = {other, w}")
        self.load()
        self.run_lua("""
            assert(GetDesire() > 0); Think()
            assert(actions[#actions][3] == w, 'never targets a non-Watcher unit')
            channeling = true; now = now + 0.1; GetDesire(); Think()
            now = now + 1.0; channeling = false; GetDesire(); Think()
            assert(GetDesire() == 0, 'turned-off Watcher is untargetable for a while')
            now = now + 121; w.team = TEAM_NEUTRAL
            assert(GetDesire() > 0); Think()
            now = now + 3.5; GetDesire(); Think()
            assert(GetDesire() == 0, 'cast that never channelled backs off')
            now = now + 31
            assert(GetDesire() > 0, 'and retries after the cooldown')
        """)
        printed = [str(p) for p in self.lua.globals().printed.values()]
        self.assertTrue(any("turned off enemy watcher" in p for p in printed))
        self.assertTrue(any("never started channelling" in p for p in printed))

    def test_trace_logs_nearby_unattackable_units(self):
        self.run_lua("w = watcher(300); units = {w}")
        self.load()
        self.run_lua("GetDesire(); GetDesire()")
        lines = [str(p) for p in self.lua.globals().printed.values() if "unit name=" in str(p)]
        self.assertEqual(len(lines), 1, lines)
        self.assertTrue(lines[0].startswith("[OHA_WATCHER] "))
        self.assertIn("name=npc_dota_lantern team=4 invuln=true attackImmune=true matched=true", lines[0])

    def test_watcher_trace_survives_global_print_filter(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute('Utils={DebugMode=false}; output={}; '
                    'function orig_print(s) table.insert(output,s) end')
        lua.execute(function('bots/FunLib/aba_global_overrides.lua', 'print'))
        lua.execute("print('ordinary'); print('[OHA_WATCHER] t=1'); "
                    "assert(#output==1 and output[1]=='[OHA_WATCHER] t=1')")

    def test_farm_mode_still_filters_watchers(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(MOCKS)
        lua.execute("X = {}; function Unit:CanBeSeen() return true end")
        lua.execute(function('bots/mode_farm_generic.lua', 'X.FilterAttackable'))
        lua.execute("""
            local creep = unit({name='npc_dota_neutral_kobold', loc={x=0, y=0}})
            local out = X.FilterAttackable({watcher(100), creep})
            assert(#out == 1 and out[1] == creep)
        """)


if __name__ == "__main__":
    unittest.main()
