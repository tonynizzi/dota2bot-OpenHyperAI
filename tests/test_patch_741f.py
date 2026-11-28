"""Focused 7.41f maintenance checks, running production Lua in Lua 5.1."""
import unittest
from test_bot_regressions import COMMON, ROOT, LuaRuntime, function
from test_roshan_diagnostics import MODE_SETUP


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class PatchMaintenance(unittest.TestCase):
    def treant(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(COMMON + '''
            X={}; mode='attack'; behavior=135176; castable=true; disarmed=false
            BOT_ACTION_DESIRE_NONE=0; BOT_ACTION_DESIRE_HIGH=0.8
            BOT_ACTION_DESIRE_MODERATE=0.5; DAMAGE_TYPE_ALL=7
            ABILITY_BEHAVIOR_UNIT_TARGET=8
            enemy=unit(1); second=unit(2); objective=unit(3); target=enemy
            function bot:IsDisarmed() return disarmed end
            function bot:GetAttackRange() return 150 end
            function bot:WasRecentlyDamagedByAnyHero() return true end
            function bot:FindAoELocation() return {count=2,targetloc={x=10}} end
            function enemy:GetEstimatedDamageToTarget() return 100 end
            second.GetEstimatedDamageToTarget=enemy.GetEstimatedDamageToTarget
            LeechSeed={}
            function LeechSeed:IsFullyCastable() return castable end
            function LeechSeed:GetBehavior() return behavior end
            function J.Utils.AbilityBehaviorHasFlag(b,f) return math.floor(b/f)%2==1 end
            function J.GetProperTarget() return target end
            function J.IsGoingOnSomeone() return mode=='attack' end
            function J.IsRetreating() return mode=='retreat' end
            function J.IsDoingRoshan() return mode=='roshan' end
            function J.IsDoingTormentor() return mode=='tormentor' end
            function J.IsRoshan(t) return t==objective end
            function J.IsTormentor(t) return t==objective end
            function J.IsAttacking() return true end
            function J.GetNearbyHeroes(b,r,enemies)
                return enemies and {enemy,second} or {bot}
            end
            function J.IsValidHero(t) return t~=nil and t.alive end
            function J.CanCastOnNonMagicImmune() return true end
            function J.IsInRange(b,t,r) return t.distance<=r end
            function J.IsSuspiciousIllusion() return false end
            function J.IsDisabled() return false end
            function J.IsChasingTarget() return true end
            function J.CanNotUseAbility() return false end
            function X.ConsiderBlinkOvergrowth() return 0 end
            function X.ConsiderOvergrowth() return 0 end
            function X.ConsiderNaturesGrasp() return 0 end
            function X.ConsiderEyesInTheForest() return 0 end
            function X.ConsiderLivingArmor() return 0 end
            actions=0
            function bot:Action_UseAbilityOnEntity(a,t)
                assert(a==LeechSeed and (t==enemy or t==objective))
                actions=actions+1; castTarget=t
            end
            function bot:Action_UseAbilityOnLocation() error('ground cast') end
        ''')
        path = 'bots/BotLib/hero_treant.lua'
        lua.execute(function(path, 'X.ConsiderLeechSeed'))
        lua.execute(function(path, 'X.SkillsComplement'))
        return lua

    def test_treant_combat_and_retreat_use_unit_orders(self):
        lua = self.treant()
        lua.execute('''
            -- Two nearby enemies must never produce a ground-targeted cast.
            X.SkillsComplement(); assert(actions==1 and castTarget==enemy)
            mode='retreat'; X.SkillsComplement(); assert(actions==2)
            enemy.distance=151; second.distance=151
            X.SkillsComplement(); assert(actions==2)
        ''')

    def test_treant_objectives_use_unit_and_attack_range(self):
        lua = self.treant()
        lua.execute('''
            target=objective
            for _,m in ipairs({'roshan','tormentor'}) do
                mode=m; actions=0; objective.distance=100
                X.SkillsComplement(); assert(actions==1 and castTarget==objective)
                objective.distance=300; X.SkillsComplement(); assert(actions==1)
            end
        ''')

    def test_treant_declines_disarm_unaffordable_or_wrong_behavior(self):
        lua = self.treant()
        lua.execute('''
            disarmed=true; X.SkillsComplement(); assert(actions==0)
            disarmed=false; castable=false; X.SkillsComplement(); assert(actions==0)
            castable=true; behavior=16; X.SkillsComplement(); assert(actions==0)
            behavior=135176; X.SkillsComplement(); assert(actions==1)
        ''')

    def test_bounty_shuriken_uses_live_damage_once(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(COMMON + '''
            X={}; aetherRange=0; talent3Damage=999; liveDamage=310
            BOT_ACTION_DESIRE_HIGH=0.8; DAMAGE_TYPE_MAGICAL=2
            enemy=unit(1); hEnemyList={enemy}; J.Chat={}
            function enemy:IsChanneling() return false end
            abilityQ={}
            function abilityQ:IsFullyCastable() return true end
            function abilityQ:GetLevel() return 4 end
            function abilityQ:GetCastRange() return 600 end
            function abilityQ:GetCastPoint() return 0.3 end
            function abilityQ:GetManaCost() return 105 end
            function abilityQ:GetSpecialValueInt(k)
                if k=='bonus_damage' then return liveDamage end
                return 1200
            end
            function J.GetAroundEnemyHeroList() return {enemy} end
            function J.GetAroundBotUnitList() return {} end
            function J.CanCastOnNonMagicImmune() return true end
            function J.WillMagicKillTarget(b,t,d) measured=d; return true end
            function J.IsInRange() return true end
            function J.CanCastOnTargetAdvanced() return true end
            function J.Chat.GetNormName() return 'enemy' end
        ''')
        lua.execute(function('bots/BotLib/hero_bounty_hunter.lua', 'X.ConsiderQ'))
        lua.execute('''
            for _,damage in ipairs({310,500,520}) do
                liveDamage=damage
                local desire,target=X.ConsiderQ()
                assert(desire>0 and target==enemy and measured==damage)
            end
        ''')

    def roshan(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(COMMON + MODE_SETUP)
        lua.execute(function('bots/FunLib/jmz_func.lua', 'J.GetCurrentRoshanLocation'))
        lua.execute(read('bots/mode_roshan_generic.lua'))
        return lua

    def test_roshan_fight_gate_uses_current_pit_on_both_sides(self):
        lua = self.roshan()
        lua.execute('''
            fight=true
            for _,isNight in ipairs({false,true}) do
                night=isNight
                local current=J.GetCurrentRoshanLocation()
                local other=current==J.Utils.DireRoshanLoc
                    and J.Utils.RadiantRoshanLoc or J.Utils.DireRoshanLoc
                current.distance=100; other.distance=5000
                local desire,reason=GetDesireHelper()
                assert(desire==0 and reason==(night and 'nearby_teamfight_night' or 'nearby_teamfight_day'))
                current.distance=5000; other.distance=100
                desire,reason=GetDesireHelper()
                assert(desire>0 and reason=='engine_desire_scaled')
            end
        ''')

    def test_roshan_reacquires_after_cached_unit_becomes_invalid(self):
        lua = self.roshan()
        lua.execute('''
            first={valid=true}; replacement={valid=true}; visibleRoshan=first; scans=0
            for _,r in ipairs({first,replacement}) do
                function r:GetUnitName() return 'npc_dota_roshan' end
                function r:GetHealth() assert(self.valid); return 25 end
                function r:GetMaxHealth() return 100 end
            end
            function J.Utils.IsValidUnit(u) return u~=nil and u.valid end
            function bot:GetNearbyNeutralCreeps() scans=scans+1; return {visibleRoshan} end
            local _,reason=GetDesireHelper(); assert(reason=='finish_low_health_roshan')
            GetDesireHelper(); assert(scans==1)
            first.valid=false; visibleRoshan=replacement
            _,reason=GetDesireHelper(); assert(reason=='finish_low_health_roshan' and scans==2)
            replacement.valid=false; visibleRoshan=nil
            _,reason=GetDesireHelper(); assert(reason=='engine_desire_scaled' and scans==3)
        ''')


if __name__ == '__main__':
    unittest.main()
