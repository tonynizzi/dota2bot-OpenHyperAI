"""Reaction windows delay new decisions without delaying or replaying orders."""
import unittest
from test_bot_regressions import ROOT, LuaRuntime, function


class ReactionDelayTests(unittest.TestCase):
    def runtime(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
            now=10; draws=0; scans=0; enemies={}; projectiles={}; hurt=false
            config={Enable=true,ReactionDelay={Enable=true,MinSeconds=0.15,MaxSeconds=0.30}}
            BOT_MODE_NONE=0
            function DotaTime() return now end
            function RandomFloat(a,b)
                draws=draws+1; low=a; high=b
                return randomValue or (a+b)/2
            end
            bot={alive=true}
            function bot:IsAlive() return self.alive end
            function bot:IsHero() return true end
            function bot:IsIllusion() return false end
            function bot:GetTeam() return 2 end
            function bot:GetNearbyHeroes() scans=scans+1; return enemies end
            function bot:GetIncomingTrackingProjectiles() return projectiles end
            function bot:WasRecentlyDamagedByAnyHero() return hurt end
            function enemy()
                local e={visible=true,alive=true,casting=false}
                function e:IsNull() return false end
                function e:CanBeSeen() return self.visible end
                function e:IsAlive() assert(self.visible); return self.alive end
                function e:IsCastingAbility() assert(self.visible); return self.casting end
                function e:IsUsingAbility() return false end
                function e:IsChanneling() return false end
                function e:GetCurrentActiveAbility() assert(self.visible); return self.spell end
                function e:GetTeam() assert(self.visible); return self.team or 3 end
                return e
            end
            foe=enemy()
        ''')
        lua.globals().ReactionDelay = lua.execute(
            (ROOT / 'bots/FunLib/reaction_delay.lua').read_text(encoding='utf-8'))
        return lua

    def test_new_enemy_draws_once_and_wait_expires_at_sampled_deadline(self):
        lua = self.runtime()
        lua.execute('''
            assert(not ReactionDelay.ShouldWait(bot,config))
            enemies={foe}; now=10.1
            assert(ReactionDelay.ShouldWait(bot,config))
            assert(draws==1 and low==0.15 and high==0.30)
            assert(ReactionDelay.ShouldWait(bot,config) and draws==1)
            now=10.2; assert(ReactionDelay.ShouldWait(bot,config))
            now=10.324; assert(ReactionDelay.ShouldWait(bot,config))
            now=10.326; assert(not ReactionDelay.ShouldWait(bot,config))
            now=11; assert(not ReactionDelay.ShouldWait(bot,config) and draws==1)
        ''')

    def test_new_cast_on_known_enemy_triggers_but_channel_does_not_repeat(self):
        lua = self.runtime()
        lua.execute('''
            enemies={foe}; ReactionDelay.ShouldWait(bot,config)
            now=10.4; assert(not ReactionDelay.ShouldWait(bot,config))
            now=10.5; foe.casting=true; foe.spell={}
            assert(ReactionDelay.ShouldWait(bot,config) and draws==2)
            now=10.8; assert(not ReactionDelay.ShouldWait(bot,config))
            now=11; assert(not ReactionDelay.ShouldWait(bot,config) and draws==2)
            foe.casting=false; now=11.1; ReactionDelay.ShouldWait(bot,config)
            foe.casting=true; now=11.2
            assert(ReactionDelay.ShouldWait(bot,config) and draws==3)
        ''')

    def test_pending_burst_cannot_be_extended_by_more_enemies(self):
        lua = self.runtime()
        lua.execute('''
            enemies={foe}; assert(ReactionDelay.ShouldWait(bot,config))
            for i=1,4 do
                now=10+i*0.05; enemies[#enemies+1]=enemy()
                assert(ReactionDelay.ShouldWait(bot,config) and draws==1)
            end
            now=10.23; enemies[#enemies+1]=enemy()
            assert(not ReactionDelay.ShouldWait(bot,config))
            assert(not ReactionDelay.ShouldWait(bot,config) and draws==1)
        ''')

    def test_fog_is_not_inspected_and_brief_visibility_flicker_is_debounced(self):
        lua = self.runtime()
        lua.execute('''
            foe.visible=false; enemies={foe}
            assert(not ReactionDelay.ShouldWait(bot,config) and draws==0)
            now=10.1; foe.visible=true; assert(ReactionDelay.ShouldWait(bot,config))
            now=10.4; assert(not ReactionDelay.ShouldWait(bot,config))
            now=10.5; foe.visible=false; assert(not ReactionDelay.ShouldWait(bot,config))
            now=10.6; foe.visible=true; assert(not ReactionDelay.ShouldWait(bot,config))
            now=10.7; foe.visible=false; ReactionDelay.ShouldWait(bot,config)
            now=11.3; foe.visible=true
            assert(ReactionDelay.ShouldWait(bot,config) and draws==2)
        ''')

    def test_spell_projectiles_use_stable_counts_and_ignore_normal_attacks(self):
        lua = self.runtime()
        lua.execute('''
            spell={}
            projectiles={{is_attack=true,caster=foe,ability=spell}}
            assert(not ReactionDelay.ShouldWait(bot,config))
            now=10.1; projectiles={{is_attack=false,caster=foe,ability=spell}}
            assert(ReactionDelay.ShouldWait(bot,config))
            -- A fresh API table for the same flying spell is not a fresh event.
            now=10.4; projectiles={{is_attack=false,caster=foe,ability=spell}}
            assert(not ReactionDelay.ShouldWait(bot,config) and draws==1)
            now=10.5; projectiles[2]={is_attack=false,caster=foe,ability=spell}
            assert(ReactionDelay.ShouldWait(bot,config) and draws==2)
        ''')

    def test_friendly_projectiles_and_persistent_damage_do_not_repeat_delays(self):
        lua = self.runtime()
        lua.execute('''
            foe.team=2; projectiles={{is_attack=false,caster=foe,ability={}}}
            assert(not ReactionDelay.ShouldWait(bot,config))
            hurt=true; now=10.1; assert(ReactionDelay.ShouldWait(bot,config))
            now=10.4; assert(not ReactionDelay.ShouldWait(bot,config))
            now=11; assert(not ReactionDelay.ShouldWait(bot,config) and draws==1)
            hurt=false; now=11.1; ReactionDelay.ShouldWait(bot,config)
            hurt=true; now=11.2; assert(ReactionDelay.ShouldWait(bot,config))
        ''')

    def test_disabled_missing_and_zero_settings_do_no_perception_work(self):
        lua = self.runtime()
        lua.execute('''
            enemies={foe}; config.ReactionDelay.Enable=false
            assert(not ReactionDelay.ShouldWait(bot,config))
            assert(not ReactionDelay.ShouldWait(bot,{Enable=true}))
            assert(not ReactionDelay.ShouldWait(bot,nil))
            config.ReactionDelay.Enable=true; config.Enable=false
            assert(not ReactionDelay.ShouldWait(bot,config))
            config.Enable=true; config.ReactionDelay.MinSeconds=0; config.ReactionDelay.MaxSeconds=0
            assert(not ReactionDelay.ShouldWait(bot,config) and scans==0 and draws==0)
        ''')

    def test_death_clock_rollback_and_disable_clear_old_waits(self):
        lua = self.runtime()
        lua.execute('''
            enemies={foe}; assert(ReactionDelay.ShouldWait(bot,config))
            bot.alive=false; assert(not ReactionDelay.ShouldWait(bot,config))
            bot.alive=true; enemies={}; assert(not ReactionDelay.ShouldWait(bot,config))
            now=10.1; enemies={foe}; assert(ReactionDelay.ShouldWait(bot,config))
            now=0; enemies={}; assert(not ReactionDelay.ShouldWait(bot,config))
            now=0.1; enemies={foe}; assert(ReactionDelay.ShouldWait(bot,config))
            config.ReactionDelay.Enable=false; assert(not ReactionDelay.ShouldWait(bot,config))
            config.ReactionDelay.Enable=true; enemies={}
            assert(not ReactionDelay.ShouldWait(bot,config))
        ''')

    def test_per_bot_independent_jitter_and_shared_callback_scan(self):
        lua = self.runtime()
        lua.execute('''
            other=setmetatable({alive=true}, {__index=bot}); enemies={foe}
            randomValue=0.15; assert(ReactionDelay.ShouldWait(bot,config))
            assert(ReactionDelay.ShouldWait(bot,config) and scans==1 and draws==1)
            randomValue=0.30; assert(ReactionDelay.ShouldWait(other,config))
            now=10.2
            assert(not ReactionDelay.ShouldWait(bot,config))
            assert(ReactionDelay.ShouldWait(other,config))
            now=10.31; assert(not ReactionDelay.ShouldWait(other,config))
        ''')

    def test_invalid_bounds_are_sanitized(self):
        lua = self.runtime()
        lua.execute('''
            enemies={foe}; config.ReactionDelay.MinSeconds='bad'; config.ReactionDelay.MaxSeconds=0/0
            assert(ReactionDelay.ShouldWait(bot,config) and low==0.15 and high==0.30)
            now=0; config.ReactionDelay.MinSeconds=5; config.ReactionDelay.MaxSeconds=-1
            assert(ReactionDelay.ShouldWait(bot,config) and low==1 and high==1)
        ''')

    def test_production_callbacks_share_wait_and_reconsider_current_targets(self):
        lua = self.runtime()
        lua.execute('''
            J={Customize=config}; Customize={ThinkLess=1}; botName='npc_dota_hero_test'
            LocalUpdateNotice={Think=function() end}
            now=50; bot.frameProcessTime=0.1
            function bot:IsInvulnerable() return false end
            function RefreshBotHandle() return false end
            function J.IsNoItemIllution() return false end
            function J.IsNoAbilityIllution() return false end
            abilityCalls=0; itemCalls=0; currentTarget='old'; BotBuild={}
            function BotBuild.SkillsComplement() abilityCalls=abilityCalls+1; usedTarget=currentTarget end
            function ItemUsageComplement() itemCalls=itemCalls+1; usedTarget=currentTarget end
        ''')
        path = 'bots/ability_item_usage_generic.lua'
        lua.execute(function(path, 'AbilityUsageThink'))
        lua.execute(function(path, 'ItemUsageThink'))
        lua.execute('''
            enemies={foe}; AbilityUsageThink(); ItemUsageThink()
            assert(abilityCalls==0 and itemCalls==0 and draws==1)
            assert(bot.lastAbilityFrameProcessTime==50 and bot.lastItemFrameProcessTime==50)
            now=50.1; AbilityUsageThink(); ItemUsageThink()
            assert(bot.lastAbilityFrameProcessTime==50 and bot.lastItemFrameProcessTime==50)
            currentTarget='fresh'; now=50.23; AbilityUsageThink(); ItemUsageThink()
            assert(abilityCalls==1 and itemCalls==1 and usedTarget=='fresh')
            assert(draws==1)
        ''')


if __name__ == '__main__':
    unittest.main()
