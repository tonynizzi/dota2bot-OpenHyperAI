"""Exercise shipped base-defense Lua with engine mocks; no live game required."""
import unittest
import re
from test_bot_regressions import LuaRuntime, function, source

PATH = 'bots/FunLib/aba_defend.lua'


class BaseDefenseTests(unittest.TestCase):
    def decision_runtime(self):
        lua = LuaRuntime()
        lua.execute('''
            ____exports={}; nTeam=2; now=100
            BASE_THREAT_RADIUS=2600; BASE_THREAT_HOLD=4
            BotModeDesire={None=0,VeryLow=0.1,Moderate=0.5}
            BotMode={None=0,PushTowerTop=1,PushTowerMid=2,PushTowerBot=3}
            heroes=1; hg=0; weight=0; nearby={}; hit=false
            ancient={GetLocation=function() return {} end}
            function DotaTime() return now end
            function updateDefendGameStateCache() return {team=2,ourAncient=ancient} end
            function updateDefendLocationStateCache() return {laneFronts={[1]={},[2]={},[3]={}}} end
            ds={distanceToLane={}}
            function getDefendState() return ds end
            function GetUnitToLocationDistance() return 100 end
            bot={GetLevel=function() return 20 end,GetAssignedLane=function() return 1 end,
                GetLocation=function() return {} end,
                WasRecentlyDamagedByAnyHero=function() return hit end,
                WasRecentlyDamagedByTower=function() return hit end}
            member={IsAlive=function() return true end,GetActiveMode=function() return 1 end,
                GetLocation=function() return {} end}
            function GetTeamPlayers() return {0,1,2,3,4} end
            function GetTeamMember() return member end
            function GetThreatenedLane() return 1 end
            function WeightedEnemiesAroundLocation() return weight end
            jmz={GetEnemiesNearLoc=function() return nearby end,
                GetAlliesNearLoc=function() return {bot,member,{}} end,
                GetNearbyHeroes=function() return {bot} end,
                GetLastSeenEnemiesNearLoc=function() return nearby end,
                WeAreStronger=function() return false end,
                AdjustLocationWithOffsetTowardsFountain=function(loc) return loc end,
                IsDoingRoshan=function() return true end,
                IsDoingTormentor=function() return true end,
                Utils={CountEnemyHeroesNear=function() return heroes end,
                    CountEnemyHeroesOnHighGround=function() return hg end}}
        ''')
        # Use the production initializer so a negative sentinel cannot escape coverage.
        lua.execute(re.search(r'^baseThreatUntil = .+$', source(PATH), re.M).group())
        lua.execute(function(PATH, 'IsBaseThreatActive'))
        lua.execute(function(PATH, '____exports.GetDefendDesireHelper'))
        return lua

    def test_countdown_without_threat_leaves_opening_modes_available(self):
        for now in (-90, -60, -10, -1, 0, 1):
            with self.subTest(now=now):
                lua = self.decision_runtime()
                lua.execute(f'now={now}; heroes=0; bot.GetLevel=function() return 1 end')
                self.assertFalse(lua.eval('IsBaseThreatActive()'))
                for lane in (1, 2, 3):
                    self.assertEqual(lua.eval(f'____exports.GetDefendDesireHelper(bot,{lane})'), 0)
                self.assertIsNone(lua.eval('jmz.Utils.GameStates'))

    def test_real_countdown_threat_expires_across_zero(self):
        lua = self.decision_runtime()
        lua.execute('now=-4')
        self.assertEqual(lua.eval('____exports.GetDefendDesireHelper(bot,1)'), .96)
        lua.execute('heroes=0; now=-1')
        self.assertTrue(lua.eval('IsBaseThreatActive()'))
        lua.execute('now=0')
        self.assertFalse(lua.eval('IsBaseThreatActive()'))

    def test_emergency_beats_push_combat_damage_and_objectives(self):
        for setup in ('', 'nearby={{}}', 'hit=true', 'heroes=0; hg=2', 'heroes=0; weight=2'):
            with self.subTest(setup=setup):
                lua = self.decision_runtime()
                lua.execute(setup)
                self.assertEqual(lua.eval('____exports.GetDefendDesireHelper(bot,1)'), .96)
                self.assertEqual(lua.eval('bot.laneToDefend'), 1)
                self.assertEqual(lua.eval('jmz.Utils.GameStates.recentDefendTime'), 100)

    def test_only_selected_lane_is_urgent_and_threat_expires(self):
        lua = self.decision_runtime()
        self.assertEqual(lua.eval('____exports.GetDefendDesireHelper(bot,2)'), .1)
        lua.execute('heroes=0; now=102')
        self.assertEqual(lua.eval('____exports.GetDefendDesireHelper(bot,1)'), .96)
        lua.execute('now=105')
        self.assertEqual(lua.eval('____exports.GetDefendDesireHelper(bot,1)'), .1)

    def test_ordinary_push_and_local_combat_still_suppress_lane_defense(self):
        lua = self.decision_runtime()
        lua.execute('heroes=0')
        self.assertEqual(lua.eval('____exports.GetDefendDesireHelper(bot,1)'), .1)
        lua.execute('nearby={{}}')
        self.assertEqual(lua.eval('____exports.GetDefendDesireHelper(bot,1)'), .3)

    def test_closest_role_includes_first_candidate(self):
        lua = LuaRuntime()
        lua.execute('''
            members={{pos=4,distance=100},{pos=5,distance=5000}}
            function GetTeamMember(i) return members[i] end
            function GetUnitToLocationDistance(m) return m.distance end
            jmz={IsValidHero=function(m) return m~=nil end,GetPosition=function(m) return m.pos end}
        ''')
        lua.execute(function(PATH, 'GetClosestAllyPos'))
        self.assertEqual(lua.eval('GetClosestAllyPos({4,5},{})'), 4)
        lua.execute('members[1].distance=6000')
        self.assertEqual(lua.eval('GetClosestAllyPos({4,5},{})'), 5)

    def test_weighted_creeps_summons_and_heroes(self):
        lua = LuaRuntime()
        lua.execute('''
            units={}; _cacheEnemyAroundLoc={}; CACHE_ENEMY_AROUND_LOC_HZ=0.35
            function DotaTime() return 100 end
            function _keyLoc() return 'key' end
            function updateDefendUnitStateCache() return {enemyUnits=units} end
            function GetUnitToLocationDistance(u) return u.distance or 100 end
            function __TS__StringIncludes(s,part) return string.find(s,part,1,true)~=nil end
            jmz={IsValid=function() return true end,IsValidHero=function(u) return u.hero end,
                IsSuspiciousIllusion=function(u) return u.illusion end,IsCore=function() return true end}
            function creep(name)
                return {GetUnitName=function() return name end,IsCreep=function() return true end}
            end
        ''')
        lua.execute(function(PATH, 'WeightedEnemiesAroundLocation'))
        for name, count, expected in (
            ('npc_dota_creep_lane', 10, 2),
            ('npc_dota_creep_upgraded_mega', 4, 2),
            ('npc_dota_creep_siege', 4, 2),
            ('npc_dota_warlock_golem', 2, 2),
            ('npc_dota_creep_lane', 1, 0),
        ):
            with self.subTest(name=name):
                lua.execute(f"units={{}}; _cacheEnemyAroundLoc={{}}; for i=1,{count} do units[i]=creep('{name}') end")
                self.assertEqual(lua.eval('WeightedEnemiesAroundLocation({},2600)'), expected)
        lua.execute("units={creep('npc_dota_hero_axe')}; units[1].hero=true; units[1].illusion=true; _cacheEnemyAroundLoc={}")
        self.assertEqual(lua.eval('WeightedEnemiesAroundLocation({},2600)'), 0)


if __name__ == '__main__':
    unittest.main()
