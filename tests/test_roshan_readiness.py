"""Participant-aware Roshan policy, using production Lua with engine mocks."""
import unittest
from test_bot_regressions import COMMON, LuaRuntime, function
from test_roshan_diagnostics import MODE_SETUP, read


class RoshanReadiness(unittest.TestCase):
    def mode(self, scenario=''):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(COMMON + MODE_SETUP + scenario)
        lua.execute(read('bots/mode_roshan_generic.lua'))
        return lua

    def test_damaged_ancient_recovers_after_threat_hold(self):
        lua = self.mode('function J.GetHP() return 0.2 end')
        lua.execute('''
            assert(GetDesireHelper()>0)
            baseDanger=true; assert(GetDesireHelper()==0)
            baseDanger=false; now=13; assert(GetDesireHelper()==0)
            now=14; assert(GetDesireHelper()>0)
            function J.Utils.CountEnemyHeroesOnHighGround() return 2 end
            assert(GetDesireHelper()==0)
        ''')

    def test_finishing_cannot_bypass_safety_or_readiness(self):
        for scenario, reason in [
            ('baseDanger=true', 'ancient_danger_or_damage'),
            ('outnumbered=true', 'outnumbered_alive'),
            ('dps=false', 'dps_not_ready'),
            ('function J.GetRoshanParticipants() return {} end', 'participant_unavailable'),
            ('visible=true; changing=true; finishing=true', 'visible_enemies_near_bot'),
            ('function J.GetEnemiesNearLoc(loc,r) return r==2500 and {1} or {} end', 'enemies_near_pit'),
            ('function J.GetLastSeenEnemiesNearLoc(loc,r) return r==2500 and {1} or {} end', 'enemies_near_pit'),
        ]:
            with self.subTest(reason=reason):
                lua = self.mode('lowHP=true; ' + scenario)
                self.assertEqual(lua.eval('GetDesireHelper()'), (0, reason))

    def estimator(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(COMMON + '''
            DAMAGE_TYPE_PHYSICAL=1
            function J.IsValidHero(h) return h~=nil and not h:IsNull() and h:IsHero() end
            function J.IsMeepoClone(h) return h.clone end
            function J.GetHP(h) return h.hp or 1 end
            function J.IsRetreating(h) return h.retreat end
            function J.IsRoshan(r) return r~=nil and r.visible end
            function J.GetCurrentRoshanLocation() return {} end
            function GetUnitToLocationDistance(h,p) return h.distance end
            function fighter(id,damage)
                local h=unit(id); h.damage=damage; h.distance=0
                function h:IsDisarmed() return self.disarmed end
                function h:IsStunned() return self.stunned end
                function h:GetAttackDamage() return self.damage end
                function h:GetSecondsPerAttack() return self.interval or 1 end
                function h:GetCurrentMovementSpeed() return self.speed or 300 end
                return h
            end
        ''')
        for name in ('J.GetRoshanParticipants', 'J.HasEnoughDPSForRoshan'):
            lua.execute(function('bots/FunLib/jmz_func.lua', name))
        return lua

    def test_filters_unavailable_allies_and_duplicate_players(self):
        lua = self.estimator()
        lua.execute('''
            a=fighter(0,500); b=fighter(1,10)
            assert(#J.GetRoshanParticipants({a,b,a},{})==2)
            for _,field in ipairs({'clone','double','retreat','disarmed','stunned'}) do
                b[field]=true
                assert(#J.GetRoshanParticipants({a,b},{})==1)
                b[field]=false
            end
            b.distance=2501; assert(#J.GetRoshanParticipants({a,b},{})==1)
            b.distance=0; b.hp=0.49; assert(#J.GetRoshanParticipants({a,b},{})==1)
            b.hp=1; b.alive=false; assert(#J.GetRoshanParticipants({a,b},{})==1)
            b.alive=true; b.IsIllusion=function() return true end
            assert(#J.GetRoshanParticipants({a,b},{})==1)
        ''')

    def test_sum_attack_interval_arrival_and_empty_team(self):
        lua = self.estimator()
        lua.execute('''
            a=fighter(0,250); b=fighter(1,250); support=fighter(2,1)
            assert(not J.HasEnoughDPSForRoshan({}))
            assert(not J.HasEnoughDPSForRoshan({a}))
            assert(J.HasEnoughDPSForRoshan({a,b}))
            assert(J.HasEnoughDPSForRoshan({a,b,support}))
            a.interval=2; b.interval=2
            assert(not J.HasEnoughDPSForRoshan({a,b}))
            a.interval=1; b.interval=1; a.distance=2500; b.distance=2500
            a.speed=100; b.speed=100
            assert(not J.HasEnoughDPSForRoshan({a,b}))
        ''')

    def test_live_mitigation_and_fog_safe_fallback(self):
        lua = self.estimator()
        lua.execute('''
            a=fighter(0,250); r={visible=true}
            function r:GetHealth() assert(self.visible); return 600 end
            function r:GetHealthRegen() assert(self.visible); return 20 end
            function r:GetActualIncomingDamage(d,t) assert(self.visible and t==1); return d*0.5 end
            assert(J.HasEnoughDPSForRoshan({a},r))
            r.visible=false
            assert(not J.HasEnoughDPSForRoshan({a},r))
            a.interval=0; assert(not J.HasEnoughDPSForRoshan({a},r))
        ''')


if __name__ == '__main__':
    unittest.main()
