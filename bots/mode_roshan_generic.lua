local bot = GetBot()
local botName = bot:GetUnitName();
if bot == nil or bot:IsInvulnerable() or not bot:IsHero() or not bot:IsAlive() or not string.find(botName, "hero") or bot:IsIllusion() then return end

local J = require( GetScriptDirectory()..'/FunLib/jmz_func' )
local Customize = require( GetScriptDirectory()..'/Customize/general' )
local RoshanTrace = require( GetScriptDirectory()..'/FunLib/roshan_diagnostics' )

local killTime = 0.0
local shouldKillRoshan = false
local DoingRoshanMessage = DotaTime()

-- local rTwinGate = nil
-- local dTwinGate = nil
-- local rTwinGateLoc = Vector(5888, -7168, 256)
-- local dTwinGateLoc = Vector(6144, 7552, 256)

local sinceRoshAliveTime = 0
local roshTimeFlag = false
local initDPSFlag = false

local Roshan
local currentDPSCheck
local baseDangerUntil

function GetDesire()
	local res, reason = GetDesireHelper()
	if J.Customize.Enable and J.Customize.RoshanDiagnostics then
		RoshanTrace.Record(bot, res, reason, J, {
			aliveEstimate = shouldKillRoshan,
			dpsLatched = initDPSFlag,
			dpsCurrent = currentDPSCheck,
		})
	end
	if res > 0.6 then J.ModeAnnounce(bot, 'say_roshan', 30) end
	return res
end
function GetDesireHelper()
	currentDPSCheck = nil
	if bot:IsInvulnerable() or not bot:IsHero() or not bot:IsAlive() or not string.find(botName, "hero") or bot:IsIllusion() then return BOT_MODE_DESIRE_NONE, 'ineligible_bot' end
    if not J.Utils.IsValidUnit(Roshan) then
        Roshan = nil
        local nCreeps = bot:GetNearbyNeutralCreeps(700)
        for _, creepOrRoshan in pairs(nCreeps)
        do
            if creepOrRoshan:GetUnitName() == "npc_dota_roshan"
            then
                Roshan = creepOrRoshan
            end
        end
    end

	-- 如果在打高地 就别撤退去干别的
	if J.Utils.IsTeamPushingSecondTierOrHighGround(bot) then
		return BOT_MODE_DESIRE_NONE, 'team_pushing'
	end

    local now = DotaTime()
    if baseDangerUntil ~= nil and baseDangerUntil > now + 4 then baseDangerUntil = nil end
    if J.GetEnemiesAroundAncient(bot, 3200) > 0
    or J.Utils.CountEnemyHeroesOnHighGround(bot:GetTeam()) >= 2 then
        baseDangerUntil = now + 4
    end
    if baseDangerUntil ~= nil and now < baseDangerUntil then
		return BOT_MODE_DESIRE_NONE, 'ancient_danger_or_damage'
	end

    local timeOfDay = J.CheckTimeOfDay()

    local nTeamFightLocation = J.GetTeamFightLocation(bot)
    if nTeamFightLocation ~= nil
    and GetUnitToLocationDistance(bot, J.GetCurrentRoshanLocation()) < 1600
    and GetUnitToLocationDistance(bot, nTeamFightLocation) < 2000
    then
        return BOT_ACTION_DESIRE_NONE, timeOfDay == 'day'
            and 'nearby_teamfight_day' or 'nearby_teamfight_night'
    end

    local lEnemyHeroesAroundLoc = J.GetLastSeenEnemiesNearLoc(bot:GetLocation(), 1200)
    if #lEnemyHeroesAroundLoc >= 2 then
        return BOT_ACTION_DESIRE_NONE, 'recent_enemies_near_bot'
    end

    local pit = J.GetCurrentRoshanLocation()
    if #J.GetEnemiesNearLoc(pit, 2500) > 0
    or #J.GetLastSeenEnemiesNearLoc(pit, 2500) > 0 then
        return BOT_MODE_DESIRE_NONE, 'enemies_near_pit'
    end

    local aliveAlly = J.GetNumOfAliveHeroes(false)
    local aliveEnemy = J.GetNumOfAliveHeroes(true)
    local hasSameOrMoreHero = aliveAlly >= aliveEnemy

    if not hasSameOrMoreHero then
        return BOT_ACTION_DESIRE_NONE, 'outnumbered_alive'
    end

    local nCoreWithNoEmptySlot = 0
    local aliveHeroesList = {}
    local botCanParticipate = false
    for _, h in pairs(J.GetRoshanParticipants(GetUnitList(UNIT_LIST_ALLIED_HEROES), pit)) do
        if h:IsAlive()
        then
            if J.Utils.CountBackpackEmptySpace(h) <= 0 and J.IsCore(h) then
                nCoreWithNoEmptySlot = nCoreWithNoEmptySlot + 1
            end

            -- do not take rosh if the cores do not have any empty slot, it may get dropped on ground.
            if nCoreWithNoEmptySlot >= 2 then
                return BOT_ACTION_DESIRE_NONE, 'core_backpacks_full'
            end
            table.insert(aliveHeroesList, h)
            if h == bot then botCanParticipate = true end
        end
    end

    if not botCanParticipate then return BOT_MODE_DESIRE_NONE, 'participant_unavailable' end

    shouldKillRoshan = J.IsRoshanAlive()

    if shouldKillRoshan
    and not roshTimeFlag
    then
        sinceRoshAliveTime = DotaTime()
        roshTimeFlag = true
    else
        if not shouldKillRoshan
        then
            sinceRoshAliveTime = 0
            roshTimeFlag = false
        end
    end

    currentDPSCheck = J.HasEnoughDPSForRoshan(aliveHeroesList, Roshan)
    -- Readiness must recover and expire with the current team, not latch forever.
    initDPSFlag = currentDPSCheck
    if not initDPSFlag then return BOT_ACTION_DESIRE_NONE, 'dps_not_ready' end

    local nEnemyHeroes = J.GetEnemiesNearLoc(bot:GetLocation(), 1300)
    if nEnemyHeroes ~= nil and #nEnemyHeroes > 0
    then
        return BOT_ACTION_DESIRE_NONE, 'visible_enemies_near_bot'
    end

    if J.IsRoshanCloseToChangingSides()
    then
        local botTarget = J.GetProperTarget(bot)
        if J.IsRoshan(botTarget) then
            return RemapValClamped(J.GetHP(botTarget), 1, 0, BOT_ACTION_DESIRE_NONE, BOT_ACTION_DESIRE_VERYHIGH ), 'finish_before_side_change'
        end
        if not J.IsValid(botTarget) or not J.IsRoshan(botTarget) then
            return BOT_ACTION_DESIRE_NONE, 'side_change_soon'
        end
    end

    if J.IsRoshan(Roshan) and Roshan:GetHealth() / Roshan:GetMaxHealth() < 0.5 then
        return math.min(0.9, RemapValClamped(Roshan:GetHealth() / Roshan:GetMaxHealth(),
            1, 0, BOT_MODE_DESIRE_MODERATE, BOT_MODE_DESIRE_ABSOLUTE)), 'finish_low_health_roshan'
    end

    if shouldKillRoshan
    and initDPSFlag
    then
        local human, humanPing = J.GetHumanPing()
        if human ~= nil and DotaTime() > 5.0 then
            if humanPing ~= nil
            and humanPing.normal_ping
            and GetUnitToLocationDistance(human, J.GetCurrentRoshanLocation()) < 4500
            and J.GetDistance(humanPing.location, J.GetCurrentRoshanLocation()) < 600
            and DotaTime() < humanPing.time + 5.0
            then
                return 0.9, 'human_ping'
            end
        end

        local mul = RemapValClamped(DotaTime(), sinceRoshAliveTime, sinceRoshAliveTime + (2.5 * 60), 1, 2)
        local nRoshanDesire = (GetRoshanDesire() * mul)

        return Clamp(nRoshanDesire, 0, 0.9), 'engine_desire_scaled'
    end

    if not shouldKillRoshan then return BOT_ACTION_DESIRE_NONE, 'respawn_estimate_not_ready' end
    return BOT_ACTION_DESIRE_NONE, 'dps_not_ready'
end
