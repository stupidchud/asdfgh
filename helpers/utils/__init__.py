from typing import Optional

async def symboltocurrency(symbol: str) -> Optional[str]:
    symbol = symbol.lower()

    map = {
        "usd": "$",
        "eur": "€",
        "gbp": "£",
        "jpy": "¥",
        "aud": "A$",
        # lazy add more as needed
    }

    return map.get(symbol.lower())