"""Cast tracing must remain bounded and cannot change engine order dispatch."""
import unittest
from test_bot_regressions import ROOT, LuaRuntime


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


class ActionDiagnostics(unittest.TestCase):
    def runtime(self, integrated=False):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
            now=10; lines={}; orders={}; inventory={}; reads=0
            config={Enable=true,ActionDiagnostics=true,DiagnosticsGamePatch='7.41f'}
            function GameTime() return now end
            function GetScriptDirectory() return 'bots' end
            function print(line) lines[#lines+1]=line end
            CDOTA_Bot_Script={}
            function CDOTA_Bot_Script:GetPlayerID() return self.id or 0 end
            function CDOTA_Bot_Script:GetUnitName() return 'npc_dota_hero_test' end
            function CDOTA_Bot_Script:GetItemInSlot(slot) return inventory[slot] end
            for _,prefix in ipairs({'Action_','ActionQueue_','ActionPush_'}) do
                for _,suffix in ipairs({'UseAbility','UseAbilityOnEntity','UseAbilityOnLocation','UseAbilityOnTree'}) do
                    local method=prefix..suffix
                    CDOTA_Bot_Script[method]=function(self, ...)
                        orders[#orders+1]={method=method,args={...},n=select('#',...)}
                        return 'sent',42
                    end
                end
            end
            caster=setmetatable({}, {__index=CDOTA_Bot_Script})
            behavior=8; item=false; hidden=false
            ability={}
            function ability:GetName() reads=reads+1; return 'test_spell' end
            function ability:GetBehavior() return behavior end
            function ability:IsHidden() return hidden end
            function ability:IsItem() return item end
            target={}
            function target:CanBeSeen() return true end
            function target:GetUnitName() return 'enemy' end
        ''')
        lua.globals().trace = lua.execute(read('bots/FunLib/action_diagnostics.lua'))
        if integrated:
            lua.execute('''
                Utils={DebugMode=false}
                function require(path)
                    if string.find(path,'action_diagnostics') then return trace end
                    if string.find(path,'custom_loader') then return config end
                    return Utils
                end
            ''')
            lua.execute(read('bots/FunLib/aba_global_overrides.lua'))
        else:
            lua.execute('trace.Install(CDOTA_Bot_Script,config)')
        return lua

    def test_all_order_forms_preserve_arguments_returns_and_install_once(self):
        lua = self.runtime()
        lua.execute('''
            trace.Install(CDOTA_Bot_Script,config)
            for _,prefix in ipairs({'Action_','ActionQueue_','ActionPush_'}) do
                for _,suffix in ipairs({'UseAbility','UseAbilityOnEntity','UseAbilityOnLocation','UseAbilityOnTree'}) do
                    local method=prefix..suffix
                    local a,b=caster[method](caster,ability,target,nil,123)
                    local order=orders[#orders]
                    assert(a=='sent' and b==42 and order.method==method)
                    assert(order.n==4 and order.args[1]==ability and order.args[2]==target)
                    assert(order.args[3]==nil and order.args[4]==123)
                end
            end
            assert(#orders==12)
        ''')

    def test_disabled_diagnostics_do_not_inspect_handles(self):
        lua = self.runtime()
        lua.execute('''
            config.ActionDiagnostics=false
            caster:Action_UseAbilityOnEntity(ability,target)
            assert(reads==0 and #lines==0 and #orders==1)
            config.ActionDiagnostics=true; config.Enable=false
            caster:Action_UseAbility(ability)
            assert(reads==0 and #lines==0 and #orders==2)
        ''')

    def test_sampling_separates_suspect_orders_and_handles_clock_reset(self):
        lua = self.runtime()
        lua.execute('''
            for i=1,100 do caster:Action_UseAbilityOnEntity(ability,target) end
            assert(#orders==100 and #lines==2)
            assert(string.find(lines[1],'script_revision=maintenance-2026-09-27',1,true))
            assert(string.find(lines[1],'game_patch=7.41f',1,true))
            caster:Action_UseAbilityOnLocation(ability,{})
            assert(#lines==3 and string.find(lines[3],'warning=target_type_mismatch',1,true))
            for i=1,100 do caster:Action_UseAbilityOnLocation(ability,{}) end
            assert(#lines==3)
            now=12; caster:Action_UseAbilityOnEntity(ability,target)
            assert(#lines==4 and string.find(lines[4],'sampled_out=99',1,true))
            caster.id=1; caster:Action_UseAbilityOnEntity(ability,target); assert(#lines==6)
            now=0; caster:Action_UseAbilityOnEntity(ability,target); assert(#lines==8)
        ''')

    def test_stash_fog_and_shuriken_details(self):
        lua = self.runtime()
        lua.execute('''
            item=true; inventory[9]=ability
            function target:CanBeSeen() return false end
            function target:GetUnitName() error('must not inspect unseen enemy') end
            caster:Action_UseAbilityOnEntity(ability,target)
            assert(string.find(lines[2],'item_slot=9 warning=inactive_inventory_slot',1,true))
            assert(string.find(lines[2],'target=unseen_or_invalid',1,true))
            item=false; now=12
            function ability:GetName() return 'bounty_hunter_shuriken_toss' end
            function ability:GetSpecialValueInt(k) assert(k=='bonus_damage'); return 500 end
            function caster:GetAbilityByName(k)
                assert(k=='special_bonus_unique_bounty_hunter_2')
                return {IsTrained=function() return true end}
            end
            caster:Action_UseAbilityOnEntity(ability,target)
            assert(string.find(lines[3],'shuriken_damage=500 damage_talent_trained=true',1,true))
        ''')

    def test_logging_failures_cannot_block_original_and_original_errors_propagate(self):
        lua = self.runtime()
        lua.execute('''
            function trace.Record() error('logger failed') end
            assert(caster:Action_UseAbility(ability)=='sent' and #orders==1)
            local brokenClass={Action_UseAbility=function() error('engine failure') end}
            trace.Install(brokenClass,config)
            local ok,err=pcall(brokenClass.Action_UseAbility,caster,ability)
            assert(not ok and string.find(err,'engine failure',1,true))
        ''')

    def test_real_overrides_keep_trace_with_debug_off_and_hidden_guard(self):
        lua = self.runtime(integrated=True)
        lua.execute('''
            print('ordinary debug'); assert(#lines==0)
            caster:Action_UseAbilityOnEntity(ability,target)
            assert(#orders==1 and #lines==2)
            hidden=true; caster:Action_UseAbility(ability)
            assert(#orders==1 and #lines==3)
            assert(string.find(lines[3],'warning=hidden_ability',1,true))
        ''')


if __name__ == '__main__':
    unittest.main()
