local bot = GetBot()
local botName = bot:GetUnitName()
if bot == nil or bot:IsInvulnerable() or not bot:IsHero() or not bot:IsAlive() or not string.find(botName, "hero") or bot:IsIllusion() then return end

local J = require( GetScriptDirectory()..'/FunLib/jmz_func')
local Customize = require( GetScriptDirectory()..'/Customize/general' )

-- Overrides the engine's built-in BOT_MODE_WATCHER (mode 28, dota_bot_mode_watcher.cpp).
-- Without this file the engine's default Watcher mode runs, and in playtests bots stood
-- in it next to Watchers for 30-70s at a time ("staring"). This version only lights a
-- Watcher when it is safe and cheap, channels ability_lamp_use, and always lets go.
--
-- Game data (d2vpkr): unit npc_dota_lantern (neutral, building-class, 800/450 vision);
-- ability_lamp_use: unit-target channel, 200 cast range, 1.0s channel, 420s active,
-- 120s inactive after an enemy-lit Watcher is turned off.

local WATCHER_ABILITY = 'ability_lamp_use'
local WATCHER_ACTIVE_DURATION = 420     -- a Watcher we light stays ours this long
local WATCHER_OFF_DURATION = 120        -- an enemy Watcher we turn off is untargetable this long
local WATCHER_FAIL_COOLDOWN = 30        -- per-bot back-off after a cast that never started channelling
local WATCHER_SCAN_INTERVAL = 10
local WATCHER_CAST_START_RANGE = 400    -- issue the cast from here; the engine walks the last bit
local WATCHER_CAST_TIMEOUT = 3          -- seconds from cast order to channel start before giving up
local WATCHER_SAFE_RADIUS = 1600        -- no visible / recently seen enemy hero this close
local WATCHER_SUPPORT_RADIUS = 2000     -- pos 4/5 detour distance
local WATCHER_SUPPORT_LANING_RADIUS = 1200
local WATCHER_CORE_RADIUS = 800         -- cores only grab Watchers they are standing next to
-- Opt-in trace, printed with the [OHA_WATCHER] prefix (passes the global print filter).
-- Logs nearby non-hero units that are invulnerable/attack-immune or look like Watchers,
-- plus every capture attempt and its outcome. Set to false once names are confirmed in-game.
local WATCHER_TRACE = true

local Watchers = {}
local WatcherLastScan = -1000
local WatcherTarget = nil
local WatcherCast = nil                 -- { key, startTime, channelStart, team }
local WatcherFailUntil = {}             -- key -> DotaTime until which this bot skips it
local WatcherTraceSeen = {}
local WatcherNoAbilityLogged = false
local hAbilityLamp = bot:GetAbilityByName(WATCHER_ABILITY)

-- Team-shared Watcher state (modules returned by require are shared by a team's bots;
-- if they aren't, this simply degrades to per-bot memory).
J.WatcherState = J.WatcherState or { lit = {}, claims = {} }
local WatcherShared = J.WatcherState

local function TraceLog(...)
	if not WATCHER_TRACE then return end
	local parts = { '[OHA_WATCHER] t=' .. string.format('%.1f', DotaTime()), 'bot=' .. botName }
	for _, v in ipairs({...}) do table.insert(parts, tostring(v)) end
	print(table.concat(parts, ' '))
end

-- Watchers are building-class units, so J.IsValid (which rejects buildings) can't be used.
local function IsWatcherHandle(unit)
	return unit ~= nil and not unit:IsNull()
end

local function IsWatcher(unit)
	if not IsWatcherHandle(unit) or unit:IsHero() then return false end
	local name = string.lower(unit:GetUnitName() or '')
	-- Unit definition is npc_dota_lantern; match loosely in case the map gives it a
	-- display name (outposts report '#DOTA_OutpostName_North' instead of their class).
	return string.find(name, 'lantern', 1, true) ~= nil
		or string.find(name, 'watcher', 1, true) ~= nil
end

local function WatcherKey(unit)
	local loc = unit:GetLocation()
	return tostring(math.floor(loc.x / 50)) .. ':' .. tostring(math.floor(loc.y / 50))
end

-- Log name, team, IsInvulnerable and IsAttackImmune of nearby non-hero units that could be
-- a Watcher, once per unit and again whenever its team changes.
local function TraceNearbyUnit(unit)
	if GetUnitToUnitDistance(bot, unit) > 1200 then return end
	local bWatcher = IsWatcher(unit)
	local bInvuln = unit:IsInvulnerable()
	local bAttackImmune = unit:IsAttackImmune()
	if not bWatcher and not bInvuln and not bAttackImmune then return end

	local key = unit:GetUnitName() .. '@' .. WatcherKey(unit)
	local team = unit:GetTeam()
	if WatcherTraceSeen[key] == team then return end
	WatcherTraceSeen[key] = team
	TraceLog('unit name=' .. unit:GetUnitName(), 'team=' .. tostring(team),
		'invuln=' .. tostring(bInvuln), 'attackImmune=' .. tostring(bAttackImmune),
		'matched=' .. tostring(bWatcher),
		'stateMod=' .. tostring(unit:HasModifier('modifier_watcher_state')),
		'buffMod=' .. tostring(unit:HasModifier('modifier_watcher_buff')))
end

local function ScanWatchers()
	if DotaTime() - WatcherLastScan < WATCHER_SCAN_INTERVAL then return end
	WatcherLastScan = DotaTime()

	local known = {}
	local kept = {}
	for _, w in ipairs(Watchers) do
		if IsWatcherHandle(w) then
			table.insert(kept, w)
			known[w] = true
		end
	end
	Watchers = kept

	local nBefore = #Watchers
	for _, unit in pairs(GetUnitList(UNIT_LIST_ALL)) do
		if unit ~= nil and not unit:IsNull() and not unit:IsHero() then
			if IsWatcher(unit) and not known[unit] then
				table.insert(Watchers, unit)
				known[unit] = true
			end
			if WATCHER_TRACE then TraceNearbyUnit(unit) end
		end
	end

	if #Watchers ~= nBefore then
		TraceLog('scan watchers=' .. #Watchers)
	end
end

local function IsWatcherAvailable(w)
	if not IsWatcherHandle(w) then return false end
	if w:GetTeam() == GetTeam() then return false end

	local key = WatcherKey(w)
	local now = DotaTime()
	local lit = WatcherShared.lit[key]
	if lit ~= nil and now < lit then return false end
	local failUntil = WatcherFailUntil[key]
	if failUntil ~= nil and now < failUntil then return false end

	local claim = WatcherShared.claims[key]
	if claim ~= nil and claim.id ~= bot:GetPlayerID() and now - claim.time < 3 then return false end

	return true
end

local function GetClosestWatcher(nRadius)
	local closest = nil
	local dist = nRadius
	for _, w in ipairs(Watchers) do
		if IsWatcherAvailable(w) then
			local d = GetUnitToUnitDistance(bot, w)
			if d < dist then
				closest = w
				dist = d
			end
		end
	end
	return closest, dist
end

local function GetSearchRadius()
	local pos = J.GetPosition(bot)
	if pos == 4 or pos == 5 then
		if J.IsInLaningPhase() then return WATCHER_SUPPORT_LANING_RADIUS end
		return WATCHER_SUPPORT_RADIUS
	end
	if J.IsInLaningPhase() then return 0 end
	return WATCHER_CORE_RADIUS
end

local function IsEnemyRecentlySeenNear(vLoc, nRadius)
	for _, id in pairs(GetTeamPlayers(GetOpposingTeam())) do
		local info = GetHeroLastSeenInfo(id)
		if info ~= nil then
			local dInfo = info[1]
			if dInfo ~= nil
			and dInfo.time_since_seen < 5
			and J.GetDistance(dInfo.location, vLoc) < nRadius
			then
				return true
			end
		end
	end
	return false
end

local function IsBotBusy()
	local botTarget = J.GetProperTarget(bot)
	return (J.IsGoingOnSomeone(bot) and J.IsValidTarget(botTarget) and GetUnitToUnitDistance(bot, botTarget) < 700)
		or J.IsDefending(bot)
		or J.IsRetreating(bot)
		or J.IsDoingRoshan(bot)
		or J.IsDoingTormentor(bot)
		or bot:GetActiveMode() == BOT_MODE_DEFEND_ALLY
		or J.GetNumOfAliveHeroes( false ) < J.GetNumOfAliveHeroes( true )
end

local function IsSafeToCapture(vWatcherLoc, nDist)
	if J.GetHP(bot) < 0.5 then return false end
	if bot:WasRecentlyDamagedByAnyHero(5) then return false end
	if IsBotBusy() then return false end

	if #J.GetEnemiesNearLoc(bot:GetLocation(), WATCHER_SAFE_RADIUS) > 0 then return false end
	if #J.GetEnemiesNearLoc(vWatcherLoc, WATCHER_SAFE_RADIUS) > 0 then return false end
	if IsEnemyRecentlySeenNear(vWatcherLoc, math.max(nDist, WATCHER_SAFE_RADIUS)) then return false end

	return true
end

-- Track one capture attempt: issued -> channelling -> finished (or never started).
local function UpdateCast()
	if WatcherCast == nil then return end
	local now = DotaTime()

	if bot:IsChanneling() then
		if WatcherCast.channelStart == nil then WatcherCast.channelStart = now end
		return
	end

	if WatcherCast.channelStart ~= nil then
		local channelled = now - WatcherCast.channelStart
		if channelled >= 0.8 then
			if WatcherCast.team == GetOpposingTeam() then
				WatcherShared.lit[WatcherCast.key] = now + WATCHER_OFF_DURATION
				TraceLog('turned off enemy watcher key=' .. WatcherCast.key)
			else
				WatcherShared.lit[WatcherCast.key] = now + WATCHER_ACTIVE_DURATION
				TraceLog('lit watcher key=' .. WatcherCast.key,
					'teamAfter=' .. (IsWatcherHandle(WatcherTarget) and tostring(WatcherTarget:GetTeam()) or 'na'))
			end
		else
			WatcherFailUntil[WatcherCast.key] = now + WATCHER_FAIL_COOLDOWN
			TraceLog('channel interrupted key=' .. WatcherCast.key, string.format('after=%.2fs', channelled))
		end
		WatcherCast = nil
		WatcherTarget = nil
	elseif now - WatcherCast.startTime > WATCHER_CAST_TIMEOUT then
		WatcherFailUntil[WatcherCast.key] = now + WATCHER_FAIL_COOLDOWN
		TraceLog('cast never started channelling key=' .. WatcherCast.key)
		WatcherCast = nil
		WatcherTarget = nil
	end
end

local function GetDesireHelper()
	if bot:IsInvulnerable() or not bot:IsHero() or not bot:IsAlive() or not string.find(botName, "hero") or bot:IsIllusion() then return BOT_MODE_DESIRE_NONE end
	if DotaTime() < 0 then return BOT_MODE_DESIRE_NONE end
	-- Kept in line with the outpost mode, which never lets Invoker capture.
	if botName == 'npc_dota_hero_invoker' then return BOT_MODE_DESIRE_NONE end
	if J.Utils.IsTeamPushingSecondTierOrHighGround(bot) then return BOT_MODE_DESIRE_NONE end
	if J.GetEnemiesAroundAncient(bot, 3200) > 0 then return BOT_MODE_DESIRE_NONE end

	if hAbilityLamp == nil then hAbilityLamp = bot:GetAbilityByName(WATCHER_ABILITY) end
	if hAbilityLamp == nil then
		if not WatcherNoAbilityLogged then
			WatcherNoAbilityLogged = true
			TraceLog('no ' .. WATCHER_ABILITY .. ' ability on this hero; Watcher capture disabled')
		end
		return BOT_MODE_DESIRE_NONE
	end

	ScanWatchers()

	-- Keep a started channel going unless it became unsafe.
	if WatcherCast ~= nil and IsWatcherHandle(WatcherTarget) and bot:IsChanneling() then
		if IsSafeToCapture(WatcherTarget:GetLocation(), GetUnitToUnitDistance(bot, WatcherTarget)) then
			return BOT_MODE_DESIRE_HIGH
		end
		TraceLog('abort channel: unsafe')
		return BOT_MODE_DESIRE_NONE
	end

	local nRadius = GetSearchRadius()
	if nRadius <= 0 then return BOT_MODE_DESIRE_NONE end

	local w, dist = GetClosestWatcher(nRadius)
	if w == nil then
		WatcherTarget = nil
		return BOT_MODE_DESIRE_NONE
	end

	if not IsSafeToCapture(w:GetLocation(), dist) then
		return BOT_MODE_DESIRE_NONE
	end

	WatcherTarget = w
	WatcherShared.claims[WatcherKey(w)] = { id = bot:GetPlayerID(), time = DotaTime() }

	return RemapValClamped(dist, nRadius, 0, BOT_MODE_DESIRE_LOW, BOT_MODE_DESIRE_MODERATE)
end

function GetDesire()
	return GetDesireHelper()
end

function OnStart()

end

function OnEnd()
	if WatcherCast ~= nil and WatcherCast.channelStart == nil then
		WatcherFailUntil[WatcherCast.key] = DotaTime() + WATCHER_FAIL_COOLDOWN
	end
	WatcherCast = nil
	WatcherTarget = nil
end

function Think()
	if J.CanNotUseAction(bot) then return end

	-- Channel bookkeeping must run every tick, even while the bot is mid-channel.
	if WatcherCast ~= nil then
		UpdateCast()
		return
	end

	if J.Utils.IsBotThinkingMeaningfulAction(bot, Customize.ThinkLess, "watcher") then return end
	if not IsWatcherHandle(WatcherTarget) or hAbilityLamp == nil then return end

	if GetUnitToUnitDistance(bot, WatcherTarget) > WATCHER_CAST_START_RANGE then
		bot:Action_MoveToLocation(WatcherTarget:GetLocation())
		return
	end

	WatcherCast = { key = WatcherKey(WatcherTarget), startTime = DotaTime(), team = WatcherTarget:GetTeam() }
	TraceLog('cast ' .. WATCHER_ABILITY .. ' key=' .. WatcherCast.key,
		'name=' .. WatcherTarget:GetUnitName(), 'team=' .. tostring(WatcherCast.team))
	bot:Action_UseAbilityOnEntity(hAbilityLamp, WatcherTarget)
end
