if NeutralItems == nil
then
    NeutralItems = {}
end

-- 7.42: neutral items have 4 tiers (T1 0:00, T2 15:00, T3 30:00, T4 50:00).
-- The old tier-5 list and its timing block were removed. Infinite Madstone (65:00) is ignored.
local isTierOneDone   = false
local isTierTwoDone   = false
local isTierThreeDone = false
local isTierFourDone  = false
local DOTA_ITEM_NEUTRAL_SLOT = 16

-- Pools verified against Valve's itemlist `neutral_item_tier` for 7.42.
local Tier1NeutralItems = {
    -- --[[Trusty Shovel]]         "item_trusty_shovel",        -- removed in 7.41
    -- --[[Arcane Ring]]           "item_arcane_ring",
    -- --[[Fairy's Trinket]]       "item_mysterious_hat",
    -- --[[Pig Pole]]              "item_unstable_wand",        -- removed in 7.41
    -- --[[Safety Bubble]]         "item_safety_bubble",        -- now T2 in 7.42
    -- --[[Lance of Pursuit]]      "item_lance_of_pursuit",
    -- --[[Occult Bracelet]]       "item_occult_bracelet",      -- cycled out in 7.42
    -- --[[Duelist Gloves]]        "item_duelist_gloves",       -- cycled out in 7.42
    -- --[[Broom Handle]]          "item_broom_handle",
    -- --[[Royal Jelly]]           "item_royal_jelly",
    -- --[[Faded Broach]]          "item_faded_broach",
    -- --[[Spark Of Courage]]      "item_spark_of_courage",     -- removed in 7.41
    -- --[[Ironwood Tree]]         "item_ironwood_tree",
    -- --[[Mana Draught]]          "item_mana_draught",         -- moved to T2 in 7.41
    -- --[[Ripper's Lash]]         "item_rippers_lash",         -- removed in 7.41
    -- --[[Orb of Destruction]]    "item_orb_of_destruction",   -- removed in 7.41
    -- --[[Dagger of Ristul]]      "item_dagger_of_ristul",     -- cycled out in 7.42
    --[[Chipped Vest]]          "item_chipped_vest",
    --[[Ash Legion Shield]]     "item_ash_legion_shield",
    --[[Possessed Mask]]        "item_possessed_mask",
    --[[Dormant Curio]]         "item_dormant_curio",
    --[[Red Ledger]]            "item_red_ledger",           -- new in 7.42
    --[[Weighted Dice]]         "item_weighted_dice",
    --[[Pollywog Charm]]        "item_polliwog_charm",
    --[[Seeds of Serenity]]     "item_seeds_of_serenity",    -- moved from T2 in 7.42
    --[[Forager's Kit]]         "item_foragers_kit",
    --[[Kobold Cup]]            "item_kobold_cup",
    --[[Stonefeather Satchel]]  "item_stonefeather_satchel",
    --[[Tumbler's Toy]]         "item_pogo_stick",           -- moved from T2 in 7.42
}

local Tier2NeutralItems = {
    -- --[[Dragon Scale]]          "item_dragon_scale",
    -- --[[Whisper of the Dread]]  "item_whisper_of_the_dread",
    -- --[[Pupil's Gift]]          "item_pupils_gift",
    -- --[[Grove Bow]]             "item_grove_bow",
    -- --[[Philosopher's Stone]]   "item_philosophers_stone",
    -- --[[Bullwhip]]              "item_bullwhip",
    -- --[[Orb of Destruction]]    "item_orb_of_destruction",
    -- --[[Specialist's Array]]    "item_specialists_array",
    -- --[[Eye of the Vizier]]     "item_eye_of_the_vizier",
    -- --[[Vampire Fangs]]         "item_vampire_fangs",
    -- --[[Gossamer's Cape]]       "item_gossamer_cape",        -- removed in 7.41
    -- --[[Light Collector]]       "item_light_collector",
    -- --[[Iron Talon]]            "item_iron_talon",           -- removed in 7.41
    -- --[[Brigand's Blade]]       "item_misericorde",          -- removed in 7.41
    -- --[[Essence Ring]]          "item_essence_ring",         -- cycled out in 7.42
    -- --[[Searing Signet]]        "item_searing_signet",       -- cycled out in 7.42
    -- --[[Poor Man's Shield]]     "item_poor_mans_shield",     -- cycled out in 7.42
    -- --[[Medallion of Courage]]  "item_medallion_of_courage", -- cycled out in 7.42
    -- --[[Tumbler's Toy]]         "item_pogo_stick",           -- moved to T1 in 7.42
    -- --[[Seeds of Serenity]]     "item_seeds_of_serenity",    -- moved to T1 in 7.42
    --[[Psychic Headband]]      "item_psychic_headband",     -- moved from T3 in 7.42
    --[[Safety Bubble]]         "item_safety_bubble",        -- new in 7.42
    --[[Metamorphic Mandible]]  "item_metamorphic_mandible", -- moved from T4 in 7.42
    --[[Jidi Pollen Bag]]       "item_jidi_pollen_bag",      -- moved from T3 in 7.42
    --[[Brick]]                 "item_brick",                -- new in 7.42
    --[[Crippling Crossbow]]    "item_crippling_crossbow",
    --[[Imp Claw]]              "item_imp_claw",             -- new in 7.42
    --[[Gunpowder Gauntlets]]   "item_gunpowder_gauntlets",  -- moved from T3 in 7.42
    --[[Defiant Shell]]         "item_defiant_shell",
    --[[Partisan's Brand]]      "item_partisans_brand",      -- moved from T3 in 7.42
    --[[Spellslinger]]          "item_spellslinger",         -- moved from T3 in 7.42
    --[[Mana Draught]]          "item_mana_draught",
}

local Tier3NeutralItems = {
    -- --[[Defiant Shell]]         "item_defiant_shell",        -- moved to T2 in 7.41
    -- --[[Paladin Sword]]         "item_paladin_sword",
    -- --[[Nemesis Curse]]         "item_nemesis_curse",        -- removed in 7.41
    -- --[[Vindicator's Axe]]      "item_vindicators_axe",
    -- --[[Craggy Coat]]           "item_craggy_coat",
    -- --[[Enchanted Quiver]]      "item_enchanted_quiver",
    -- --[[Elven Tunic]]           "item_elven_tunic",
    -- --[[Doubloon]]              "item_doubloon",
    -- --[[Vambrace]]              "item_vambrace",
    -- --[[Whisper of the Dread]]  "item_whisper_of_the_dread", -- removed in 7.41
    -- --[[Gale Guard]]            "item_gale_guard",           -- removed in 7.41
    -- --[[Ninja Gear]]            "item_ninja_gear",           -- removed in 7.41
    -- --[[Cloak of Flames]]       "item_cloak_of_flames",      -- cycled out in 7.42
    -- --[[Unrelenting Eye]]       "item_unrelenting_eye",      -- cycled out in 7.42
    -- --[[Psychic Headband]]      "item_psychic_headband",     -- moved to T2 in 7.42
    -- --[[Gunpowder Gauntlets]]   "item_gunpowder_gauntlets",  -- moved to T2 in 7.42
    -- --[[Jidi Pollen Bag]]       "item_jidi_pollen_bag",      -- moved to T2 in 7.42
    -- --[[Spellslinger]]          "item_spellslinger",         -- moved to T2 in 7.42
    -- --[[Partisan's Brand]]      "item_partisans_brand",      -- moved to T2 in 7.42
    --[[Prophet's Pendulum]]    "item_prophets_pendulum",    -- moved from T4 in 7.42
    --[[Dandelion Amulet]]      "item_dandelion_amulet",     -- moved from T4 in 7.42
    --[[Idol of Scree'auk]]     "item_idol_of_screeauk",     -- moved from T4 in 7.42
    --[[Balmhook]]              "item_balmhook",             -- new in 7.42
    --[[Rattlecage]]            "item_rattlecage",           -- moved from T4 in 7.42
    --[[Stormcrafter]]          "item_stormcrafter",
    --[[Enchanter's Bauble]]    "item_enchanters_bauble",    -- moved from T4 in 7.42
    --[[Ceremonial Robe]]       "item_ceremonial_robe",      -- new in 7.42
    --[[Harmonizer]]            "item_harmonizer",           -- moved from T5 in 7.42
    --[[Vile Phial]]            "item_vile_phial",           -- new in 7.42
    --[[Serrated Shiv]]         "item_serrated_shiv",
    --[[Revenant's Brooch]]     "item_revenants_brooch",     -- new in 7.42
}

local Tier4NeutralItems = {
    -- --[[Timeless Relic]]        "item_timeless_relic",
    -- --[[Ascetic Cap]]           "item_ascetic_cap",
    -- --[[Aviana's Feather]]      "item_avianas_feather",
    -- --[[Ninja Gear]]            "item_ninja_gear",
    -- --[[Telescope]]             "item_spy_gadget",
    -- --[[Trickster Cloak]]       "item_trickster_cloak",
    -- --[[Ancient Guardian]]      "item_ancient_guardian",
    -- --[[Havoc Hammer]]          "item_havoc_hammer",
    -- --[[Martyr's Plate]]        "item_martyrs_plate",
    -- --[[Ogre Seal Totem]]       "item_ogre_seal_totem",      -- removed in 7.41
    -- --[[Magnifying Monocle]]    "item_magnifying_monocle",   -- removed in 7.41
    -- --[[Pyrrhic Cloak]]         "item_pyrrhic_cloak",        -- removed in 7.41
    -- --[[Giant Maul]]            "item_giant_maul",           -- cycled out in 7.42
    -- --[[Flayer's Bota]]         "item_flayers_bota",         -- cycled out in 7.42
    -- --[[Rattlecage]]            "item_rattlecage",           -- moved to T3 in 7.42
    -- --[[Idol of Screeauk]]      "item_idol_of_screeauk",     -- moved to T3 in 7.42
    -- --[[Metamorphic Mandible]]  "item_metamorphic_mandible", -- moved to T2 in 7.42
    -- --[[Dandelion Amulet]]      "item_dandelion_amulet",     -- moved to T3 in 7.42
    -- --[[Enchanter's Bauble]]    "item_enchanters_bauble",    -- moved to T3 in 7.42
    -- --[[Prophet's Pendulum]]    "item_prophets_pendulum",    -- moved to T3 in 7.42
    -- Old tier-5 entries (7.42 removed tier 5):
    -- --[[Force Boots]]           "item_force_boots",
    -- --[[Seer Stone]]            "item_seer_stone",
    -- --[[Mirror Shield]]         "item_mirror_shield",
    -- --[[Apex]]                  "item_apex",
    -- --[[Arcanist's Armor]]      "item_force_field",
    -- --[[Pirate Hat]]            "item_pirate_hat",           -- removed in 7.41
    -- --[[Unwavering Condition]]  "item_unwavering_condition",
    -- --[[Book of Shadows]]       "item_book_of_shadows",
    -- --[[Magic Lamp]]            "item_panic_button",         -- removed in 7.41
    -- --[[Stygian Desolator]]     "item_desolator_2",          -- cycled out in 7.42
    -- --[[Spider Legs]]           "item_spider_legs",          -- cycled out in 7.42
    --[[Fallen Sky]]            "item_fallen_sky",           -- moved from T5 in 7.42
    --[[Flicker]]               "item_flicker",              -- new in 7.42
    --[[Minotaur Horn]]         "item_minotaur_horn",        -- moved from T5 in 7.42
    --[[Mind Breaker]]          "item_mind_breaker",         -- new in 7.42
    --[[Divine Regalia]]        "item_divine_regalia",       -- moved from T5 in 7.42
    --[[Witchbane]]             "item_heavy_blade",          -- moved from T5 in 7.42
    --[[Helm of the Hivemind]]  "item_helm_of_the_hivemind", -- new in 7.42
    --[[Dezun Bloodrite]]       "item_dezun_bloodrite",      -- moved from T5 in 7.42
    --[[Conjurer's Catalyst]]   "item_conjurers_catalyst",
    --[[Giant's Ring]]          "item_giants_ring",          -- new in 7.42
    --[[Book of the Dead]]      "item_demonicon",            -- moved from T5 in 7.42
    --[[Riftshadow Prism]]      "item_riftshadow_prism",     -- moved from T5 in 7.42
}

-- 7.42 enchantment tiers:
--   Alert, Brawny, Mystical, Quickened, Tough: 1-3.  Vital: 1-2.
--   Crude, Keen-eyed, Nimble, Titanic: 2-3.  Greedy: 3.
--   Evolved, Timeless, Audacious, Feverish, Fleetfooted, Hulking, Manic, Vampiric: 4.
-- Vast, Wise and Boundless are not in the 7.42 notes (probably cycled out), so they are disabled:
--   { name = "item_enhancement_vast",      tier = 2/3, ... }  -- not in 7.42
--   { name = "item_enhancement_boundless", tier = 5,   ... }  -- not in 7.42
--   { name = "item_enhancement_wise",      tier = 5,   ... }  -- not in 7.42
local enhancements = {
    -- Tier 1 enhancements
    { name = "item_enhancement_mystical",  tier = 1, roles = {1, 1, 1, 1, 1}, realName = "Mystical Enhancement" },
    { name = "item_enhancement_brawny",    tier = 1, roles = {1, 1, 3, 2, 2}, realName = "Brawny Enhancement" },
    { name = "item_enhancement_alert",     tier = 1, roles = {1, 2, 1, 1, 1}, realName = "Alert Enhancement" },
    { name = "item_enhancement_tough",     tier = 1, roles = {1, 1, 2, 2, 1}, realName = "Tough Enhancement" },
    { name = "item_enhancement_quickened", tier = 1, roles = {1, 1, 1, 2, 1}, realName = "Quickened Enhancement" },
    { name = "item_enhancement_vital",     tier = 1, roles = {1, 1, 1, 1, 1}, realName = "Vital Enhancement" },

    -- Tier 2 enhancements
    { name = "item_enhancement_mystical",  tier = 2, roles = {1, 1, 1, 1, 1}, realName = "Mystical Enhancement" },
    { name = "item_enhancement_brawny",    tier = 2, roles = {1, 1, 3, 2, 2}, realName = "Brawny Enhancement" },
    { name = "item_enhancement_alert",     tier = 2, roles = {1, 2, 1, 1, 1}, realName = "Alert Enhancement" },
    { name = "item_enhancement_tough",     tier = 2, roles = {1, 1, 2, 2, 1}, realName = "Tough Enhancement" },
    { name = "item_enhancement_quickened", tier = 2, roles = {1, 1, 1, 2, 1}, realName = "Quickened Enhancement" },
    { name = "item_enhancement_vital",     tier = 2, roles = {1, 1, 1, 1, 1}, realName = "Vital Enhancement" },
    { name = "item_enhancement_keen_eyed", tier = 2, roles = {1, 1, 1, 1, 2}, realName = "Keen Eyed Enhancement" },
    { name = "item_enhancement_nimble",    tier = 2, roles = {1, 1, 1, 1, 1}, realName = "Nimble Enhancement" },
    { name = "item_enhancement_crude",     tier = 2, roles = {1, 1, 1, 1, 1}, realName = "Crude Enhancement" },
    { name = "item_enhancement_titanic",   tier = 2, roles = {1, 1, 1, 1, 1}, realName = "Titanic Enhancement" },

    -- Tier 3 enhancements
    { name = "item_enhancement_mystical",  tier = 3, roles = {1, 1, 1, 1, 1}, realName = "Mystical Enhancement" },
    { name = "item_enhancement_brawny",    tier = 3, roles = {1, 1, 3, 2, 2}, realName = "Brawny Enhancement" },
    { name = "item_enhancement_alert",     tier = 3, roles = {1, 2, 1, 1, 1}, realName = "Alert Enhancement" },
    { name = "item_enhancement_tough",     tier = 3, roles = {1, 1, 2, 2, 1}, realName = "Tough Enhancement" },
    { name = "item_enhancement_quickened", tier = 3, roles = {1, 1, 1, 2, 1}, realName = "Quickened Enhancement" },
    { name = "item_enhancement_keen_eyed", tier = 3, roles = {1, 1, 1, 1, 2}, realName = "Keen Eyed Enhancement" },
    { name = "item_enhancement_greedy",    tier = 3, roles = {1, 1, 1, 2, 2}, realName = "Greedy Enhancement" },
    { name = "item_enhancement_nimble",    tier = 3, roles = {1, 1, 1, 1, 1}, realName = "Nimble Enhancement" },
    { name = "item_enhancement_crude",     tier = 3, roles = {1, 1, 1, 1, 1}, realName = "Crude Enhancement" },
    { name = "item_enhancement_titanic",   tier = 3, roles = {1, 1, 1, 1, 1}, realName = "Titanic Enhancement" },

    -- Tier 4 enhancements
    { name = "item_enhancement_timeless",    tier = 4, roles = {1, 1, 1, 1, 1}, realName = "Timeless Enhancement" },
    { name = "item_enhancement_evolved",     tier = 4, roles = {1, 1, 1, 1, 1}, realName = "Evolved Enhancement" },
    { name = "item_enhancement_audacious",   tier = 4, roles = {1, 1, 1, 1, 1}, realName = "Audacious Enhancement" },
    { name = "item_enhancement_feverish",    tier = 4, roles = {1, 1, 1, 1, 1}, realName = "Feverish Enhancement" },
    { name = "item_enhancement_fleetfooted", tier = 4, roles = {1, 1, 1, 1, 1}, realName = "Fleetfooted Enhancement" },
    { name = "item_enhancement_hulking",     tier = 4, roles = {1, 1, 1, 1, 1}, realName = "Hulking Enhancement" },
    { name = "item_enhancement_manic",       tier = 4, roles = {1, 1, 1, 1, 1}, realName = "Manic Enhancement" },
    { name = "item_enhancement_vampiric",    tier = 4, roles = {1, 1, 1, 1, 1}, realName = "Vampiric Enhancement" },
}

function NeutralItems:GetRandomEnhanByTier(tier)
    local filtered = {}
    for _, enh in ipairs(enhancements) do
        if enh.tier == tier then
            table.insert(filtered, enh)
        end
    end

    if #filtered == 0 then
        return nil  -- No enhancement found for this tier
    end

    -- Return a random enhancement from the filtered list.
    return filtered[math.random(#filtered)]
end

-- Returns a random item name from a tier list, or nil if the list is empty.
local function RandomFromTier(tierList)
    if tierList == nil or #tierList == 0 then
        return nil
    end
    return tierList[RandomInt(1, #tierList)]
end

-- Tier unlock times in minutes (7.42: 0/15/30/50).
-- Turbo keeps the previous proportional style: before 7.42 every turbo time was exactly half of
-- the normal time (8.5/13.5/18.5/30 vs 17/27/37/60), so turbo uses half of the new times.
local TierTimings = {
    { list = Tier1NeutralItems, normal = 0,  turbo = 0    },
    { list = Tier2NeutralItems, normal = 15, turbo = 7.5  },
    { list = Tier3NeutralItems, normal = 30, turbo = 15   },
    { list = Tier4NeutralItems, normal = 50, turbo = 25   },
}

-- Just give out random for now.
-- Will work out a decent algorithm later to better assign suitable items.
function NeutralItems.GiveNeutralItems(TeamRadiant, TeamDire)
    local isTurboMode = Helper.IsTurboMode()
    local tierDone = { isTierOneDone, isTierTwoDone, isTierThreeDone, isTierFourDone }

    for nTier, info in ipairs(TierTimings) do
        local unlockMinutes = isTurboMode and info.turbo or info.normal
        if not tierDone[nTier]
        and Helper.DotaTime() >= unlockMinutes * 60
        then
            GameRules:SendCustomMessage('Bots receiving Tier '..nTier..' Neutral Items...', 0, 0)

            -- Replace the current neutral once the previous tier has been handed out
            -- (same as the old per-tier blocks, which passed the previous tier's flag).
            local isPrevTierDone = nTier == 1 and isTierOneDone or tierDone[nTier - 1]

            for _, h in pairs(TeamRadiant) do
                NeutralItems.GiveItem(RandomFromTier(info.list), h, isPrevTierDone, nTier)
            end

            for _, h in pairs(TeamDire) do
                NeutralItems.GiveItem(RandomFromTier(info.list), h, isPrevTierDone, nTier)
            end

            tierDone[nTier] = true
        end
    end

    isTierOneDone   = tierDone[1]
    isTierTwoDone   = tierDone[2]
    isTierThreeDone = tierDone[3]
    isTierFourDone  = tierDone[4]
end

function NeutralItems.GiveItem(itemName, hero, isTierDone, nTier)
    if itemName == nil or hero == nil then return end
    NeutralItems:RemoveEnhan(hero)
    if hero:HasRoomForItem(itemName, true, true)
    then
        local item = CreateItem(itemName, hero, hero)
        -- An item Valve removed returns nil here; skip it instead of erroring.
        if item == nil then return end
        item:SetPurchaseTime(0)

        if NeutralItems.HasNeutralItem(hero)
        and isTierDone
        then
            hero:RemoveItem(hero:GetItemInSlot(DOTA_ITEM_NEUTRAL_SLOT))
            NeutralItems:RemoveEnhan(hero)
            hero:AddItem(item)
        else
            hero:AddItem(item)
        end
        local enhancement = NeutralItems:GetRandomEnhanByTier(nTier)
        if enhancement then
            local enha = CreateItem(enhancement.name, hero, hero)
            if enha ~= nil then
                enha:SetPurchaseTime(0)
                hero:AddItem(enha)
            end
        end
    end
end

function NeutralItems:RemoveEnhan(unit)
	for idx = 1, 20 do
		local currentItem = unit:GetItemInSlot(idx)
		if currentItem ~= nil then
			if string.find(currentItem:GetName(), "item_enhancement") then
				unit:RemoveItem(currentItem)
				-- return
			end
		end
	end
end

function NeutralItems.HasNeutralItem(hero)
    if not hero then
        return false
    end

    local item = hero:GetItemInSlot(DOTA_ITEM_NEUTRAL_SLOT)
    if item then
        return true
    end

    return false
end

return NeutralItems
