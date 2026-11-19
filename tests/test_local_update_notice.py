"""Local startup chat, using production Lua and isolated per-bot contexts."""
import unittest
from test_bot_regressions import ROOT, LuaRuntime, function


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


class LocalUpdateNoticeTests(unittest.TestCase):
    def runtime(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
            now=-40; gameState=5; messages={}; scans=0
            TEAM_RADIANT=2; TEAM_DIRE=3; GAME_STATE_PRE_GAME=5; GAME_STATE_GAME_IN_PROGRESS=6
            config={Enable=true,LocalUpdateNotice=true,ActionDiagnostics=false,
                ReactionDelay={Enable=true,MinSeconds=0.15,MaxSeconds=0.30}}
            function DotaTime() return now end
            function GetGameState() return gameState end
            function GetScriptDirectory() return 'bots' end
            ids={[2]={0,1,2,3,4},[3]={5,6,7,8,9}}; humans={[0]=true}
            heroes={}; rosters={[2]={},[3]={}}
            function makeHero(id,team)
                local h={id=id,team=team,alive=true,illusion=false}
                function h:GetPlayerID() return self.id end
                function h:GetTeam() return self.team end
                function h:IsHero() return true end
                function h:IsAlive() return self.alive end
                function h:IsIllusion() return self.illusion end
                function h:IsNull() return false end
                function h:ActionImmediate_Chat(text,all)
                    assert(all==true and #text<256)
                    messages[#messages+1]={id=self.id,text=text,time=now}
                end
                return h
            end
            for team,list in pairs(ids) do
                for index,id in ipairs(list) do
                    heroes[id]=makeHero(id,team); rosters[team][index]=heroes[id]
                end
            end
            current=heroes[1]
            function GetTeamPlayers(team,bypass)
                assert(bypass==true); scans=scans+1; return ids[team]
            end
            function GetTeamMember(index) return rosters[current.team][index] end
            function IsPlayerBot(id) return not humans[id] end
        ''')
        lua.globals().Release = lua.execute(read('bots/FunLib/local_release.lua'))
        lua.globals().ReactionLibrary = lua.execute(read('bots/FunLib/reaction_delay.lua'))
        lua.execute('''
            function require(path)
                if string.find(path,'local_release',1,true) then return Release end
                if string.find(path,'reaction_delay',1,true) then return ReactionLibrary end
                error('unexpected dependency: '..path)
            end
        ''')
        lua.globals().Notice = lua.execute(read('bots/FunLib/local_update_notice.lua'))
        return lua

    def test_two_short_lines_stagger_once_inside_start_window(self):
        lua = self.runtime()
        lua.execute('''
            Notice.Think(current,config); assert(#messages==0 and scans==0)
            now=-35; Notice.Think(current,config); assert(#messages==1)
            assert(string.find(messages[1].text,Release.revision,1,true))
            assert(string.find(messages[1].text,Release.changes,1,true))
            for i=1,10 do Notice.Think(current,config) end
            now=-30; Notice.Think(current,config); assert(#messages==1)
            now=-29; Notice.Think(current,config); assert(#messages==2)
            assert(string.find(messages[2].text,'150-300 ms',1,true))
            assert(string.find(messages[2].text,'Cast diagnostics: off',1,true))
            now=10; Notice.Think(current,config); now=61; Notice.Think(current,config)
            assert(#messages==2)
        ''')

    def test_election_is_global_even_with_isolated_bot_contexts(self):
        counts = []
        for player in range(10):
            lua = self.runtime()
            lua.execute(f'''current=heroes[{player}]; now=-35
                Notice.Think(current,config); now=-29; Notice.Think(current,config)''')
            counts.append(lua.eval('#messages'))
        self.assertEqual(counts, [0, 2, 0, 0, 0, 0, 0, 0, 0, 0])

    def test_dire_only_bots_use_real_ids_and_team_member_indices(self):
        lua = self.runtime()
        lua.execute('''
            for id=0,4 do humans[id]=true end
            ids[3]={17,8,12}; rosters[3]={}
            for i,id in ipairs(ids[3]) do
                heroes[id]=makeHero(id,3); rosters[3][i]=heroes[id]
            end
            current=heroes[8]; now=0; Notice.Think(current,config)
            now=6; Notice.Think(current,config)
            assert(#messages==2 and messages[1].id==8)
        ''')

    def test_clones_and_deaths_cannot_duplicate_the_notice(self):
        lua = self.runtime()
        lua.execute('''
            now=-35
            clone=makeHero(1,2); Notice.Think(clone,config); assert(#messages==0)
            current.illusion=true; Notice.Think(current,config); assert(#messages==0)
            current.illusion=false; current.alive=false
            Notice.Think(current,config); assert(#messages==0)
            current.alive=true; Notice.Think(current,config); assert(#messages==1)
            now=-29; current.alive=false; Notice.Think(current,config); assert(#messages==1)
            now=-28; current.alive=true; Notice.Think(current,config); assert(#messages==2)
            now=0; current.alive=false; Notice.Think(current,config)
            now=10; current.alive=true; Notice.Think(current,config); assert(#messages==2)
        ''')

    def test_disable_settings_and_non_game_states_suppress_chat(self):
        lua = self.runtime()
        lua.execute('''
            now=-35; config.LocalUpdateNotice=false; Notice.Think(current,config)
            config.LocalUpdateNotice=true; config.Enable=false; Notice.Think(current,config)
            Notice.Think(current,nil); config.Enable=true
            gameState=1; Notice.Think(current,config)
            gameState=9; Notice.Think(current,config)
            gameState=6; now=61; Notice.Think(current,config)
            assert(#messages==0 and scans==0)
        ''')

    def test_older_customizations_and_effective_reaction_settings(self):
        for settings, expected in (
            ("config.ReactionDelay=nil", "off"),
            ("config.ReactionDelay.Enable=false", "off"),
            ("config.ReactionDelay.MinSeconds=0; config.ReactionDelay.MaxSeconds=0", "off"),
            ("config.ReactionDelay.MinSeconds='bad'; config.ReactionDelay.MaxSeconds=0/0", "150-300 ms"),
            ("config.ReactionDelay.MinSeconds=0.4; config.ReactionDelay.MaxSeconds=0.2", "400-400 ms"),
        ):
            with self.subTest(settings=settings):
                lua = self.runtime()
                lua.execute(settings + '''
                    config.LocalUpdateNotice=nil; config.ActionDiagnostics=true
                    now=-35; Notice.Think(current,config); now=-29; Notice.Think(current,config)
                    assert(#messages==2)
                ''')
                message = lua.globals().messages[2]['text']
                self.assertIn(f'reaction delay: {expected}.', message)
                self.assertIn('Cast diagnostics: on.', message)

    def test_new_match_clock_resets_announcement(self):
        lua = self.runtime()
        lua.execute('''
            now=-35; Notice.Think(current,config); now=-29; Notice.Think(current,config)
            now=600; Notice.Think(current,config); assert(#messages==2)
            now=-35; Notice.Think(current,config); now=-29; Notice.Think(current,config)
            assert(#messages==4)
        ''')

    def test_production_hook_runs_even_while_reaction_gate_is_waiting(self):
        lua = self.runtime()
        lua.execute('''
            bot=current; J={Customize=config}; LocalUpdateNotice=Notice
            ReactionDelay={ShouldWait=function() return true end}
            function RefreshBotHandle() return false end
        ''')
        lua.execute(function('bots/ability_item_usage_generic.lua', 'AbilityUsageThink'))
        lua.execute('''
            now=-35; AbilityUsageThink(); now=-29; AbilityUsageThink()
            assert(#messages==2)
        ''')


if __name__ == '__main__':
    unittest.main()
