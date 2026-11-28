	-- Default neutral items table, returns the table, so use
	-- local <x> = require "SettingsNeutralItemTable" to include in another file.

local neutral_items =
{
    -- 7.42: 4 tiers (T1 0:00, T2 15:00, T3 30:00, T4 50:00), 12 items per tier.
    -- Pools verified against Valve's itemlist `neutral_item_tier` and the 7.42 patch notes.
    -- Older source: https://github.com/dotabuff/d2vpkr/blob/master/dota/scripts/npc/neutral_items.txt

	-- Just going to comment out items we don"t want entirely rather than force the code to do a rollup on the roles count
	-- roles{} arrays are the desire weights for roles {1,2,3,4,5}

	-- tier 1
	-- {name="item_arcane_ring",			tier=1,		ranged=1,		melee=1,		roles={1,1,1,2,2},		realName="Arcane Ring"},
	-- {name="item_broom_handle",			tier=1,		ranged=0,		melee=3,		roles={2,2,1,0,0},		realName="Broom Handle"},
	-- {name="item_duelist_gloves",		tier=1,		ranged=0,		melee=1,		roles={1,1,1,1,1},		realName="Duelist Gloves"},  -- cycled out in 7.42
	-- {name="item_faded_broach",			tier=1,		ranged=1,		melee=1,		roles={5,5,5,5,5},		realName="Faded Broach"},
	-- {name="item_mysterious_hat",		tier=1,		ranged=1,		melee=1,		roles={1,4,1,1,1},		realName="Fairy's Trinket"},
	-- {name="item_lance_of_pursuit",		tier=1,		ranged=1,		melee=2,		roles={2,2,1,1,1},		realName="Lance of Pursuit"},
	-- {name="item_occult_bracelet",		tier=1,		ranged=1,		melee=1,		roles={1,1,3,2,2},		realName="Occult Bracelet"},  -- cycled out in 7.42
	-- {name="item_unstable_wand",			tier=1,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Pig Pole"},
	-- {name="item_rippers_lash",			tier=1,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Ripper's Lash"},
	-- {name="item_royal_jelly",			tier=1,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Royal Jelly"},
	-- {name="item_safety_bubble",			tier=1,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Safety Bubble"},  -- tier 2 in 7.42
	-- {name="item_spark_of_courage",		tier=1,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Spark of Courage"},
	-- {name="item_keen_optic",				tier=1,		ranged=1,		melee=1,		roles={1,1,1,2,2},		realName="Keen Optic"},
	-- {name="item_ironwood_tree",			tier=1,		ranged=1,		melee=1,		roles={2,2,2,1,1},		realName="Ironwood Tree"},
	-- {name="item_mango_tree",				tier=1,		ranged=1,		melee=1,		roles={0,0,0,0,0},		realName="Mango Tree"},
	-- {name="item_ocean_heart",				tier=1,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Ocean Heart"},
	-- {name="item_trusty_shovel",			tier=1,		ranged=1,		melee=1,		roles={0,0,0,0,0},		realName="Trusty Shovel"},
	-- {name="item_orb_of_destruction",	tier=1,		ranged=1,		melee=1,		roles={4,1,1,0,0},		realName="Orb of Destruction"},
	-- {name="item_sisters_shroud",			tier=1,		ranged=1,		melee=1,		roles={1,1,1,5,5},		realName="Sister's Shroud"},
	-- {name="item_dagger_of_ristul",		tier=1,		ranged=1,		melee=1,		roles={3,3,1,0,0},		realName="Dagger of Ristul"},  -- cycled out in 7.42
	{name="item_chipped_vest",			tier=1,		ranged=0,		melee=1,		roles={2,2,4,2,2},		realName="Chipped Vest"},
	{name="item_ash_legion_shield",		tier=1,		ranged=0,		melee=1,		roles={1,1,2,3,3},		realName="Ash Legion Shield"},
	{name="item_possessed_mask",			tier=1,		ranged=1,		melee=1,		roles={3,3,2,1,1},		realName="Possessed Mask"},
	{name="item_dormant_curio",			tier=1,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Dormant Curio"},
	{name="item_red_ledger",				tier=1,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Red Ledger"},  -- new in 7.42
	{name="item_weighted_dice",			tier=1,		ranged=1,		melee=1,		roles={3,3,1,1,1},		realName="Weighted Dice"},
	{name="item_polliwog_charm",			tier=1,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Pollywog Charm"},
	{name="item_seeds_of_serenity",		tier=1,		ranged=1,		melee=1,		roles={0,0,0,1,1},		realName="Seeds of Serenity"},  -- moved from tier 2 in 7.42
	{name="item_foragers_kit",			tier=1,		ranged=1,		melee=1,		roles={1,1,1,3,3},		realName="Forager's Kit"},
	{name="item_kobold_cup",				tier=1,		ranged=1,		melee=1,		roles={1,1,1,3,3},		realName="Kobold Cup"},
	{name="item_stonefeather_satchel",	tier=1,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Stonefeather Satchel"},
	{name="item_pogo_stick",				tier=1,		ranged=1,		melee=1,		roles={3,3,3,3,3},		realName="Tumbler's Toy"},  -- moved from tier 2 in 7.42

	-- tier 2
	-- {name="item_bullwhip",				tier=2,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Bullwhip"},
	-- {name="item_dragon_scale",			tier=2,		ranged=1,		melee=1,		roles={1,1,3,1,1},		realName="Dragon Scale"},
	-- {name="item_eye_of_the_vizier",		tier=2,		ranged=1,		melee=1,		roles={1,1,1,4,4},		realName="Eye of the Vizier"},
	-- {name="item_gossamer_cape",			tier=2,		ranged=1,		melee=1,		roles={1,1,1,3,3},		realName="Gossamer Cape"},
	-- {name="item_grove_bow",				tier=2,		ranged=5,		melee=0,		roles={2,2,1,-5,-5},	realName="Grove Bow"},
	-- {name="item_light_collector", 		tier=2, 	ranged=1, 		melee=1,		roles={1,1,1,3,3}, 		realName = 'Light Collector'},
	-- {name="item_pupils_gift",			tier=2,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Pupil's Gift"},
	-- {name="item_specialists_array",		tier=2,		ranged=2,		melee=0,		roles={2,2,1,1,1},		realName="Specialist's Array"},
	-- {name="item_vambrace",				tier=2,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Vambrace"},
	-- {name="item_iron_talon",			tier=2,		ranged=1,		melee=1,		roles={1,1,1,0,0},		realName="Iron Talon"},
	-- {name="item_vampire_fangs",			tier=2,		ranged=1,		melee=1,		roles={2,2,2,0,0},		realName="Vampire Fangs"},
	-- {name="item_misericorde",				tier=2,		ranged=1,		melee=1,		roles={4,2,1,0,0},		realName="Brigand's Blade"},
	--{name="item_clumsy_net",				tier=2,		ranged=1,		melee=1,		roles={1,1,2,3,3},		realName="Clumsy Net"},
	--{name="item_paintball",				tier=2,		ranged=1,		melee=1,		roles={2,2,1,1,1},		realName="Fae Grenade"},
	--{name="item_nether_shawl",			tier=2,		ranged=1,		melee=1,		roles={0,0,0,0,0},		realName="Nether Shawl"},
	--{name="item_philosophers_stone",		tier=2,		ranged=1,		melee=1,		roles={0,0,0,0,0},		realName="Philosopher's Stone"},
	--{name="item_quicksilver_amulet",		tier=2,		ranged=1,		melee=1,		roles={2,2,1,1,1},		realName="Quicksilver Amulet"},
	--{name="item_ring_of_aquila",			tier=2,		ranged=1,		melee=1,		roles={3,2,1,0,0},		realName="Ring of Aquila"},
	-- {name="item_searing_signet",			tier=2,		ranged=1,		melee=1,		roles={2,2,1,2,2},		realName="Searing Signet"},  -- cycled out in 7.42
	-- {name="item_essence_ring",			tier=2,		ranged=1,		melee=1,		roles={3,3,3,2,2},		realName="Essence Ring"},  -- cycled out in 7.42
	-- {name="item_poor_mans_shield",		tier=2,		ranged=1,		melee=3,		roles={2,2,3,1,1},		realName="Poor Man's Shield"},  -- cycled out in 7.42
	-- {name="item_medallion_of_courage",	tier=2,		ranged=1,		melee=1,		roles={1,1,1,3,3},		realName="Medallion of Courage"},  -- cycled out in 7.42
	-- {name="item_pogo_stick",				tier=2,		ranged=1,		melee=1,		roles={3,3,3,3,3},		realName="Tumbler's Toy"},  -- moved to tier 1 in 7.42
	-- {name="item_seeds_of_serenity",		tier=2,		ranged=1,		melee=1,		roles={0,0,0,1,1},		realName="Seeds of Serenity"},  -- moved to tier 1 in 7.42
	{name="item_psychic_headband",		tier=2,		ranged=3,		melee=1,		roles={1,1,1,6,6},		realName="Psychic Headband"},  -- moved from tier 3 in 7.42
	{name="item_safety_bubble",			tier=2,		ranged=1,		melee=1,		roles={1,2,1,3,3},		realName="Safety Bubble"},  -- new in 7.42
	{name="item_metamorphic_mandible",	tier=2,		ranged=1,		melee=1,		roles={1,1,1,3,3},		realName="Metamorphic Mandible"},  -- moved from tier 4 in 7.42
	{name="item_jidi_pollen_bag",		tier=2,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Jidi Pollen Bag"},  -- moved from tier 3 in 7.42
	{name="item_brick",					tier=2,		ranged=1,		melee=1,		roles={1,1,2,2,2},		realName="Brick"},  -- new in 7.42 (active)
	{name="item_crippling_crossbow",	tier=2,		ranged=1,		melee=1,		roles={1,1,3,1,1},		realName="Crippling Crossbow"},
	{name="item_imp_claw",				tier=2,		ranged=1,		melee=1,		roles={4,3,2,0,0},		realName="Imp Claw"},  -- new in 7.42
	{name="item_gunpowder_gauntlets",	tier=2,		ranged=1,		melee=1,		roles={1,1,4,1,1},		realName="Gunpowder Gauntlets"},  -- moved from tier 3 in 7.42
	{name="item_defiant_shell",			tier=2,		ranged=1,		melee=2,		roles={2,2,6,2,2},		realName="Defiant Shell"},
	{name="item_partisans_brand",		tier=2,		ranged=1,		melee=1,		roles={3,3,1,0,0},		realName="Partisan's Brand"},  -- moved from tier 3 in 7.42
	{name="item_spellslinger",			tier=2,		ranged=1,		melee=1,		roles={1,1,1,3,3},		realName="Spellslinger"},  -- moved from tier 3 in 7.42
	{name="item_mana_draught",			tier=2,		ranged=1,		melee=1,		roles={1,1,1,3,3},		realName="Mana Draught"},

	-- tier 3
	-- {name="item_craggy_coat",			tier=3,		ranged=1,		melee=1,		roles={0,0,4,1,1},		realName="Craggy Coat"},
	-- {name="item_doubloon",				tier=3,		ranged=0,		melee=0,		roles={0,0,0,0,0},		realName="Doubloon"},
	-- {name="item_elven_tunic",			tier=3,		ranged=1,		melee=1,		roles={5,5,5,2,2},		realName="Elven Tunic"},
	-- {name="item_enchanted_quiver",		tier=3,		ranged=4,		melee=0,		roles={1,1,1,1,1},		realName="Enchanted Quiver"},
	-- {name="item_vambrace",				tier=3,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Vambrace"},
	-- {name="item_paladin_sword",			tier=3,		ranged=1,		melee=1,		roles={4,1,1,0,0},		realName="Paladin Sword"},
	-- {name="item_nemesis_curse",			tier=3,		ranged=1,		melee=1,		roles={2,2,0,0,0},		realName="Nemesis Curse"},
	-- {name="item_vindicators_axe",		tier=3,		ranged=1,		melee=1,		roles={1,1,4,1,1},		realName="Vindicator's Axe"},
	--{name="item_black_powder_bag",		tier=3,		ranged=1,		melee=1,		roles={1,1,4,1,1},		realName="Blast Rig"},
	--{name="item_greater_faerie_fire",		tier=3,		ranged=1,		melee=1,		roles={1,1,1,0,0},		realName="Greater Faerie Fire"},
	--{name="item_repair_kit",				tier=3,		ranged=1,		melee=1,		roles={0,0,2,1,1},		realName="Repair Kit"},
	--{name="item_quickening_charm",		tier=3,		ranged=1,		melee=1,		roles={1,1,1,4,4},		realName="Quickening Charm"},
	--{name="item_titan_sliver",			tier=3,		ranged=1,		melee=1,		roles={1,1,4,1,1},		realName="Titan Sliver"},
	-- {name="item_gale_guard",			tier=3,		ranged=1,		melee=1,		roles={1,1,4,1,1},		realName="Gale Guard"},
	-- {name="item_whisper_of_the_dread",	tier=3,		ranged=1,		melee=1,		roles={1,2,1,4,4},		realName="Whisper of the Dread"},  -- removed in 7.41
	-- {name="item_ninja_gear",			tier=3,		ranged=1,		melee=1,		roles={2,1,1,0,0},		realName="Ninja Gear"},
	-- {name="item_cloak_of_flames",		tier=3,		ranged=1,		melee=2,		roles={2,2,6,2,2},		realName="Cloak of Flames"},  -- cycled out in 7.42
	-- {name="item_unrelenting_eye",		tier=3,		ranged=1,		melee=1,		roles={2,2,2,2,2},		realName="Unrelenting Eye"},  -- cycled out in 7.42
	-- {name="item_psychic_headband",		tier=3,		ranged=3,		melee=1,		roles={1,1,1,6,6},		realName="Psychic Headband"},  -- moved to tier 2 in 7.42
	-- {name="item_gunpowder_gauntlets",	tier=3,		ranged=1,		melee=1,		roles={1,1,4,1,1},		realName="Gunpowder Gauntlets"},  -- moved to tier 2 in 7.42
	-- {name="item_jidi_pollen_bag",		tier=3,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Jidi Pollen Bag"},  -- moved to tier 2 in 7.42
	-- {name="item_spellslinger",			tier=3,		ranged=1,		melee=1,		roles={1,1,1,3,3},		realName="Spellslinger"},  -- moved to tier 2 in 7.42
	-- {name="item_partisans_brand",		tier=3,		ranged=1,		melee=1,		roles={3,3,1,0,0},		realName="Partisan's Brand"},  -- moved to tier 2 in 7.42
	{name="item_prophets_pendulum",		tier=3,		ranged=1,		melee=1,		roles={1,1,1,3,3},		realName="Prophet's Pendulum"},  -- moved from tier 4 in 7.42
	{name="item_dandelion_amulet",		tier=3,		ranged=1,		melee=1,		roles={2,2,6,2,2},		realName="Dandelion Amulet"},  -- moved from tier 4 in 7.42
	{name="item_idol_of_screeauk",		tier=3,		ranged=1,		melee=1,		roles={2,2,3,4,4},		realName="Idol of Scree'Auk"},  -- moved from tier 4 in 7.42
	{name="item_balmhook",				tier=3,		ranged=1,		melee=1,		roles={0,1,1,4,4},		realName="Balmhook"},  -- new in 7.42
	{name="item_rattlecage",			tier=3,		ranged=1,		melee=1,		roles={0,0,6,1,1},		realName="Rattlecage"},  -- moved from tier 4 in 7.42
	{name="item_stormcrafter",			tier=3,		ranged=1,		melee=1,		roles={1,1,3,3,3},		realName="Stormcrafter"},
	{name="item_enchanters_bauble",		tier=3,		ranged=1,		melee=1,		roles={1,1,1,3,3},		realName="Enchanter's Bauble"},  -- moved from tier 4 in 7.42
	{name="item_ceremonial_robe",		tier=3,		ranged=1,		melee=1,		roles={1,1,2,5,5},		realName="Ceremonial Robe"},  -- new in 7.42
	{name="item_harmonizer",			tier=3,		ranged=1,		melee=1,		roles={1,1,1,3,3},		realName="Harmonizer"},  -- moved from tier 5 in 7.42
	{name="item_vile_phial",			tier=3,		ranged=1,		melee=1,		roles={3,3,3,1,1},		realName="Vile Phial"},  -- new in 7.42
	{name="item_serrated_shiv",			tier=3,		ranged=1,		melee=1,		roles={1,1,4,1,1},		realName="Serrated Shiv"},
	{name="item_revenants_brooch",		tier=3,		ranged=1,		melee=1,		roles={4,4,2,0,0},		realName="Revenant's Brooch"},  -- new in 7.42

	-- tier 4
	-- {name="item_ancient_guardian",		tier=4,		ranged=1,		melee=1,		roles={3,1,1,0,0},		realName="Ancient Guardian"},
	-- {name="item_ascetic_cap",			tier=4,		ranged=1,		melee=1,		roles={1,1,6,1,1},		realName="Ascetic's Cap"},
	-- {name="item_avianas_feather",		tier=4,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Aviana's Feather"},
	-- {name="item_havoc_hammer",			tier=4,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Havoc Hammer"},
	-- {name="item_martyrs_plate",			tier=4,		ranged=1,		melee=1,		roles={1,1,5,0,0},		realName="Martyr's Plate"},
	-- {name="item_ogre_seal_totem",		tier=4,		ranged=1,		melee=1,		roles={1,1,3,1,1},		realName="Ogre Seal Totem"},
	-- {name="item_magnifying_monocle",		tier=4,		ranged=1,		melee=1,		roles={2,2,1,3,3},		realName="Magnifying Monocle"},
	-- {name="item_spy_gadget",			tier=4,		ranged=4,		melee=0,		roles={0,0,0,3,3},		realName="Telescope"},
	-- {name="item_timeless_relic",		tier=4,		ranged=1,		melee=1,		roles={1,4,1,3,3},		realName="Timeless Relic"},
	-- {name="item_trickster_cloak",		tier=4,		ranged=1,		melee=1,		roles={1,1,1,4,4},		realName="Trickster Cloak"},
	--{name="item_illusionsts_cape",		tier=4,		ranged=1,		melee=1,		roles={1,1,1,0,0},		realName="Illusionist's Cape"},
	--{name="item_the_leveller",			tier=4,		ranged=1,		melee=1,		roles={5,1,0,0,0},		realName="The Leveller"},
	--{name="item_penta_edged_sword",		tier=4,		ranged=1,		melee=5,		roles={5,3,1,1,1},		realName="Penta-Edged Sword"},
	--{name="item_princes_knife",			tier=4,		ranged=4,		melee=0,		roles={2,2,1,1,1},		realName="Prince's Knife"},
	--{name="item_spell_prism",				tier=4,		ranged=1,		melee=1,		roles={1,2,1,4,5},		realName="Spell Prism"},
	--{name="item_witless_shako",			tier=4,		ranged=1,		melee=1,		roles={1,1,5,2,2},		realName="Witless Shako"},
	-- {name="item_pyrrhic_cloak",		tier=4,		ranged=1,		melee=1,		roles={1,1,4,4,4},		realName="Pyrrhic Cloak"},
	-- {name="item_outworld_staff",		tier=4,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Outworld Staff"},
	-- {name="item_giant_maul",			tier=4,		ranged=1,		melee=1,		roles={5,5,1,0,0},		realName="Giant's Maul"},  -- cycled out in 7.42
	-- {name="item_flayers_bota",			tier=4,		ranged=1,		melee=1,		roles={5,5,1,0,0},		realName="Flayer's Bota"},  -- cycled out in 7.42
	-- {name="item_rattlecage",			tier=4,		ranged=1,		melee=1,		roles={0,0,6,1,1},		realName="Rattlecage"},  -- moved to tier 3 in 7.42
	-- {name="item_idol_of_screeauk",		tier=4,		ranged=1,		melee=1,		roles={2,2,3,4,4},		realName="Idol of Scree'Auk"},  -- moved to tier 3 in 7.42
	-- {name="item_metamorphic_mandible",	tier=4,		ranged=1,		melee=1,		roles={1,1,1,3,3},		realName="Metamorphic Mandible"},  -- moved to tier 2 in 7.42
	-- {name="item_dandelion_amulet",		tier=4,		ranged=1,		melee=1,		roles={2,2,6,2,2},		realName="Dandelion Amulet"},  -- moved to tier 3 in 7.42
	-- {name="item_enchanters_bauble",		tier=4,		ranged=1,		melee=1,		roles={1,1,1,3,3},		realName="Enchanter's Bauble"},  -- moved to tier 3 in 7.42
	-- {name="item_prophets_pendulum",		tier=4,		ranged=1,		melee=1,		roles={1,1,1,3,3},		realName="Prophet's Pendulum"},  -- moved to tier 3 in 7.42
	-- old tier 5 (removed in 7.42; its remaining items moved to tier 4)
	-- {name="item_apex",					tier=5,		ranged=1,		melee=1,		roles={1,1,1,0,0},		realName="Apex"},
	-- {name="item_force_field",			tier=5,		ranged=1,		melee=1,		roles={2,5,1,7,7},		realName="Arcanist's Armor"},
	-- {name="item_book_of_shadows",		tier=5,		ranged=1,		melee=1,		roles={1,1,1,6,6},		realName="Book of Shadows"},
	-- {name="item_force_boots",			tier=5,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Force Boots"},
	-- {name="item_panic_button",			tier=5,		ranged=1,		melee=1,		roles={1,1,3,1,1},		realName="Magic Lamp"},
	-- {name="item_mirror_shield",			tier=5,		ranged=1,		melee=1,		roles={2,2,4,0,0},		realName="Mirror Shield"},
	-- {name="item_pirate_hat",			tier=5,		ranged=1,		melee=1,		roles={4,3,1,0,0},		realName="Pirate Hat"},
	-- {name="item_seer_stone",			tier=5,		ranged=1,		melee=1,		roles={1,1,2,5,5},		realName="Seer Stone"},
	-- {name="item_unwavering_condition",	tier=5,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Unwavering Condition"},
	--{name="item_ballista",				tier=5,		ranged=5,		melee=0,		roles={1,1,1,0,0},		realName="Ballista"},
	--{name="item_ex_machina",				tier=5,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Ex Machina"},
	--{name="item_trident",					tier=5,		ranged=1,		melee=1,		roles={5,5,3,3,3},		realName="Trident"},
	--{name="item_woodland_striders",		tier=5,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Woodland Striders"},
	-- {name="item_helm_of_the_undying",	tier=5,		ranged=1,		melee=1,		roles={5,5,5,5,5},		realName="Helm of the Undying"},
	-- {name="item_desolator_2",			tier=5,		ranged=1,		melee=1,		roles={5,1,0,0,0},		realName="Stygian Desolator"},  -- cycled out in 7.42
	-- {name="item_spider_legs",			tier=5,		ranged=1,		melee=1,		roles={2,2,2,2,2},		realName="Spider Legs"},  -- cycled out in 7.42
	{name="item_fallen_sky",			tier=4,		ranged=1,		melee=1,		roles={1,1,5,0,0},		realName="Fallen Sky"},  -- moved from tier 5 in 7.42
	{name="item_flicker",				tier=4,		ranged=1,		melee=1,		roles={1,2,1,2,2},		realName="Flicker"},  -- new in 7.42
	{name="item_minotaur_horn",			tier=4,		ranged=1,		melee=1,		roles={1,1,1,1,1},		realName="Minotaur Horn"},  -- moved from tier 5 in 7.42
	{name="item_mind_breaker",			tier=4,		ranged=1,		melee=1,		roles={4,3,2,0,0},		realName="Mind Breaker"},  -- new in 7.42
	{name="item_divine_regalia",		tier=4,		ranged=1,		melee=1,		roles={4,4,1,1,1},		realName="Divine Regalia"},  -- moved from tier 5 in 7.42
	{name="item_heavy_blade",			tier=4,		ranged=1,		melee=1,		roles={3,6,1,1,1},		realName="Witchbane"},  -- moved from tier 5 in 7.42
	{name="item_helm_of_the_hivemind",	tier=4,		ranged=1,		melee=1,		roles={1,2,1,3,3},		realName="Helm of the Hivemind"},  -- new in 7.42
	{name="item_dezun_bloodrite",		tier=4,		ranged=1,		melee=1,		roles={1,2,3,4,4},		realName="Dezun Bloodrite"},  -- moved from tier 5 in 7.42
	{name="item_conjurers_catalyst",	tier=4,		ranged=1,		melee=1,		roles={1,1,1,3,3},		realName="Conjurer's Catalyst"},
	{name="item_giants_ring",			tier=4,		ranged=1,		melee=1,		roles={3,3,6,1,1},		realName="Giant's Ring"},  -- new in 7.42
	{name="item_demonicon",				tier=4,		ranged=1,		melee=1,		roles={1,1,1,5,6},		realName="Book of the Dead"},  -- moved from tier 5 in 7.42
	{name="item_riftshadow_prism",		tier=4,		ranged=1,		melee=2,		roles={4,4,1,1,1},		realName="Riftshadow Prism"},  -- moved from tier 5 in 7.42
}

local enhancements = {
    -- 7.42 enchantment tiers (from the 7.42 patch notes):
    --   Alert, Brawny, Mystical, Quickened, Tough: 1-3.  Vital: 1-2.
    --   Crude, Keen-eyed, Nimble, Titanic: 2-3.  Greedy: 3.
    --   Evolved, Timeless, Audacious, Feverish, Fleetfooted, Hulking, Manic, Vampiric: 4.
    -- Vast, Wise and Boundless are not in the 7.42 notes (probably cycled out); none were active here.

    -- Tier 1
    { name = "item_enhancement_quickened", tier = 1, roles = {1, 1, 1, 2, 1}, realName = "Quickened Enhancement" },
    { name = "item_enhancement_vital",     tier = 1, roles = {1, 1, 1, 1, 1}, realName = "Vital Enhancement" },
    { name = "item_enhancement_brawny",    tier = 1, roles = {1, 1, 3, 2, 2}, realName = "Brawny Enhancement" },
    { name = "item_enhancement_tough",     tier = 1, roles = {1, 1, 2, 2, 1}, realName = "Tough Enhancement" },
    { name = "item_enhancement_alert",     tier = 1, roles = {1, 2, 1, 1, 1}, realName = "Alert Enhancement" },
    { name = "item_enhancement_mystical",  tier = 1, roles = {1, 1, 1, 1, 1}, realName = "Mystical Enhancement" },

    -- Tier 2
    { name = "item_enhancement_quickened", tier = 2, roles = {1, 1, 1, 2, 1}, realName = "Quickened Enhancement" },
    { name = "item_enhancement_vital",     tier = 2, roles = {1, 1, 1, 1, 1}, realName = "Vital Enhancement" },
    { name = "item_enhancement_brawny",    tier = 2, roles = {1, 1, 3, 2, 2}, realName = "Brawny Enhancement" },
    { name = "item_enhancement_tough",     tier = 2, roles = {1, 1, 2, 2, 1}, realName = "Tough Enhancement" },
    { name = "item_enhancement_crude",     tier = 2, roles = {2, 1, 2, 1, 1}, realName = "Crude Enhancement" },
    { name = "item_enhancement_alert",     tier = 2, roles = {1, 2, 1, 1, 1}, realName = "Alert Enhancement" },
    { name = "item_enhancement_nimble",    tier = 2, roles = {1, 1, 1, 1, 1}, realName = "Nimble Enhancement" },
    { name = "item_enhancement_mystical",  tier = 2, roles = {1, 1, 1, 1, 1}, realName = "Mystical Enhancement" },
    { name = "item_enhancement_keen_eyed", tier = 2, roles = {1, 1, 1, 1, 2}, realName = "Keen Eyed Enhancement" },
    { name = "item_enhancement_titanic",   tier = 2, roles = {1, 1, 1, 1, 1}, realName = "Titanic Enhancement" },
    -- { name = "item_enhancement_greedy",    tier = 2, roles = {1, 1, 1, 2, 2}, realName = "Greedy Enhancement" },  -- tier 3 only in 7.42

    -- Tier 3
    { name = "item_enhancement_quickened", tier = 3, roles = {1, 1, 1, 2, 1}, realName = "Quickened Enhancement" },
    { name = "item_enhancement_greedy",    tier = 3, roles = {1, 1, 1, 2, 2}, realName = "Greedy Enhancement" },
    { name = "item_enhancement_brawny",    tier = 3, roles = {1, 1, 3, 2, 2}, realName = "Brawny Enhancement" },
    { name = "item_enhancement_tough",     tier = 3, roles = {1, 1, 2, 2, 1}, realName = "Tough Enhancement" },
    { name = "item_enhancement_crude",     tier = 3, roles = {2, 1, 2, 1, 1}, realName = "Crude Enhancement" },
    { name = "item_enhancement_alert",     tier = 3, roles = {1, 2, 1, 1, 1}, realName = "Alert Enhancement" },
    { name = "item_enhancement_nimble",    tier = 3, roles = {1, 1, 1, 1, 1}, realName = "Nimble Enhancement" },
    { name = "item_enhancement_mystical",  tier = 3, roles = {1, 1, 1, 1, 1}, realName = "Mystical Enhancement" },
    { name = "item_enhancement_keen_eyed", tier = 3, roles = {1, 1, 1, 1, 2}, realName = "Keen Eyed Enhancement" },
    { name = "item_enhancement_titanic",   tier = 3, roles = {1, 1, 1, 1, 1}, realName = "Titanic Enhancement" },

    -- Tier 4 (7.42: the old tier-5 enchantments moved here; the 1-4 / 2-4 ones now stop at tier 3)
    { name = "item_enhancement_timeless",    tier = 4, roles = {1, 1, 1, 1, 1}, realName = "Timeless Enhancement" },
    { name = "item_enhancement_evolved",     tier = 4, roles = {1, 1, 1, 1, 1}, realName = "Evolved Enhancement" },
    { name = "item_enhancement_fleetfooted", tier = 4, roles = {1, 1, 1, 1, 1}, realName = "Fleetfooted Enhancement" },
    { name = "item_enhancement_vampiric",    tier = 4, roles = {1, 1, 1, 1, 1}, realName = "Vampiric Enhancement" },
    { name = "item_enhancement_hulking",     tier = 4, roles = {1, 1, 1, 1, 1}, realName = "Hulking Enhancement" },
    { name = "item_enhancement_audacious",   tier = 4, roles = {1, 2, 1, 1, 1}, realName = "Audacious Enhancement" },
    { name = "item_enhancement_feverish",    tier = 4, roles = {1, 1, 1, 1, 1}, realName = "Feverish Enhancement" },
    { name = "item_enhancement_manic",       tier = 4, roles = {1, 1, 1, 1, 1}, realName = "Manic Enhancement" },
}


return {
	items = neutral_items,
	enhancements = enhancements
}
