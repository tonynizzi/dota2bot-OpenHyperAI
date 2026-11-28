-- Observes submitted cast orders only. Never changes or rejects an order.
local X = {}
local states = {}
local installed = setmetatable({}, {__mode = 'k'})
local revision = 'maintenance-2026-09-27'
local interval = 2

local function read(object, method, fallback, ...)
    if object == nil then return fallback end
    local args = {...}
    local ok, value = pcall(function() return object[method](object, unpack(args)) end)
    if ok and value ~= nil then return value end
    return fallback
end

local function token(value)
    return (tostring(value):gsub('[%s=%[%]]', '_'):sub(1, 160))
end

local function hasFlag(behavior, flag)
    return type(behavior) == 'number' and math.floor(behavior / flag) % 2 == 1
end

function X.Record(caster, ability, target, method, kind, config)
    if not config.Enable or not config.ActionDiagnostics then return end
    local now = GameTime()
    local player = read(caster, 'GetPlayerID', -1)
    local hero = read(caster, 'GetUnitName', 'unknown')
    local key = tostring(player) .. ':' .. hero
    local state = states[key]
    if state == nil or now < state.lastTime then
        state = {lastTime = now, normal = -math.huge, suspect = -math.huge,
            normalSkipped = 0, suspectSkipped = 0}
        states[key] = state
        print('[OHA_CAST] event=session script_revision=' .. revision
            .. ' game_patch=' .. token(config.DiagnosticsGamePatch or 'unknown')
            .. ' patch_source=user_config script_path=' .. token(GetScriptDirectory())
            .. ' player=' .. token(player) .. ' hero=' .. token(hero))
    end
    state.lastTime = now

    local name = read(ability, 'GetName', 'unknown')
    local behavior = read(ability, 'GetBehavior', -1)
    local warning = 'none'
    if ability == nil then
        warning = 'nil_ability'
    elseif read(ability, 'IsHidden', false) then
        warning = 'hidden_ability'
    elseif behavior >= 0 then
        -- A hint, not an engine verdict: hybrid spells may have multiple flags.
        if kind == 'unit' and not hasFlag(behavior, 8) then
            warning = 'target_type_mismatch'
        elseif kind == 'point' and not hasFlag(behavior, 16) then
            warning = 'target_type_mismatch'
        elseif kind == 'none' and not hasFlag(behavior, 4)
            and (hasFlag(behavior, 8) or hasFlag(behavior, 16)) then
            warning = 'target_type_mismatch'
        end
    end
    local slot = -1
    if read(ability, 'IsItem', false) then
        for i = 0, 16 do
            if read(caster, 'GetItemInSlot', nil, i) == ability then slot = i; break end
        end
        if slot >= 6 and slot <= 14 then warning = 'inactive_inventory_slot' end
    end
    local lane = warning == 'none' and 'normal' or 'suspect'
    local skipped = lane .. 'Skipped'
    if now - state[lane] < interval then
        state[skipped] = state[skipped] + 1
        return
    end
    state[lane] = now

    local targetName = kind
    if kind == 'unit' then
        targetName = 'unseen_or_invalid'
        if read(target, 'CanBeSeen', false) then
            targetName = read(target, 'GetUnitName', 'unknown')
        end
    elseif kind == 'tree' then
        targetName = target
    end
    local detail = ''
    if name == 'bounty_hunter_shuriken_toss' then
        local talent = read(caster, 'GetAbilityByName', nil, 'special_bonus_unique_bounty_hunter_2')
        detail = ' shuriken_damage=' .. token(read(ability, 'GetSpecialValueInt', 'unknown', 'bonus_damage'))
            .. ' damage_talent_trained=' .. token(read(talent, 'IsTrained', false))
    end
    print(string.format('[OHA_CAST] event=attempt game_time=%.2f player=%s hero=%s method=%s ability=%s target_type=%s target=%s behavior=%s item_slot=%s warning=%s sampled_out=%d%s',
        now, token(player), token(hero), token(method), token(name), token(kind),
        token(targetName), token(behavior), token(slot), warning, state[skipped], detail))
    state[skipped] = 0
end

local function wrap(class, method, kind, config)
    local original = class[method]
    if type(original) ~= 'function' then return end
    class[method] = function(self, ability, ...)
        if config.Enable and config.ActionDiagnostics then
            -- Broken handles/logging must not prevent the original order or hide its error.
            pcall(X.Record, self, ability, select(1, ...), method, kind, config)
        end
        return original(self, ability, ...)
    end
end

function X.Install(class, config)
    if installed[class] then return end
    installed[class] = true
    for _, prefix in ipairs({'Action_', 'ActionQueue_', 'ActionPush_'}) do
        wrap(class, prefix .. 'UseAbility', 'none', config)
        wrap(class, prefix .. 'UseAbilityOnEntity', 'unit', config)
        wrap(class, prefix .. 'UseAbilityOnLocation', 'point', config)
        wrap(class, prefix .. 'UseAbilityOnTree', 'tree', config)
    end
end

return X
