"""Read-only Roshan trace and decision-flow tests (Lua 5.1 engine mocks)."""
import subprocess
import unittest
from test_bot_regressions import ROOT, COMMON, LuaRuntime
from tools.analyze_roshan import parse_line, classify


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


MODE_SETUP = """
BOT_ACTION_DESIRE_NONE=0; BOT_ACTION_DESIRE_VERYHIGH=0.9
UNIT_LIST_ALLIED_HEROES=1
J.Customize={Enable=true,RoshanDiagnostics=false}
traceCalls=0; snapshotCalls=0
trace={Record=function() traceCalls=traceCalls+1 end}
function require(name)
    if string.find(name,'roshan_diagnostics') then return trace end
    return J
end
function bot:GetNearbyNeutralCreeps()
    if lowHP then return {{GetUnitName=function() return 'npc_dota_roshan' end,
        GetHealth=function() return 25 end, GetMaxHealth=function() return 100 end}} end
    return {}
end
function J.ModeAnnounce() end
function J.Utils.IsTeamPushingSecondTierOrHighGround() return pushing end
function J.Utils.CountEnemyHeroesOnHighGround() return 0 end
function J.GetRoshanParticipants(heroes) return heroes end
function J.GetEnemiesAroundAncient() return baseDanger and 1 or 0 end
function J.GetHP(u) return u==bot and 0.75 or 1 end
function GetAncient() return {} end
function J.CheckTimeOfDay() return night and 'night' or 'day' end
J.Utils.RadiantRoshanLoc={}; J.Utils.DireRoshanLoc={}
function J.GetTeamFightLocation() return fight and {} or nil end
function J.GetLastSeenEnemiesNearLoc(loc,r) return (r==1200 and recent) and {1,2} or {} end
function J.Utils.IsValidUnit(u) return u~=nil end
function J.GetNumOfAliveHeroes(enemy) return enemy and 5 or (outnumbered and 4 or 5) end
function GetUnitList() return full and {bot,bot} or {bot} end
function J.Utils.CountBackpackEmptySpace() return full and 0 or 1 end
function J.IsCore() return true end
function J.IsRoshanAlive() return alive end
function J.HasEnoughDPSForRoshan() return dps end
function J.IsRoshanCloseToChangingSides() return changing end
function J.GetProperTarget() return finishing and bot or nil end
function J.IsRoshan(t) return t~=nil end
function J.IsValid(t) return t~=nil end
function J.GetEnemiesNearLoc(loc,r) return (r==1300 and visible) and {1} or {} end
function J.GetHumanPing()
    if pinged then return bot,{normal_ping=true,location={},time=now} end
    return nil,nil
end
function J.GetCurrentRoshanLocation() return {} end
function J.GetDistance() return 0 end
function GetRoshanDesire() return 0.4 end
function Clamp(x,a,b) return math.max(a,math.min(x,b)) end
alive=true; dps=true
"""


class RoshanDiagnostics(unittest.TestCase):
    def runtime(self, mode, scenario):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(COMMON + MODE_SETUP + scenario)
        lua.execute(mode)
        return lua

    def test_reasons_cover_all_gates(self):
        current = read("bots/mode_roshan_generic.lua")
        scenarios = {
            "ineligible_bot": "",  # eligibility changes after module initialization
            "team_pushing": "pushing=true",
            "ancient_danger_or_damage": "baseDanger=true",
            "nearby_teamfight_day": "fight=true",
            "nearby_teamfight_night": "fight=true; night=true",
            "recent_enemies_near_bot": "recent=true",
            "finish_low_health_roshan": "lowHP=true",
            "outnumbered_alive": "outnumbered=true",
            "core_backpacks_full": "full=true",
            "finish_before_side_change": "changing=true; finishing=true",
            "side_change_soon": "changing=true",
            "visible_enemies_near_bot": "visible=true",
            "human_ping": "pinged=true",
            "engine_desire_scaled": "",
            "respawn_estimate_not_ready": "alive=false",
            "dps_not_ready": "dps=false",
        }
        for reason, scenario in scenarios.items():
            with self.subTest(reason=reason):
                new = self.runtime(current, scenario)
                if reason == "ineligible_bot":
                    new.execute("bot.alive=false")
                desire, actual_reason = new.eval("GetDesireHelper()")
                self.assertEqual(actual_reason, reason)
                self.assertGreaterEqual(desire, 0)
                self.assertLessEqual(desire, 0.9)
                self.assertEqual(new.eval("GetDesire()"), desire)
                self.assertEqual(new.globals().traceCalls, 0)

    def test_opt_in_and_readiness_refreshes_after_dps_loss_and_recovery(self):
        lua = self.runtime(read("bots/mode_roshan_generic.lua"), "")
        lua.execute("""
            J.Customize.RoshanDiagnostics=true
            trace.Record=function(b,d,r,j,c) traceCalls=traceCalls+1; last=c; reason=r end
            GetDesire(); assert(last.dpsCurrent==true and last.dpsLatched==true)
            dps=false; GetDesire()
            assert(last.dpsCurrent==false and last.dpsLatched==false)
            assert(reason=='dps_not_ready')
            dps=true; GetDesire()
            assert(last.dpsCurrent==true and last.dpsLatched==true)
            assert(reason=='engine_desire_scaled')
            pushing=true; GetDesire(); assert(last.dpsCurrent==nil)
            J.Customize.Enable=false; GetDesire(); assert(traceCalls==4)
        """)

    def test_trace_sampling_heartbeat_per_bot_and_no_action_calls(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(COMMON + """
            lines={}; scans=0
            function print(line) lines[#lines+1]=line end
            function bot:GetActiveMode() return 7 end
            function bot:GetHealth() return 60 end
            function bot:GetMaxHealth() return 100 end
            function bot:GetMana() return 0 end
            function bot:GetMaxMana() return 0 end
            function GetTeamPlayers() scans=scans+1; return {0} end
            function GetTeamMember(slot) assert(slot==1); return bot end
            function J.GetCurrentRoshanLocation() return {x=1,y=2} end
            function J.GetLastSeenEnemiesNearLoc() return {} end
            function J.GetEnemiesNearLoc() return {} end
        """)
        lua.globals().trace = lua.execute(read("bots/FunLib/roshan_diagnostics.lua"))
        lua.execute("""
            context={aliveEstimate=true,dpsCurrent=false,dpsLatched=true}
            trace.Record(bot,0.4,'engine_desire_scaled',J,context)
            assert(#lines==1 and scans==1)
            assert(string.find(lines[1],'dps_current=false dps_latched=true',1,true))
            assert(string.find(lines[1],'allies=[0@1000:60:0:7]',1,true))
            now=11; trace.Record(bot,0,'team_pushing',J,context); assert(#lines==1 and scans==1)
            now=12; trace.Record(bot,0,'team_pushing',J,context); assert(#lines==2)
            now=14; trace.Record(bot,0,'team_pushing',J,context); assert(#lines==2 and scans==2)
            now=28; trace.Record(bot,0,'team_pushing',J,context); assert(#lines==3)
            bot.id=1; trace.Record(bot,0,'team_pushing',J,context); assert(#lines==4)
            now=0; trace.Record(bot,0,'team_pushing',J,context); assert(#lines==5)
        """)
        # Verify the offline parser against output from the real Lua emitter.
        record = parse_line(lua.globals().lines[1], 1)
        self.assertEqual(record["reason"], "engine_desire_scaled")
        self.assertIn("stale_dps_offer", classify(record))


if __name__ == '__main__':
    unittest.main()
