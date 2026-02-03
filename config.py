from typing import List

class Settings:
    owner_id: int = 123456789012345678
    developer_ids: set = {123456789012345678, 123}
    mobile: bool = True
    production: bool = False
    default_prefix = ";"
    db_path = "data/sqlite/main.db"
    
    features: List[str] = [
        "moderation.events",
        "moderation.punishment",
        "miscellaneous.information",
        "miscellaneous.prefix",
        "miscellaneous.help",
        "crypto.price",
        "miscellaneous.server",
        "protection.gate",
        # "developer",
        # "socials",
        # "minigames",
        # "music"
    ]
    
    domain = "asdf.gh"
    help = f"https://{domain}/help"

class Emoji:
    class Context:
        success = ":ok_hand:"
        error = ":thumbsdown:"
        warning = ":warning:"

    class Moderation:
        envelope = ":incoming_envelope:"

    class Badges:
        emojis = {
            "staff": "<:staff:1464951595832971376>",
            "partner": "<:partner:1464951598030782609>",
            "hypesquad": "<:hypesquad:1464951608415879354>",
            "hypesquad_bravery": "<:hypesquad_bravery:1464951604707983508>",
            "hypesquad_brilliance": "<:hypesquad_brilliance:1464951602564825201>",
            "hypesquad_balance": "<:hypesquad_balance:1464951606482305128>",
            "bug_hunter": "<:bug_hunter:1464951616787452091>",
            "bug_hunter_level_2": "<:bug_hunter_level_2:1464951614778376315>",
            "early_supporter": "<:early_supporter:1464951611540639825>",
            "verified_bot_developer": "<:verified_bot_developer:1464951593941078149>",
            "discord_certified_moderator": "<:discord_certified_moderator:1464951613121626172>",
            "active_developer": "<:active_developer:1464951620625240278>",
            "nitro": "<:nitro:1464951600983441538>",
        }

    class Crypto:
        green = "<:up:1467605261245091873>"
        red = "<:down:1467605258967711942>"

    spotify = ""

class Color:
    default = 0x2f3136
