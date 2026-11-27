# High Five reply

When a human player uses High Five, one bot answers in all-chat with `Good girl!`.

- **Code:** `bots/FunLib/high_five_chat.lua`, called from `AbilityUsageThink` in `bots/ability_item_usage_generic.lua` before the reaction-delay gate.
- **Detection:** the caster carries `modifier_plus_high_five_requested` during the 10s request window of `plus_high_five` (d2vpkr; the modifier name also appears in the game's `server.dll`). A reply is sent when the modifier first appears on a human player's hero.
- **Ignored:** bots, because FretBots puts the same modifier on a bot as a kill taunt, and illusions.
- **Speaker:** the lowest-ID living bot on the high-fiver's team. If that team has no living bot, the lowest-ID living bot on the other team answers, but only if it can see the high-fiver. Both teams' scripts make the same choice, so the line is sent once.
- **No repeats:** one reply per request, including when the speaker dies and another bot takes over, or a bot respawns mid-request.
- **Settings:** `X.Message` and `X.Enabled` at the top of the file.

## How to check it in a game

1. Use High Five (it needs Dota Plus or a High Five consumable).
2. One bot on your team should say `Good girl!` in all-chat, once.
3. Do it again after the 60s cooldown: one more reply.
4. Not yet verified in a game: that the bot API sees `modifier_plus_high_five_requested` on a human hero. If nothing is said, that is the first thing to check.
