"""Regression scenarios for defects found while reviewing saved playtest logs."""
import unittest
from test_bot_regressions import LuaRuntime, ROOT, function


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class PlaytestRepairs(unittest.TestCase):
    def test_opt_in_trace_survives_global_print_filter(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute('Utils={DebugMode=false}; output={}; '
                    'function orig_print(s) table.insert(output,s) end')
        lua.execute(function('bots/FunLib/aba_global_overrides.lua', 'print'))
        lua.execute("print('ordinary'); print('[OHA_ROSHAN] t=10'); "
                    "assert(#output==1 and output[1]=='[OHA_ROSHAN] t=10'); "
                    "Utils.DebugMode=true; print('ordinary'); assert(#output==2)")

    def ward_runtime(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
        bot={}; inventory={}; actions={}; position=4; suitable=true
        function GetBot() return bot end
        function bot:IsInvulnerable() return false end
        function bot:IsHero() return true end
        function bot:IsIllusion() return false end
        function bot:GetUnitName() return 'npc_dota_hero_test' end
        function bot:GetItemInSlot(slot) return inventory[slot] end
        function bot:Action_UseAbilityOnLocation(item,loc) table.insert(actions,item:GetName()) end
        function bot:Action_UseAbilityOnEntity(item,target) table.insert(actions,'toggle') end
        function bot:Action_MoveToLocation(loc) table.insert(actions,'move') end
        function GetScriptDirectory() return 'bots' end
        function DotaTime() return 100 end
        function GetTeam() return 2 end
        function GetAncient() return {GetLocation=function() return {} end} end
        function GetUnitToLocationDistance() return 100 end
        function RandomVector() return 0 end
        BOT_MODE_DESIRE_NONE=0; BOT_MODE_DESIRE_VERYHIGH=0.8; BOT_MODE_DESIRE_ABSOLUTE=1
        function RemapValClamped(x,a,b,c,d) return d end
        J={Utils={}}; W={}
        function J.GetPosition() return position end
        function J.GetHP() return 1 end
        function J.CanCastAbility(item) return item~=nil end
        function J.CanNotUseAction() return false end
        function J.Utils.IsBotThinkingMeaningfulAction() return false end
        function J.Utils.IsTeamPushingSecondTierOrHighGround() return false end
        function J.Utils.CountEnemyHeroesNear() return 0 end
        function W.GetAvailabeObserverWardSpots() return {} end
        function W.GetClosestObserverWardSpot() return observerSpot end
        function W.GetPossibleSentryWardSpots() return {} end
        function W.GetClosestSentryWardSpot() return sentrySpot end
        function W.IsOtherWardClose() return false end
        function require(path)
            if string.find(path,'jmz_func') then return J end
            if string.find(path,'aba_ward_utility') then return W end
            return {Enable=true,ThinkLess=1}
        end
        observer={GetName=function() return 'item_ward_observer' end}
        sentry={GetName=function() return 'item_ward_sentry' end}
        observerSpot={location=1}; sentrySpot={location=2}
        ''')
        # Export the module's private test predicates in the same Lua chunk.
        lua.execute(read('bots/mode_ward_generic.lua') + '''
        X.IsSuitableToWard=function() return suitable end
        X.IsEnemyCloserToWardLocation=function() return false end
        ''')
        return lua

    def test_ward_moved_after_selection_is_not_used_or_pursued(self):
        for slot in (6, 9):
            lua = self.ward_runtime()
            lua.execute(f'''inventory[0]=observer; assert(GetDesireHelper()>0)
                inventory[0]=nil; inventory[{slot}]=observer
                Think(); assert(#actions==0)
                assert(GetDesireHelper()==0)
            ''')

    def test_sentry_destination_does_not_use_observer(self):
        lua = self.ward_runtime()
        lua.execute('''inventory[0]=observer; inventory[1]=sentry
            observerSpot=nil; assert(GetDesireHelper()>0)
            Think(); assert(actions[1]=='item_ward_sentry')
        ''')

    def test_unavailable_ward_plan_is_cleared_and_core_desire_is_numeric(self):
        lua = self.ward_runtime()
        lua.execute('''inventory[0]=observer; assert(GetDesireHelper()>0)
            suitable=false; assert(GetDesireHelper()==0); Think(); assert(#actions==0)
            position=1; assert(GetDesire()==0)
        ''')

    def test_hex_decision_and_dispatch_follow_live_behavior(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
            X={}; bot={}; J={Utils={},Chat={}}; behavior=8
            ABILITY_BEHAVIOR_POINT=16; BOT_ACTION_DESIRE_HIGH=0.8
            function J.Utils.AbilityBehaviorHasFlag(b,f) return math.floor(b/f)%2==1 end
            abilityW=setmetatable({}, {__index=function(t,k) return function() return 0 end end})
            function abilityW:GetBehavior() return behavior end
            function abilityW:IsFullyCastable() return true end
            location={x=1}; enemy={}
            function enemy:IsChanneling() return true end
            function enemy:GetLocation() return location end
            function J.GetNearbyHeroes() return {enemy} end
            function J.IsValidHero() return true end
            function J.CanCastOnTargetAdvanced() return true end
            function J.CanCastOnNonMagicImmune() return true end
            function J.Chat.GetNormName() return 'enemy' end
            function DotaTime() return 10 end
            lastCastQTime=0; aetherRange=0
            function J.SetReportMotive() end
            function J.SetQueuePtToINT() end
            function bot:ActionQueue_UseAbilityOnLocation(a,t) assert(t==location); action='point' end
            function bot:ActionQueue_UseAbilityOnEntity(a,t) assert(t==enemy); action='unit' end
        ''')
        path = 'bots/BotLib/hero_lion.lua'
        lua.execute(function(path, 'X.IsHexPointTarget'))
        lua.execute(function(path, 'X.ConsiderW'))
        src = read(path)
        dispatch = src[src.index('\tcastWDesire, castWTarget, sMotive = X.ConsiderW()'):]
        dispatch = dispatch[:dispatch.index('\n\tend') + len('\n\tend')]
        for behavior, expected in ((8, 'unit'), (16 + 32, 'point')):
            lua.execute(f'behavior={behavior}')
            lua.execute(dispatch)
            self.assertEqual(lua.globals().action, expected)

    def test_goo_dispatch_accepts_no_target_upgrade_and_normal_unit_target(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
            bot={}; X={}; J={Utils={}}; ABILITY_BEHAVIOR_NO_TARGET=4
            function J.Utils.AbilityBehaviorHasFlag(b,f) return math.floor(b/f)%2==1 end
            function J.SetQueuePtToINT() end
            target={}; ViscousNasalGoo={GetBehavior=function() return behavior end}
            function X.ConsiderViscousNasalGoo() return 1,target end
            function bot:ActionQueue_UseAbility(a) assert(a==ViscousNasalGoo); action='none' end
            function bot:ActionQueue_UseAbilityOnEntity(a,t) assert(t==target); action='unit' end
        ''')
        src = read('bots/BotLib/hero_bristleback.lua')
        dispatch = src[src.index('\tViscousNasalGooDesire, ViscousNasalGooTarget ='):]
        dispatch = dispatch[:dispatch.index('\n\tWarpathDesire =')]
        for behavior, expected in ((8, 'unit'), (4 + 32, 'none')):
            lua.execute(f'behavior={behavior}')
            lua.execute(dispatch)
            self.assertEqual(lua.globals().action, expected)


if __name__ == '__main__':
    unittest.main()
