"""High Five all-chat reply, using production Lua with one isolated runtime per bot."""
import unittest
from test_bot_regressions import ROOT, LuaRuntime, function


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


MOCKS = '''
TEAM_RADIANT=2; TEAM_DIRE=3; GAME_STATE_PRE_GAME=5; GAME_STATE_GAME_IN_PROGRESS=6
UNIT_LIST_ALLIED_HEROES=1; UNIT_LIST_ENEMY_HEROES=2
now=0; gameState=6; messages={}
ids={[2]={0,1,2,3,4},[3]={5,6,7,8,9}}; humans={[0]=true}; dead={}
requesting={}; visibleTo={[2]={},[3]={}}; illusionOf={}
function DotaTime() return now end
function GetGameState() return gameState end
function GetScriptDirectory() return 'bots' end
function GetTeamPlayers(team, bypass) assert(bypass==true); return ids[team] end
function IsPlayerBot(id) return not humans[id] end
function IsHeroAlive(id) return not dead[id] end
local function teamOf(id) for t,l in pairs(ids) do for _,v in ipairs(l) do if v==id then return t end end end end
function makeHero(id, illusion)
    local h={id=id, illusion=illusion or false}
    function h:GetPlayerID() return self.id end
    function h:GetTeam() return teamOf(self.id) end
    function h:IsHero() return true end
    function h:IsIllusion() return self.illusion end
    function h:IsAlive() return not dead[self.id] end
    function h:IsNull() return false end
    function h:HasModifier(name)
        return name=='modifier_plus_high_five_requested' and requesting[self.id]==true and not self.illusion
    end
    function h:ActionImmediate_Chat(text, all)
        assert(all==true)
        messages[#messages+1]={id=self.id, text=text, time=now}
    end
    return h
end
heroes={}; for id=0,9 do heroes[id]=makeHero(id) end
function GetTeamMember(index) return heroes[ids[current:GetTeam()][index]] end
function GetUnitList(kind)
    local myTeam=current:GetTeam(); local out={}
    for id=0,9 do
        local t=teamOf(id)
        local ally = t==myTeam
        if (kind==UNIT_LIST_ALLIED_HEROES and ally) or (kind==UNIT_LIST_ENEMY_HEROES and not ally and visibleTo[myTeam][id]) then
            table.insert(out, heroes[id])
            if illusionOf[id] then table.insert(out, makeHero(id, true)) end
        end
    end
    return out
end
'''


class HighFiveChatTests(unittest.TestCase):
    def setUp(self):
        # One runtime per bot: Radiant and Dire scripts never share module state in the game.
        self.bots = {}
        for bot_id in range(10):
            lua = LuaRuntime(unpack_returned_tuples=True)
            lua.execute(MOCKS)
            lua.execute(f'current=heroes[{bot_id}]')
            lua.globals().Chat = lua.execute(read('bots/FunLib/high_five_chat.lua'))
            self.bots[bot_id] = lua

    def world(self, code):
        for lua in self.bots.values():
            lua.execute(code)

    def tick(self, seconds=0.1, frames=1):
        for _ in range(frames):
            self.world(f'now = now + {seconds}')
            for bot_id, lua in self.bots.items():
                if lua.eval('humans[current:GetPlayerID()]'):
                    continue
                lua.execute('Chat.Think(current)')

    def messages(self):
        out = []
        for lua in self.bots.values():
            out += [(m['id'], m['text']) for m in lua.globals().messages.values()]
        return out

    def test_first_bot_on_the_high_fivers_team_says_it_once(self):
        self.tick()
        self.world('requesting[0]=true; visibleTo[3][0]=true')
        self.tick(frames=50)  # the request stays up for its whole window
        self.assertEqual(self.messages(), [(1, 'Good girl!')])
        self.world('requesting[0]=nil'); self.tick(frames=5)
        self.world('requesting[0]=true'); self.tick()
        self.assertEqual(self.messages(), [(1, 'Good girl!'), (1, 'Good girl!')], 'a later high five gets a new reply')

    def test_dead_first_bot_hands_over_to_the_next(self):
        self.world('dead[1]=true')
        self.tick()
        self.world('requesting[0]=true')
        self.tick(frames=3)
        self.assertEqual(self.messages(), [(2, 'Good girl!')])

    def test_enemy_bot_answers_only_when_the_human_team_has_no_living_bots(self):
        self.world('ids={[2]={0,1,2,3,4},[3]={5,6,7,8,9}}; humans={[0]=true,[1]=true,[2]=true,[3]=true,[4]=true}')
        self.tick()
        self.world('requesting[2]=true')
        self.tick(frames=3)
        self.assertEqual(self.messages(), [], 'Dire cannot see the high-fiver, so nobody guesses')
        self.world('requesting[2]=nil'); self.tick()
        self.world('requesting[2]=true; visibleTo[3][2]=true'); self.tick(frames=3)
        self.assertEqual(self.messages(), [(5, 'Good girl!')])

    def test_dire_human_is_answered_by_first_dire_bot(self):
        self.world('humans={[7]=true}')
        self.tick()
        self.world('requesting[7]=true; visibleTo[2][7]=true')
        self.tick(frames=3)
        self.assertEqual(self.messages(), [(5, 'Good girl!')])

    def test_bot_taunts_and_illusions_do_not_count(self):
        self.tick()
        self.world('requesting[3]=true')  # FretBots puts the modifier on a bot after a kill
        self.tick(frames=3)
        self.assertEqual(self.messages(), [])
        self.world('requesting[3]=nil; illusionOf[0]=true; requesting[0]=true')
        self.tick(frames=3)
        self.assertEqual(self.messages(), [(1, 'Good girl!')], 'one reply even with an illusion of the human around')

    def test_request_already_up_after_a_gap_is_not_repeated(self):
        self.tick()
        self.world('requesting[0]=true')
        self.tick()
        self.assertEqual(len(self.messages()), 1)
        self.world('dead[1]=true')       # speaker dies mid-request; bot 2 takes over
        self.tick(frames=3)
        self.world('dead[1]=nil')        # bot 1 respawns while the request is still up
        self.tick(seconds=3)
        self.tick(frames=3)
        self.assertEqual(len(self.messages()), 1, 'a takeover or respawn must not reply to the same request')

    def test_disabled_or_out_of_game_is_silent(self):
        self.tick()
        self.world('Chat.Enabled=false; requesting[0]=true')
        self.tick(frames=3)
        self.world('Chat.Enabled=true; requesting[0]=nil'); self.tick()
        self.world('gameState=7; requesting[0]=true'); self.tick(frames=3)
        self.assertEqual(self.messages(), [])

    def test_production_hook_runs_before_the_reaction_gate(self):
        source = function('bots/ability_item_usage_generic.lua', 'AbilityUsageThink')
        self.assertLess(source.index('HighFiveChat.Think(bot)'), source.index('ReactionDelay.ShouldWait'))
        self.assertIn("require(GetScriptDirectory()..'/FunLib/high_five_chat')",
                      read('bots/ability_item_usage_generic.lua'))


if __name__ == '__main__':
    unittest.main()
