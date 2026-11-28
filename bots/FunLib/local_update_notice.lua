local Release = require(GetScriptDirectory()..'/FunLib/local_release')
local ReactionDelay = require(GetScriptDirectory()..'/FunLib/reaction_delay')
local X = {}
local announcerID
local sent = 0
local nextMessageTime
local lastTime

local function pickAnnouncer()
    local first
    for _, team in ipairs({TEAM_RADIANT, TEAM_DIRE}) do
        -- Use actual player IDs, bypassing the project's Dire remapping override.
        for _, id in pairs(GetTeamPlayers(team, true)) do
            if IsPlayerBot(id) and (first == nil or id < first) then first = id end
        end
    end
    return first
end

local function isPrimaryHero(bot)
    for index, _ in ipairs(GetTeamPlayers(bot:GetTeam(), true)) do
        if GetTeamMember(index) == bot then return true end
    end
    return false
end

function X.Think(bot, customize)
    if not customize or not customize.Enable or customize.LocalUpdateNotice == false then return end
    local now = DotaTime()
    if lastTime ~= nil and now < lastTime then
        announcerID = nil
        sent = 0
        nextMessageTime = nil
    end
    lastTime = now
    if sent >= 2 or now < -35 or now > 60 then return end
    local gameState = GetGameState()
    if gameState ~= GAME_STATE_PRE_GAME and gameState ~= GAME_STATE_GAME_IN_PROGRESS then return end
    if bot == nil or bot:IsNull() or not bot:IsHero() or bot:IsIllusion() or not bot:IsAlive() then return end
    if announcerID == nil then announcerID = pickAnnouncer() end
    if bot:GetPlayerID() ~= announcerID or not isPrimaryHero(bot) then return end
    if nextMessageTime ~= nil and now < nextMessageTime then return end

    local message
    if sent == 0 then
        message = '[OHA Local ' .. Release.revision .. '] Updates: ' .. Release.changes
    else
        local minimum, maximum = ReactionDelay.GetWindow(customize)
        local delay = 'off'
        if minimum ~= nil then
            delay = string.format('%.0f-%.0f ms', minimum * 1000, maximum * 1000)
        end
        local diagnostics = customize.ActionDiagnostics and 'on' or 'off'
        message = '[OHA Local] Spell/item reaction delay: ' .. delay
            .. '. Cast diagnostics: ' .. diagnostics .. '.'
    end
    bot:ActionImmediate_Chat(message, true)
    sent = sent + 1
    nextMessageTime = now + 6
end

return X
