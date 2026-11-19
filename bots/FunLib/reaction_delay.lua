-- Brief response windows for newly observed combat cues. No orders are queued here.
local X = {}
local states = setmetatable({}, {__mode = 'k'})
local scanInterval = 0.05
local visibilityGrace = 0.5

local function seconds(value, fallback)
    if type(value) ~= 'number' or value ~= value then return fallback end
    return math.max(0, math.min(value, 1))
end

local function observe(bot, state, now)
    local changed = false
    for _, enemy in pairs(bot:GetNearbyHeroes(1600, true, BOT_MODE_NONE)) do
        -- Never inspect casts/health of a hero we cannot currently see.
        if enemy ~= nil and not enemy:IsNull() and enemy:CanBeSeen() and enemy:IsAlive() then
            local previous = state.enemies[enemy]
            local cast = false
            if enemy:IsCastingAbility() or enemy:IsUsingAbility() or enemy:IsChanneling() then
                cast = enemy:GetCurrentActiveAbility() or true
            end
            if previous == nil or (previous.missing and now - previous.seenAt > visibilityGrace)
                or (cast ~= false and cast ~= previous.cast) then
                changed = true
            end
            state.enemies[enemy] = {seenAt = now, cast = cast}
        end
    end
    for enemy, observation in pairs(state.enemies) do
        if observation.seenAt ~= now then
            observation.missing = true
            if now - observation.seenAt > visibilityGrace then state.enemies[enemy] = nil end
        end
    end

    local projectiles = {}
    for _, projectile in pairs(bot:GetIncomingTrackingProjectiles()) do
        local caster = projectile.caster
        if not projectile.is_attack and projectile.ability ~= nil
            and (caster == nil or caster:IsNull() or not caster:CanBeSeen()
                or caster:GetTeam() ~= bot:GetTeam()) then
            -- The API supplies no stable projectile ID. Count concurrent spells by
            -- caster/ability rather than using the freshly returned table as identity.
            local key = tostring(caster) .. ':' .. tostring(projectile.ability)
            projectiles[key] = (projectiles[key] or 0) + 1
            if projectiles[key] > (state.projectiles[key] or 0) then changed = true end
        end
    end
    state.projectiles = projectiles

    local hurt = bot:WasRecentlyDamagedByAnyHero(0.2)
    if hurt and not state.hurt then changed = true end
    state.hurt = hurt
    return changed
end

-- Shared with the startup notice so it reports the effective, sanitized window.
function X.GetWindow(customize)
    local settings = customize and customize.ReactionDelay
    if not customize or not customize.Enable or type(settings) ~= 'table' or not settings.Enable then
        return nil
    end
    local minimum = seconds(settings.MinSeconds, 0.15)
    local maximum = math.max(minimum, seconds(settings.MaxSeconds, 0.30))
    if maximum == 0 then return nil end
    return minimum, maximum
end

function X.ShouldWait(bot, customize)
    local minimum, maximum = X.GetWindow(customize)
    if minimum == nil or not bot:IsAlive() or not bot:IsHero() or bot:IsIllusion() then
        states[bot] = nil
        return false
    end

    local now = DotaTime()
    local state = states[bot]
    if state == nil or now < state.lastTime then
        state = {lastTime = now, nextScan = now, enemies = {}, projectiles = {}, hurt = false}
        states[bot] = state
    end
    state.lastTime = now
    local changed = false
    if now >= state.nextScan then
        changed = observe(bot, state, now)
        state.nextScan = now + scanInterval
    end

    if state.deadline ~= nil then
        if now < state.deadline then return true end
        state.deadline = nil
        -- Let both item and ability callbacks reconsider this burst. New cues
        -- during a pending wait do not restart it and starve the bot of turns.
        state.settledUntil = now + scanInterval
        return false
    end
    if changed and (state.settledUntil == nil or now >= state.settledUntil) then
        state.deadline = now + RandomFloat(minimum, maximum)
        return now < state.deadline
    end
    return false
end

return X
