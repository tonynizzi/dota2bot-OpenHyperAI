local bot = GetBot()
local botName = bot:GetUnitName()
if bot == nil or bot:IsInvulnerable() or not bot:IsHero() or not bot:IsAlive() or not string.find(botName, "hero") or bot:IsIllusion() then return end

local J = require( GetScriptDirectory()..'/FunLib/jmz_func')
local Customize = require( GetScriptDirectory()..'/Customize/general' )

-- BOT_MODE_OUTPOST covers two "walk up and channel on a neutral structure" objectives:
--   * Outposts  (ability_capture,  after an enemy tier-2 tower falls)
--   * Watchers  (ability_lamp_use, opportunistic vision, any time it is safe)
-- Dota only runs mode files for its fixed mode list, so Watchers can't get a mode of their own.

local Outposts = {}
local DidWeGetOutpost = false
local ClosestOutpost = nil
local ClosestOutpostDist = 10000

local IsEnemyTier2Down = false
local hAbilityCapture = bot:GetAbilityByName('ability_capture')

----------
-- Watcher constants (d2vpkr npc_units.txt "npc_dota_lantern", npc_abilities.txt "ability_lamp_use":
-- unit-target channel, 200 cast range, 1.0s channel, 420s active, 120s inactive after being turned off)
----------
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
local WatcherTargetDist = 10000
local WatcherCast = nil                 -- { key, startTime, channelStart, team }
local WatcherFailUntil = {}             -- key -> DotaTime until which this bot skips it
local WatcherTraceSeen = {}
local WatcherNoAbilityLogged = false
local hAbilityLamp = bot:GetAbilityByName(WATCHER_ABILITY)

-- Team-shared Watcher state (modules returned by require are shared by a team's bots;
-- if they aren't, this simply degrades to per-bot memory).
J.WatcherState = J.WatcherState or { lit = {}, claims = {} }
local WatcherShared = J.WatcherState

local CurrentObjective = nil            -- 'outpost' | 'watcher'

local function WatcherTraceLog(...)
	if not WATCHER_TRACE then return end
	local parts = { '[OHA_WATCHER] t=' .. string.format('%.1f', DotaTime()), 'bot=' .. botName }
	for _, v in ipairs({...}) do table.insert(parts, tostring(v)) end
	print(table.concat(parts, ' '))
end

function GetDesire()
	-- local cacheKey = 'GetOutpostDesire'..tostring(bot:GetPlayerID())
	-- local cachedVar = J.Utils.GetCachedVars(cacheKey, 0.5 * (1 + Customize.ThinkLess))
	-- if DotaTime() > 30 and cachedVar ~= nil then return cachedVar end
	local res = GetDesireHelper()
	-- J.Utils.SetCachedVars(cacheKey, res)
	return res
end
function GetDesireHelper()
	if bot:IsInvulnerable() or not bot:IsHero() or not bot:IsAlive() or not string.find(botName, "hero") or bot:IsIllusion() then return BOT_MODE_DESIRE_NONE end

	if not IsEnemyTier2Down
	then
		if GetTower(GetOpposingTeam(), TOWER_TOP_2) == nil
		or GetTower(GetOpposingTeam(), TOWER_MID_2) == nil
		or GetTower(GetOpposingTeam(), TOWER_BOT_2) == nil
		then
			IsEnemyTier2Down = true
		end
	end

	if J.Utils.IsTeamPushingSecondTierOrHighGround(bot) then
		return BOT_MODE_DESIRE_NONE;
	end

	if J.GetEnemiesAroundAncient(bot, 3200) > 0 then
		return BOT_MODE_DESIRE_NONE
	end

	if botName == 'npc_dota_hero_invoker' then return BOT_ACTION_DESIRE_NONE end

	-- local botMode = bot:GetActiveMode()
	-- if (J.IsPushing(bot) or J.IsDefending(bot) or J.IsDoingRoshan(bot) or J.IsDoingTormentor(bot)
	-- or botMode == BOT_MODE_RUNE or botMode == BOT_MODE_SECRET_SHOP or botMode == BOT_MODE_WARD or botMode == BOT_MODE_ROAM)
	-- and bot:GetActiveModeDesire() >= BOT_MODE_DESIRE_HIGH then
	-- 	return BOT_MODE_DESIRE_NONE
	-- end

	local nOutpostDesire = GetOutpostDesire()
	if nOutpostDesire > 0 then
		CurrentObjective = 'outpost'
		return nOutpostDesire
	end

	local nWatcherDesire = GetWatcherDesire()
	if nWatcherDesire > 0 then
		CurrentObjective = 'watcher'
		return nWatcherDesire
	end

	CurrentObjective = nil
	return BOT_ACTION_DESIRE_NONE
end

----------
-- Outpost
----------
function GetOutpostDesire()
	if not IsEnemyTier2Down then return BOT_ACTION_DESIRE_NONE end

	if not DidWeGetOutpost
	then
		for _, unit in pairs(GetUnitList(UNIT_LIST_ALL))
		do
			if unit:GetUnitName() == '#DOTA_OutpostName_North'
			or unit:GetUnitName() == '#DOTA_OutpostName_South'
			then
				table.insert(Outposts, unit)
			end
		end

		DidWeGetOutpost = true
	end

	ClosestOutpost, ClosestOutpostDist = GetClosestOutpost()
	if ClosestOutpost ~= nil and ClosestOutpostDist < 3000
	and not IsEnemyCloserToOutpostLoc(ClosestOutpost:GetLocation(), ClosestOutpostDist)
	and IsSuitableToCaptureOutpost()
	then
		if GetUnitToUnitDistance(bot, ClosestOutpost) < 600
		then
			local nInRangeEnemy = J.GetEnemiesNearLoc(bot:GetLocation(), bot:GetCurrentVisionRange())
			if nInRangeEnemy ~= nil and #nInRangeEnemy >= 1
			then
				return BOT_ACTION_DESIRE_NONE
			end
		end

		return RemapValClamped(GetUnitToUnitDistance(bot, ClosestOutpost), 3000, 0, BOT_ACTION_DESIRE_VERYLOW, BOT_ACTION_DESIRE_HIGH )
	end

	return BOT_ACTION_DESIRE_NONE
end

----------
-- Watcher
----------
-- Watchers are building-class units, so J.IsValid (which rejects buildings) can't be used.
function IsWatcherHandle(unit)
	return unit ~= nil and not unit:IsNull()
end

function IsWatcher(unit)
	if unit == nil or unit:IsNull() or unit:IsHero() then return false end
	local name = string.lower(unit:GetUnitName() or '')
	-- Unit definition is npc_dota_lantern; match loosely in case the map gives it a
	-- display name (outposts report '#DOTA_OutpostName_North' instead of their class).
	return string.find(name, 'lantern', 1, true) ~= nil
		or string.find(name, 'watcher', 1, true) ~= nil
end

function WatcherKey(unit)
	local loc = unit:GetLocation()
	return tostring(math.floor(loc.x / 50)) .. ':' .. tostring(math.floor(loc.y / 50))
end

function ScanWatchers()
	if DotaTime() - WatcherLastScan < WATCHER_SCAN_INTERVAL then return end
	WatcherLastScan = DotaTime()

	local known = {}
	local kept = {}
	for _, w in ipairs(Watchers) do
		if w ~= nil and not w:IsNull() then
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
		WatcherTraceLog('scan watchers=' .. #Watchers)
	end
end

-- Log name, team, IsInvulnerable and IsAttackImmune of nearby non-hero units that could be
-- a Watcher, once per unit and again whenever its team changes.
function TraceNearbyUnit(unit)
	if GetUnitToUnitDistance(bot, unit) > 1200 then return end
	local bWatcher = IsWatcher(unit)
	local bInvuln = unit:IsInvulnerable()
	local bAttackImmune = unit:IsAttackImmune()
	if not bWatcher and not bInvuln and not bAttackImmune then return end

	local key = unit:GetUnitName() .. '@' .. WatcherKey(unit)
	local team = unit:GetTeam()
	if WatcherTraceSeen[key] == team then return end
	WatcherTraceSeen[key] = team
	WatcherTraceLog('unit name=' .. unit:GetUnitName(), 'team=' .. tostring(team),
		'invuln=' .. tostring(bInvuln), 'attackImmune=' .. tostring(bAttackImmune),
		'matched=' .. tostring(bWatcher))
end

function IsWatcherAvailable(w)
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

function GetClosestWatcher(nRadius)
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

function GetWatcherSearchRadius()
	local pos = J.GetPosition(bot)
	if pos == 4 or pos == 5 then
		if J.IsInLaningPhase() then return WATCHER_SUPPORT_LANING_RADIUS end
		return WATCHER_SUPPORT_RADIUS
	end
	if J.IsInLaningPhase() then return 0 end
	return WATCHER_CORE_RADIUS
end

function IsSafeToCaptureWatcher(vWatcherLoc, nDist)
	if J.GetHP(bot) < 0.5 then return false end
	if bot:WasRecentlyDamagedByAnyHero(4) then return false end
	if not IsSuitableToCaptureOutpost() then return false end
	if J.IsRetreating(bot) or J.IsDoingRoshan(bot) or J.IsDoingTormentor(bot) then return false end

	if #J.GetEnemiesNearLoc(bot:GetLocation(), WATCHER_SAFE_RADIUS) > 0 then return false end
	if #J.GetEnemiesNearLoc(vWatcherLoc, WATCHER_SAFE_RADIUS) > 0 then return false end
	if IsEnemyCloserToOutpostLoc(vWatcherLoc, math.max(nDist, WATCHER_SAFE_RADIUS)) then return false end

	return true
end

function GetWatcherDesire()
	if DotaTime() < 0 then return BOT_ACTION_DESIRE_NONE end

	if hAbilityLamp == nil then hAbilityLamp = bot:GetAbilityByName(WATCHER_ABILITY) end
	if hAbilityLamp == nil then
		if not WatcherNoAbilityLogged then
			WatcherNoAbilityLogged = true
			WatcherTraceLog('no ' .. WATCHER_ABILITY .. ' ability on this hero; Watcher capture disabled')
		end
		return BOT_ACTION_DESIRE_NONE
	end

	ScanWatchers()

	-- Keep a started channel going unless it became unsafe.
	if WatcherCast ~= nil and IsWatcherHandle(WatcherTarget) and bot:IsChanneling() then
		if IsSafeToCaptureWatcher(WatcherTarget:GetLocation(), GetUnitToUnitDistance(bot, WatcherTarget)) then
			return BOT_MODE_DESIRE_HIGH
		end
		WatcherTraceLog('abort channel: unsafe')
		return BOT_ACTION_DESIRE_NONE
	end

	local nRadius = GetWatcherSearchRadius()
	if nRadius <= 0 then return BOT_ACTION_DESIRE_NONE end

	local w, dist = GetClosestWatcher(nRadius)
	if w == nil then
		WatcherTarget = nil
		return BOT_ACTION_DESIRE_NONE
	end

	if not IsSafeToCaptureWatcher(w:GetLocation(), dist) then
		return BOT_ACTION_DESIRE_NONE
	end

	WatcherTarget = w
	WatcherTargetDist = dist
	WatcherShared.claims[WatcherKey(w)] = { id = bot:GetPlayerID(), time = DotaTime() }

	return RemapValClamped(dist, nRadius, 0, BOT_ACTION_DESIRE_LOW, BOT_ACTION_DESIRE_MODERATE)
end

-- Track one capture attempt: issued -> channelling -> finished (or never started).
function UpdateWatcherCast()
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
				WatcherTraceLog('turned off enemy watcher key=' .. WatcherCast.key)
			else
				WatcherShared.lit[WatcherCast.key] = now + WATCHER_ACTIVE_DURATION
				WatcherTraceLog('lit watcher key=' .. WatcherCast.key,
					'teamAfter=' .. (IsWatcherHandle(WatcherTarget) and tostring(WatcherTarget:GetTeam()) or 'na'))
			end
		else
			WatcherFailUntil[WatcherCast.key] = now + WATCHER_FAIL_COOLDOWN
			WatcherTraceLog('channel interrupted key=' .. WatcherCast.key, string.format('after=%.2fs', channelled))
		end
		WatcherCast = nil
		WatcherTarget = nil
	elseif now - WatcherCast.startTime > WATCHER_CAST_TIMEOUT then
		WatcherFailUntil[WatcherCast.key] = now + WATCHER_FAIL_COOLDOWN
		WatcherTraceLog('cast never started channelling key=' .. WatcherCast.key)
		WatcherCast = nil
		WatcherTarget = nil
	end
end

function WatcherThink()
	UpdateWatcherCast()
	if WatcherCast ~= nil then return end
	if not IsWatcherHandle(WatcherTarget) or hAbilityLamp == nil then return end

	if GetUnitToUnitDistance(bot, WatcherTarget) > WATCHER_CAST_START_RANGE then
		bot:Action_MoveToLocation(WatcherTarget:GetLocation())
		return
	end

	WatcherCast = { key = WatcherKey(WatcherTarget), startTime = DotaTime(), team = WatcherTarget:GetTeam() }
	WatcherTraceLog('cast ' .. WATCHER_ABILITY .. ' key=' .. WatcherCast.key,
		'name=' .. WatcherTarget:GetUnitName(), 'team=' .. tostring(WatcherCast.team))
	bot:Action_UseAbilityOnEntity(hAbilityLamp, WatcherTarget)
end

function OnStart()

end

function OnEnd()
	ClosestOutpost = nil
	ClosestOutpostDist = 10000
	ShouldWaitInBaseToHeal = false
	if WatcherCast ~= nil and WatcherCast.channelStart == nil then
		WatcherFailUntil[WatcherCast.key] = DotaTime() + WATCHER_FAIL_COOLDOWN
	end
	WatcherCast = nil
	WatcherTarget = nil
	CurrentObjective = nil
end

function Think()
	if J.CanNotUseAction(bot) then return end

	if CurrentObjective == 'watcher' then
		-- Channel bookkeeping must run every tick, even while the bot is mid-channel.
		if WatcherCast ~= nil then
			UpdateWatcherCast()
			return
		end
		if J.Utils.IsBotThinkingMeaningfulAction(bot, Customize.ThinkLess, "outpost") then return end
		WatcherThink()
		return
	end

	if J.Utils.IsBotThinkingMeaningfulAction(bot, Customize.ThinkLess, "outpost") then return end

	if ClosestOutpost ~= nil
	then
		if GetUnitToUnitDistance(bot, ClosestOutpost) > 300
		then
			bot:Action_MoveToLocation(ClosestOutpost:GetLocation())
			return
		else
			if hAbilityCapture then
				bot:Action_UseAbilityOnEntity(hAbilityCapture, ClosestOutpost)
			else
				bot:Action_AttackUnit(ClosestOutpost, false)
			end
			return
		end
	end
end

function GetClosestOutpost()
	local closest = nil
	local dist = 10000

	for i = 1, 2
	do
		if Outposts[i] ~= nil
		and Outposts[i]:GetTeam() ~= GetTeam()
		and GetUnitToUnitDistance(bot, Outposts[i]) < dist
		and not Outposts[i]:IsNull()
		and not Outposts[i]:IsInvulnerable()
		then
			closest = Outposts[i]
			dist = GetUnitToUnitDistance(bot, Outposts[i])
		end
	end

	return closest, dist
end

function IsEnemyCloserToOutpostLoc(opLoc, botDist)
	for _, id in pairs(GetTeamPlayers(GetOpposingTeam()))
	do
		local info = GetHeroLastSeenInfo(id)

		if info ~= nil
		then
			local dInfo = info[1]
			if dInfo ~= nil
			then
				if dInfo ~= nil
				and dInfo.time_since_seen < 5
				and J.GetDistance(dInfo.location, opLoc) < botDist
				then
					return true
				end
			end
		end
	end

	return false
end

function IsSuitableToCaptureOutpost()
	local botTarget = J.GetProperTarget(bot)

	if (J.IsGoingOnSomeone(bot) and J.IsValidTarget(botTarget) and GetUnitToUnitDistance(bot, botTarget) < 700)
	or J.IsDefending(bot)
	or (J.IsDoingTormentor(bot) and J.IsTormentor(botTarget) and J.IsAttacking(bot))
	or (J.IsDoingRoshan(bot) and J.IsRoshan(botTarget) and J.IsAttacking(bot))
	or (J.IsRetreating(bot) and bot:GetActiveModeDesire() > BOT_MODE_DESIRE_HIGH)
	or bot:WasRecentlyDamagedByAnyHero(5)
	or bot:GetActiveMode() == BOT_MODE_DEFEND_ALLY
	or J.GetNumOfAliveHeroes( false ) < J.GetNumOfAliveHeroes( true )
	then
		return false
	end

	return true
end
