-- When a human player uses High Five (plus_high_five), one bot answers in all-chat.
--
-- Detection: the caster gets modifier_plus_high_five_requested for the 10s request window.
-- Only human players count. FretBots' kill taunt puts the same modifier on bots, and that
-- must not trigger a reply.
--
-- Speaker: exactly one bot in the whole match, chosen the same way by both teams' scripts:
--   1. the lowest-ID living bot on the high-fiver's team (allies are always visible), else
--   2. the lowest-ID living bot on the other team, but only if it can see the high-fiver.
local X = {}

X.Enabled = true
X.Message = 'Good girl!'

local REQUEST_MODIFIER = 'modifier_plus_high_five_requested'
local RESCAN_GAP = 1.0          -- a bot that missed this long re-primes instead of replying
local MIN_REPLY_GAP = 2.0       -- per-bot spam guard

local states = {}               -- per bot player ID: { lastScan, primed, seen = {humanID=true}, lastReply }

local function otherTeam(team)
    if team == TEAM_RADIANT then return TEAM_DIRE end
    return TEAM_RADIANT
end

local function firstLivingBot(team)
    local first
    -- Actual player IDs, bypassing the project's Dire remapping override.
    for _, id in pairs(GetTeamPlayers(team, true)) do
        if IsPlayerBot(id) and IsHeroAlive(id) and (first == nil or id < first) then first = id end
    end
    return first
end

-- Returns the speaker's player ID and team for a high five by a human on humanTeam.
function X.PickSpeaker(humanTeam)
    local id = firstLivingBot(humanTeam)
    if id ~= nil then return id, humanTeam end
    local team = otherTeam(humanTeam)
    id = firstLivingBot(team)
    if id ~= nil then return id, team end
    return nil, nil
end

local function isPrimaryHero(bot)
    for index, _ in ipairs(GetTeamPlayers(bot:GetTeam(), true)) do
        if GetTeamMember(index) == bot then return true end
    end
    return false
end

local function humansRequesting()
    local requesting = {}
    for _, listType in ipairs({UNIT_LIST_ALLIED_HEROES, UNIT_LIST_ENEMY_HEROES}) do
        for _, hero in pairs(GetUnitList(listType) or {}) do
            if hero ~= nil and not hero:IsNull() and hero:IsHero() and not hero:IsIllusion() then
                local id = hero:GetPlayerID()
                if id ~= nil and id >= 0 and not IsPlayerBot(id) and hero:HasModifier(REQUEST_MODIFIER) then
                    requesting[id] = hero:GetTeam()
                end
            end
        end
    end
    return requesting
end

function X.Think(bot)
    if not X.Enabled then return end
    if bot == nil or bot:IsNull() or not bot:IsHero() or bot:IsIllusion() or not bot:IsAlive() then return end
    local gameState = GetGameState()
    if gameState ~= GAME_STATE_PRE_GAME and gameState ~= GAME_STATE_GAME_IN_PROGRESS then return end
    if not isPrimaryHero(bot) then return end

    local now = DotaTime()
    local botID = bot:GetPlayerID()
    local state = states[botID]
    if state == nil or state.lastScan == nil or now < state.lastScan or now - state.lastScan > RESCAN_GAP then
        -- First scan, new match, or this bot was dead/idle: record what is already up without replying.
        state = { primed = false, seen = {}, lastReply = state and state.lastReply or nil }
        states[botID] = state
    end
    state.lastScan = now

    local requesting = humansRequesting()
    for humanID, humanTeam in pairs(requesting) do
        if not state.seen[humanID] and state.primed then
            local speakerID = X.PickSpeaker(humanTeam)
            if speakerID == botID
            and (state.lastReply == nil or now < state.lastReply or now - state.lastReply >= MIN_REPLY_GAP)
            then
                bot:ActionImmediate_Chat(X.Message, true)
                state.lastReply = now
            end
        end
    end
    state.seen = {}
    for humanID, _ in pairs(requesting) do state.seen[humanID] = true end
    state.primed = true
end

return X
