from typing import Optional, List, Dict, Any, Union

import aiohttp

from .http import HTTPClient
from .models import (
    PriceData,
    MultiPriceFullData,
    HistoricalResponse,
    CoinListResponse,
    TopVolumeResponse,
    ExchangeListResponse,
)


class CryptoCompare:
    """
    CryptoCompare API client wrapper
    
    Provides methods for accessing CryptoCompare Min API endpoints including
    price data, historical data, coin information, and more.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None
    ):
        """
        Initialize CryptoCompare API client
        
        Args:
            api_key: Optional API key for authenticated requests
            session: Optional aiohttp ClientSession to use
        """
        self.http = HTTPClient(api_key=api_key, session=session)
        
    async def close(self) -> None:
        """Close the HTTP client session"""
        await self.http.close()
        
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    # Price endpoints
    
    async def get_price(
        self,
        fsym: str,
        tsyms: Union[str, List[str]],
        exchange: Optional[str] = None,
        try_conversion: bool = True,
    ) -> Union[float, PriceData]:
        """
        Get current price of a cryptocurrency in multiple currencies
        
        Args:
            fsym: From symbol (e.g., 'BTC')
            tsyms: To symbols (e.g., 'USD' or ['USD', 'EUR'])
            exchange: Optional exchange name (default: CCCAGG)
            try_conversion: Try conversion if direct trading pair unavailable
            
        Returns:
            Float if single currency requested, PriceData object if multiple
            
        Example:
            >>> client = CryptoCompare()
            >>> price = await client.get_price('BTC', 'USD')
            >>> print(price)  # 50000.0
            >>> prices = await client.get_price('BTC', ['USD', 'EUR'])
            >>> print(prices['USD'])  # 50000.0
        """
        single_currency = isinstance(tsyms, str)
        
        if isinstance(tsyms, list):
            tsyms = ",".join(tsyms)
            
        params = {
            "fsym": fsym.upper(),
            "tsyms": tsyms.upper(),
            "tryConversion": str(try_conversion).lower(),
        }
        
        if exchange:
            params["e"] = exchange
            
        response = await self.http.get("/data/price", params=params)
        price_data = PriceData(prices=response)
        
        # Return float directly if single currency requested
        if single_currency and len(price_data.prices) == 1:
            return list(price_data.prices.values())[0]
        
        return price_data
    
    async def get_price_multi(
        self,
        fsyms: Union[str, List[str]],
        tsyms: Union[str, List[str]],
        exchange: Optional[str] = None,
        try_conversion: bool = True,
    ) -> Dict[str, Dict[str, float]]:
        """
        Get current prices for multiple cryptocurrencies in multiple currencies
        
        Args:
            fsyms: From symbols (e.g., ['BTC', 'ETH'])
            tsyms: To symbols (e.g., ['USD', 'EUR'])
            exchange: Optional exchange name (default: CCCAGG)
            try_conversion: Try conversion if direct trading pair unavailable
            
        Returns:
            Dictionary mapping from_symbol -> to_symbol -> price
            
        Example:
            >>> prices = await client.get_price_multi(['BTC', 'ETH'], ['USD', 'EUR'])
            >>> print(prices['BTC']['USD'])  # 50000.0
        """
        if isinstance(fsyms, list):
            fsyms = ",".join(fsyms)
        if isinstance(tsyms, list):
            tsyms = ",".join(tsyms)
            
        params = {
            "fsyms": fsyms.upper(),
            "tsyms": tsyms.upper(),
            "tryConversion": str(try_conversion).lower(),
        }
        
        if exchange:
            params["e"] = exchange
            
        return await self.http.get("/data/pricemulti", params=params)
    
    async def get_price_multi_full(
        self,
        fsyms: Union[str, List[str]],
        tsyms: Union[str, List[str]],
        exchange: Optional[str] = None,
        try_conversion: bool = True,
    ) -> MultiPriceFullData:
        """
        Get full price data for multiple cryptocurrencies including OHLCV and more
        
        Args:
            fsyms: From symbols (e.g., ['BTC', 'ETH'])
            tsyms: To symbols (e.g., ['USD', 'EUR'])
            exchange: Optional exchange name (default: CCCAGG)
            try_conversion: Try conversion if direct trading pair unavailable
            
        Returns:
            MultiPriceFullData object with detailed price information
            
        Example:
            >>> data = await client.get_price_multi_full(['BTC'], ['USD'])
            >>> btc_usd = data.raw['BTC']['USD']
            >>> print(btc_usd.price, btc_usd.volume_24h)
        """
        if isinstance(fsyms, list):
            fsyms = ",".join(fsyms)
        if isinstance(tsyms, list):
            tsyms = ",".join(tsyms)
            
        params = {
            "fsyms": fsyms.upper(),
            "tsyms": tsyms.upper(),
            "tryConversion": str(try_conversion).lower(),
        }
        
        if exchange:
            params["e"] = exchange
            
        response = await self.http.get("/data/pricemultifull", params=params)
        return MultiPriceFullData(**response)
    
    # Historical data endpoints
    
    async def get_historical_day(
        self,
        fsym: str,
        tsym: str,
        limit: int = 30,
        aggregate: int = 1,
        exchange: Optional[str] = None,
        to_ts: Optional[int] = None,
    ) -> HistoricalResponse:
        """
        Get daily historical OHLCV data
        
        Args:
            fsym: From symbol (e.g., 'BTC')
            tsym: To symbol (e.g., 'USD')
            limit: Number of data points (max 2000, default 30)
            aggregate: Data points to aggregate (default 1)
            exchange: Optional exchange name (default: CCCAGG)
            to_ts: Optional timestamp to get data up to
            
        Returns:
            HistoricalResponse with OHLCV data
            
        Example:
            >>> hist = await client.get_historical_day('BTC', 'USD', limit=7)
            >>> for point in hist.data:
            ...     print(point.time, point.close)
        """
        params = {
            "fsym": fsym.upper(),
            "tsym": tsym.upper(),
            "limit": limit,
            "aggregate": aggregate,
        }
        
        if exchange:
            params["e"] = exchange
        if to_ts:
            params["toTs"] = to_ts
            
        response = await self.http.get("/data/v2/histoday", params=params)
        return HistoricalResponse(**response)
    
    async def get_historical_hour(
        self,
        fsym: str,
        tsym: str,
        limit: int = 24,
        aggregate: int = 1,
        exchange: Optional[str] = None,
        to_ts: Optional[int] = None,
    ) -> HistoricalResponse:
        """
        Get hourly historical OHLCV data
        
        Args:
            fsym: From symbol (e.g., 'BTC')
            tsym: To symbol (e.g., 'USD')
            limit: Number of data points (max 2000, default 24)
            aggregate: Data points to aggregate (default 1)
            exchange: Optional exchange name (default: CCCAGG)
            to_ts: Optional timestamp to get data up to
            
        Returns:
            HistoricalResponse with OHLCV data
            
        Example:
            >>> hist = await client.get_historical_hour('ETH', 'USD', limit=12)
            >>> for point in hist.data:
            ...     print(point.time, point.high, point.low)
        """
        params = {
            "fsym": fsym.upper(),
            "tsym": tsym.upper(),
            "limit": limit,
            "aggregate": aggregate,
        }
        
        if exchange:
            params["e"] = exchange
        if to_ts:
            params["toTs"] = to_ts
            
        response = await self.http.get("/data/v2/histohour", params=params)
        return HistoricalResponse(**response)
    
    async def get_historical_minute(
        self,
        fsym: str,
        tsym: str,
        limit: int = 60,
        aggregate: int = 1,
        exchange: Optional[str] = None,
        to_ts: Optional[int] = None,
    ) -> HistoricalResponse:
        """
        Get minute-level historical OHLCV data
        
        Args:
            fsym: From symbol (e.g., 'BTC')
            tsym: To symbol (e.g., 'USD')
            limit: Number of data points (max 2000, default 60)
            aggregate: Data points to aggregate (default 1)
            exchange: Optional exchange name (default: CCCAGG)
            to_ts: Optional timestamp to get data up to
            
        Returns:
            HistoricalResponse with OHLCV data
            
        Example:
            >>> hist = await client.get_historical_minute('BTC', 'USD', limit=30)
            >>> latest = hist.data[-1]
            >>> print(f"Latest close: {latest.close}")
        """
        params = {
            "fsym": fsym.upper(),
            "tsym": tsym.upper(),
            "limit": limit,
            "aggregate": aggregate,
        }
        
        if exchange:
            params["e"] = exchange
        if to_ts:
            params["toTs"] = to_ts
            
        response = await self.http.get("/data/v2/histominute", params=params)
        return HistoricalResponse(**response)
    
    # Coin/Exchange information endpoints
    
    async def get_coin_list(self) -> CoinListResponse:
        """
        Get list of all available cryptocurrencies
        
        Returns:
            CoinListResponse with coin information
            
        Example:
            >>> coin_list = await client.get_coin_list()
            >>> btc_info = coin_list.data['BTC']
            >>> print(btc_info.full_name)  # 'Bitcoin (BTC)'
        """
        response = await self.http.get("/data/all/coinlist")
        return CoinListResponse(**response)
    
    async def get_top_by_volume(
        self,
        tsym: str = "USD",
        limit: int = 10,
    ) -> TopVolumeResponse:
        """
        Get top cryptocurrencies by 24h volume
        
        Args:
            tsym: Currency to get volume in (default: 'USD')
            limit: Number of results (default 10, max 100)
            
        Returns:
            TopVolumeResponse with top volume coins
            
        Example:
            >>> top = await client.get_top_by_volume(limit=5)
            >>> for coin in top.data:
            ...     print(coin.symbol, coin.volume_24h)
        """
        params = {
            "tsym": tsym.upper(),
            "limit": limit,
        }
        
        response = await self.http.get("/data/top/totalvolfull", params=params)
        return TopVolumeResponse(**response)
    
    async def get_top_by_market_cap(
        self,
        tsym: str = "USD",
        limit: int = 10,
    ) -> TopVolumeResponse:
        """
        Get top cryptocurrencies by market cap
        
        Args:
            tsym: Currency to get market cap in (default: 'USD')
            limit: Number of results (default 10, max 100)
            
        Returns:
            TopVolumeResponse with top market cap coins
            
        Example:
            >>> top = await client.get_top_by_market_cap(limit=5)
            >>> for coin in top.data:
            ...     print(coin.full_name)
        """
        params = {
            "tsym": tsym.upper(),
            "limit": limit,
        }
        
        response = await self.http.get("/data/top/mktcapfull", params=params)
        return TopVolumeResponse(**response)
    
    async def get_exchange_list(self) -> ExchangeListResponse:
        """
        Get list of all available exchanges
        
        Returns:
            ExchangeListResponse with exchange information
            
        Example:
            >>> exchanges = await client.get_exchange_list()
            >>> for name, info in exchanges.data.items():
            ...     print(name, info.name)
        """
        response = await self.http.get("/data/all/exchanges")
        return ExchangeListResponse(**response)
    
    async def get_trading_pairs(
        self,
        exchange: Optional[str] = None,
    ) -> Dict[str, List[str]]:
        """
        Get available trading pairs for exchanges
        
        Args:
            exchange: Optional specific exchange to get pairs for
            
        Returns:
            Dictionary mapping symbols to list of trading pairs
            
        Example:
            >>> pairs = await client.get_trading_pairs()
            >>> btc_pairs = pairs.get('BTC', [])
            >>> print('USD' in btc_pairs)  # True
        """
        params = {}
        if exchange:
            params["e"] = exchange
            
        return await self.http.get("/data/v4/all/exchanges", params=params)
    
    # Social and news endpoints
    
    async def get_social_stats(
        self,
        coin_id: int,
    ) -> Dict[str, Any]:
        """
        Get social statistics for a cryptocurrency
        
        Args:
            coin_id: CryptoCompare coin ID
            
        Returns:
            Dictionary with social statistics
            
        Example:
            >>> social = await client.get_social_stats(1182)  # Bitcoin
            >>> print(social)
        """
        params = {"id": coin_id}
        return await self.http.get("/data/social/coin/latest", params=params)
    
    async def get_latest_news(
        self,
        lang: str = "EN",
        feeds: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get latest cryptocurrency news
        
        Args:
            lang: Language code (default: 'EN')
            feeds: Optional list of news feeds
            categories: Optional list of categories
            
        Returns:
            Dictionary with news articles
            
        Example:
            >>> news = await client.get_latest_news()
            >>> for article in news.get('Data', []):
            ...     print(article['title'])
        """
        params = {"lang": lang}
        
        if feeds:
            params["feeds"] = ",".join(feeds)
        if categories:
            params["categories"] = ",".join(categories)
            
        return await self.http.get("/data/v2/news/", params=params)