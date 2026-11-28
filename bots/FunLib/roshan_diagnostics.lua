-- Read-only, per-bot sampling. No actions, chat, or cross-bot state assumptions.
local X = {}
local states = {}
local SAMPLE_INTERVAL = 2
local HEARTBEAT_INTERVAL = 15

local function value(v)
    if v == nil then return 'na' end
    return tostring(v)
end

function X.Record(bot, desire, reason, J, context)
    local now = DotaTime()
    local id = bot:GetPlayerID()
    local key = tostring(bot:GetTeam()) .. ':' .. tostring(id)
    local previous = states[key]
    -- Rate-limit all additional perception work, not just printing.
    if previous and now >= previous.sampleTime and now - previous.sampleTime < SAMPLE_INTERVAL then return end

    local mode = bot:GetActiveMode()
    local signature = table.concat({reason or 'unknown', tostring(mode),
        tostring(math.floor(desire * 20)), value(context.dpsCurrent), value(context.dpsLatched)}, ':')
    if previous and now >= previous.printTime and previous.signature == signature
    and now - previous.printTime < HEARTBEAT_INTERVAL then
        previous.sampleTime = now
        return
    end
    states[key] = {sampleTime = now, printTime = now, signature = signature}

    local pit = J.GetCurrentRoshanLocation()
    local allies = {}
    local alive, nearby, healthyNearby = 0, 0, 0
    for slot = 1, #GetTeamPlayers(bot:GetTeam()) do
        local ally = GetTeamMember(slot)
        if ally ~= nil and not ally:IsNull() and ally:IsAlive() then
            alive = alive + 1
            local distance = GetUnitToLocationDistance(ally, pit)
            local hp = ally:GetHealth() / math.max(1, ally:GetMaxHealth())
            local mp = ally:GetMana() / math.max(1, ally:GetMaxMana())
            if distance <= 2500 then
                nearby = nearby + 1
                if hp >= 0.5 then healthyNearby = healthyNearby + 1 end
            end
            -- ID@distance:HP%:MP%:active-mode. These are observations, not commitments.
            allies[#allies + 1] = string.format('%d@%.0f:%.0f:%.0f:%d',
                ally:GetPlayerID(), distance, hp * 100, mp * 100, ally:GetActiveMode())
        end
    end
    local seenNearPit = J.GetLastSeenEnemiesNearLoc(pit, 2500)
    local seenNearBot = J.GetLastSeenEnemiesNearLoc(bot:GetLocation(), 1200)
    local visibleNearPit = J.GetEnemiesNearLoc(pit, 2500)
    print(string.format('[OHA_ROSHAN] t=%.1f team=%d player=%d reason=%s desire=%.3f active_mode=%d '
        .. 'pit=%.0f,%.0f bot_distance=%.0f alive_estimate_cached=%s dps_current=%s dps_latched=%s '
        .. 'allies_alive=%d allies_near2500=%d allies_hp50_near2500=%d '
        .. 'enemy_recent_bot1200=%d enemy_recent_pit2500=%d enemy_visible_pit2500=%d allies=[%s]',
        now, bot:GetTeam(), id, reason or 'unknown', desire, mode, pit.x, pit.y,
        GetUnitToLocationDistance(bot, pit), value(context.aliveEstimate),
        value(context.dpsCurrent), value(context.dpsLatched), alive, nearby, healthyNearby,
        #seenNearBot, #seenNearPit, #visibleNearPit, table.concat(allies, ',')))
end

return X
