"""Execute shipped Lua functions with small engine mocks using Lupa's Lua 5.1.

Install: python -m pip install lupa==2.6
Run: python -m unittest discover -s tests -v
Set OHA_TEST_REVISION=HEAD to demonstrate failures against the original code.
"""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "temp_build/python-deps"))
from lupa.lua51 import LuaRuntime


def source(path):
    revision = os.environ.get("OHA_TEST_REVISION")
    if revision:
        return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT).decode("utf-8")
    return (ROOT / path).read_text(encoding="utf-8")


def function(path, name):
    # These production functions have an unindented declaration and closing end.
    match = re.search(r"^function " + re.escape(name) + r"\([^\n]*\).*?^end\b",
                      source(path), re.M | re.S)
    if not match:
        raise AssertionError(f"Function not found: {path}:{name}")
    return match.group()


COMMON = """
now = 10
function DotaTime() return now end
function GameTime() return now end
BOT_MODE_DESIRE_NONE = 0
BOT_MODE_DESIRE_MODERATE = 0.5
BOT_MODE_DESIRE_ABSOLUTE = 1
BOT_MODE_NONE = 0
function RemapValClamped(x, a, b, c, d)
    return c + math.max(0, math.min(1, (x-a)/(b-a))) * (d-c)
end
function GetUnitToUnitDistance(a, b) return b.distance or 100 end
function GetUnitToLocationDistance(a, b) return b.distance or 1000 end
function unit(id)
    return setmetatable({id=id, distance=100, alive=true}, {__index={
        GetPlayerID=function(s) return s.id end,
        GetUnitName=function() return 'npc_dota_hero_axe' end,
        IsAlive=function(s) return s.alive end,
        IsNull=function() return false end,
        IsHero=function() return true end,
        IsIllusion=function() return false end,
        IsInvulnerable=function() return false end,
        HasModifier=function(s) return s.double or false end,
        GetTeam=function() return 2 end,
        SetTarget=function(s,t) s.target=t end,
        GetLocation=function() return {} end,
    }})
end
bot=unit(0)
botName=bot:GetUnitName()
function GetBot() return bot end
function GetTeam() return 2 end
function GetScriptDirectory() return 'bots' end
J={Utils={}}
function require() return J end
"""


class BotRegressions(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(COMMON)

    def test_nearby_filter_uses_candidate_for_both_observer_types(self):
        self.lua.execute(function("bots/FunLib/jmz_func.lua", "J.GetNearbyHeroes"))
        self.lua.execute("""
            real=unit(1); double=unit(2); double.double=true
            function J.IsValidHero(u) return true end
            function J.IsMeepoClone(u) return false end
            function bot:GetNearbyHeroes() return {real,double} end
            for _,isDouble in ipairs({false,true}) do
                bot.double=isDouble
                local result=J.GetNearbyHeroes(bot,1000,true)
                assert(#result==1 and result[1]==real)
            end
        """)

    def test_mixed_units_include_every_creep_without_mutating_inputs(self):
        self.lua.execute(function("bots/FunLib/jmz_func.lua", "J.GetAroundBotUnitList"))
        self.lua.execute("""
            local h,c1,c2,c3=unit(1),unit(2),unit(3),unit(4)
            for _,heroes in ipairs({{}, {h}}) do
                for _,creeps in ipairs({{}, {c1,c2,c3}}) do
                    function J.GetNearbyHeroes() return heroes end
                    function bot:GetNearbyCreeps() return creeps end
                    local n=#heroes
                    local result=J.GetAroundBotUnitList(bot,1000,true)
                    assert(#result==n+#creeps)
                    for i,c in ipairs(creeps) do assert(result[n+i]==c) end
                    assert(#heroes==n)
                    assert(result~=heroes and result~=creeps)
                end
            end
        """)

    def load_cache(self):
        self.lua.execute("____exports={GameStates={}}")
        for name in ["SetCachedVars", "GetCachedVars"]:
            self.lua.execute(function("bots/FunLib/utils.lua", "____exports." + name))

    def test_cache_preserves_false_zero_and_expiry(self):
        self.load_cache()
        self.lua.execute("""
            for _,value in ipairs({false,0,true}) do
                ____exports.SetCachedVars('key',value)
                assert(____exports.GetCachedVars('key',1)==value)
                now=now+1.01
                assert(____exports.GetCachedVars('key',1)==nil)
            end
            assert(____exports.GetCachedVars('missing',1)==nil)
        """)

    def test_team_indices_and_player_liveness_on_both_sides(self):
        self.load_cache()
        self.lua.execute(function("bots/FunLib/utils.lua", "____exports.IsTeamPushingSecondTierOrHighGround"))
        self.lua.execute("""
            BotMode={None=0}
            function GetAncient() return {} end
            function GetOpposingTeam() return 3 end
            function ____exports.IsNearEnemySecondTierTower(u) return u.qualifies end
            function ____exports.IsNearEnemyHighGroundTower() return false end
            for _,offset in ipairs({0,5}) do
                for selected=1,5 do
                    ____exports.GameStates={}
                    local players,members={},{}
                    for i=1,5 do
                        players[i]=offset+i-1
                        members[i]=unit(players[i]); members[i].distance=5000
                        members[i].qualifies=i==selected
                        members[i].GetNearbyHeroes=function() return {1,2} end
                    end
                    function GetTeamPlayers() return players end
                    function IsHeroAlive(id) return id==players[selected] end
                    function GetTeamMember(index)
                        assert(index>=1 and index<=5,'invalid team index')
                        return members[index]
                    end
                    assert(____exports.IsTeamPushingSecondTierOrHighGround(bot)==true)
                    ____exports.GameStates={}
                    function IsHeroAlive() return false end
                    assert(____exports.IsTeamPushingSecondTierOrHighGround(bot)==false)
                end
            end
        """)

    def test_roshan_desire_uses_fractional_health(self):
        from test_roshan_diagnostics import MODE_SETUP
        self.lua.execute(MODE_SETUP)
        self.lua.execute("""
            lowHP=true
            function bot:GetNearbyNeutralCreeps()
                return {{GetUnitName=function() return 'npc_dota_roshan' end,
                    GetHealth=function() return hp end,GetMaxHealth=function() return 100 end}}
            end
        """)
        self.lua.execute(source("bots/mode_roshan_generic.lua"))
        for hp in (49, 25, 1):
            self.lua.globals().hp = hp
            self.assertAlmostEqual(self.lua.eval("(GetDesireHelper())"), min(0.9, 1 - hp / 200))

    def test_ping_is_consumed_once_and_new_ping_can_reassemble(self):
        self.lua.execute("""
            human=unit(1); ping={time=10,normal_ping=true,location={}}
            function J.GetHumanPing() return human,ping end
            function J.ModeAnnounce() end
        """)
        self.lua.execute(source("bots/mode_assemble_generic.lua"))
        self.lua.execute("""
            assert(GetDesire()>0)
            now=14; assert(GetDesire()>0)
            now=15.1; assert(GetDesire()==0)
            ping.time=15.1; assert(GetDesire()>0)
            OnEnd(); assert(GetDesire()==0)
            human=unit(2); assert(GetDesire()>0)
            ping.location.distance=100; assert(GetDesire()==0)
            ping.location.distance=1000; assert(GetDesire()==0)
            ping.time=16; now=15.5; assert(GetDesire()==0)
        """)

    def test_help_branches_respect_lock_and_release_invalid_targets(self):
        self.lua.execute("""
            J.Role={IsPvNMode=function() return false end}
            J.IsCore=function() return true end
            J.GetHP=function() return 1 end
            J.SetFrameProcessTime=function() end
            J.UpdateEnemyHeroPositions=function() end
            J.GetMostPushLaneDesire=function() return 0 end
            J.GetMostDefendLaneDesire=function() return 0 end
            J.CheckBotIdleState=function() return false end
            J.GetAlliesNearLoc=function() return {} end
            J.GetEnemiesNearLoc=function() return {} end
            J.Utils.IsValidUnit=function(u) return u~=nil and u.alive end
            function dofile() return {} end
        """)
        # Load the entire mode so tests exercise the callers, not just the lock helper.
        mode = source("bots/mode_team_roam_generic.lua")
        before, after = mode.rsplit("return X", 1)
        self.lua.execute(before + "\nTestMode=X; function TestTarget() return targetUnit end\nreturn X" + after)
        self.lua.execute("""
            function ItemOpsDesire() end
            TestMode.CanBeAttacked=function(u) return u~=nil and u.alive end
            TestMode.ConsiderHelpWhenCoreIsTargeted=function() return candidate,coreHelp end
            function ConsiderHelpAlly() return candidate,true end
            for _,core in ipairs({true,false}) do
                coreHelp=core
                local a,b=unit(1),unit(2)
                now=now+10; candidate=a; GetDesireHelper(); assert(bot.target==a)
                now=now+0.5; candidate=a; GetDesireHelper()
                candidate=b; GetDesireHelper(); assert(bot.target==a and TestTarget()==a)
                now=now+0.8; GetDesireHelper(); assert(bot.target==b)
                b.alive=false; candidate=a; GetDesireHelper(); assert(bot.target==a)
                a.distance=1900; b.alive=true; candidate=b
                GetDesireHelper(); assert(bot.target==b)
            end
        """)

    def test_modified_lua_compiles_as_lua51(self):
        compile_lua = self.lua.eval("function(s) local f,e=loadstring(s); return f~=nil,e end")
        for path in ["bots/FunLib/jmz_func.lua", "bots/FunLib/utils.lua",
                     "bots/mode_roshan_generic.lua", "bots/mode_team_roam_generic.lua",
                     "bots/mode_assemble_generic.lua", "bots/mode_ward_generic.lua",
                     "bots/FunLib/aba_global_overrides.lua", "bots/BotLib/hero_lion.lua",
                     "bots/BotLib/hero_bristleback.lua", "bots/BotLib/hero_treant.lua",
                     "bots/BotLib/hero_bounty_hunter.lua", "bots/ability_item_usage_generic.lua",
                     "bots/mode_watcher_generic.lua", "bots/mode_farm_generic.lua",
                     "bots/FunLib/high_five_chat.lua"]:
            ok, error = compile_lua(source(path))
            self.assertTrue(ok, f"{path}: {error}")

    def test_postprocessor_rewrites_paths_and_reports_io_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / "typescript/post-process/post.js"
            script.parent.mkdir(parents=True)
            script.write_text(source("typescript/post-process/post-process-lua.js"), encoding="utf-8")
            output = root / "bots"
            output.mkdir()
            target = output / "example.lua"
            target.write_text('local x=require("bots.FunLib.utils")\n', encoding="utf-8")
            result = subprocess.run(["node", str(script), str(output)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('require(GetScriptDirectory().."/FunLib/utils")', target.read_text())
            output.rename(root / "moved-bots")
            result = subprocess.run(["node", str(script)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
