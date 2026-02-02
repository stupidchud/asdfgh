from typing import Optional, Dict, Any, List, Union

from pydantic import BaseModel, Field


class PriceData(BaseModel):
    """Single price data response"""
    
    prices: Dict[str, float] = Field(default_factory=dict)
    
    def __getitem__(self, key: str) -> float:
        """Allow dictionary-style access to prices"""
        return self.prices[key.upper()]
    
    def __str__(self) -> str:
        """String representation returns first price value if only one currency"""
        if len(self.prices) == 1:
            return str(list(self.prices.values())[0])
        return str(self.prices)
    
    def __float__(self) -> float:
        """Float conversion returns first price value"""
        if self.prices:
            return list(self.prices.values())[0]
        return 0.0
    
    def get(self, key: str, default: Any = None) -> Optional[float]:
        """Get price for a specific currency"""
        return self.prices.get(key.upper(), default)


class DisplayData(BaseModel):
    """Display information for price data"""
    
    from_symbol: Optional[str] = Field(None, alias="FROMSYMBOL")
    to_symbol: Optional[str] = Field(None, alias="TOSYMBOL")
    market: Optional[str] = Field(None, alias="MARKET")
    price: Optional[float] = Field(None, alias="PRICE")
    last_update: Optional[int] = Field(None, alias="LASTUPDATE")
    last_volume: Optional[float] = Field(None, alias="LASTVOLUME")
    last_volume_to: Optional[float] = Field(None, alias="LASTVOLUMETO")
    last_trade_id: Optional[str] = Field(None, alias="LASTTRADEID")
    volume_day: Optional[float] = Field(None, alias="VOLUMEDAY")
    volume_day_to: Optional[float] = Field(None, alias="VOLUMEDAYTO")
    volume_24h: Optional[float] = Field(None, alias="VOLUME24HOUR")
    volume_24h_to: Optional[float] = Field(None, alias="VOLUME24HOURTO")
    open_day: Optional[float] = Field(None, alias="OPENDAY")
    high_day: Optional[float] = Field(None, alias="HIGHDAY")
    low_day: Optional[float] = Field(None, alias="LOWDAY")
    open_24h: Optional[float] = Field(None, alias="OPEN24HOUR")
    high_24h: Optional[float] = Field(None, alias="HIGH24HOUR")
    low_24h: Optional[float] = Field(None, alias="LOW24HOUR")
    last_market: Optional[str] = Field(None, alias="LASTMARKET")
    change_day: Optional[float] = Field(None, alias="CHANGEDAY")
    change_pct_day: Optional[float] = Field(None, alias="CHANGEPCTDAY")
    change_24h: Optional[float] = Field(None, alias="CHANGE24HOUR")
    change_pct_24h: Optional[float] = Field(None, alias="CHANGEPCT24HOUR")
    supply: Optional[float] = Field(None, alias="SUPPLY")
    market_cap: Optional[float] = Field(None, alias="MKTCAP")
    total_volume_24h: Optional[float] = Field(None, alias="TOTALVOLUME24H")
    total_volume_24h_to: Optional[float] = Field(None, alias="TOTALVOLUME24HTO")
    
    class Config:
        populate_by_name = True


class RawData(BaseModel):
    """Raw data for price information"""
    
    type: Optional[str] = Field(None, alias="TYPE")
    market: Optional[str] = Field(None, alias="MARKET")
    from_symbol: Optional[str] = Field(None, alias="FROMSYMBOL")
    to_symbol: Optional[str] = Field(None, alias="TOSYMBOL")
    flags: Optional[int] = Field(None, alias="FLAGS")
    price: Optional[float] = Field(None, alias="PRICE")
    last_update: Optional[int] = Field(None, alias="LASTUPDATE")
    median: Optional[float] = Field(None, alias="MEDIAN")
    last_volume: Optional[float] = Field(None, alias="LASTVOLUME")
    last_volume_to: Optional[float] = Field(None, alias="LASTVOLUMETO")
    last_trade_id: Optional[str] = Field(None, alias="LASTTRADEID")
    volume_day: Optional[float] = Field(None, alias="VOLUMEDAY")
    volume_day_to: Optional[float] = Field(None, alias="VOLUMEDAYTO")
    volume_24h: Optional[float] = Field(None, alias="VOLUME24HOUR")
    volume_24h_to: Optional[float] = Field(None, alias="VOLUME24HOURTO")
    open_day: Optional[float] = Field(None, alias="OPENDAY")
    high_day: Optional[float] = Field(None, alias="HIGHDAY")
    low_day: Optional[float] = Field(None, alias="LOWDAY")
    open_24h: Optional[float] = Field(None, alias="OPEN24HOUR")
    high_24h: Optional[float] = Field(None, alias="HIGH24HOUR")
    low_24h: Optional[float] = Field(None, alias="LOW24HOUR")
    last_market: Optional[str] = Field(None, alias="LASTMARKET")
    volume_hour: Optional[float] = Field(None, alias="VOLUMEHOUR")
    volume_hour_to: Optional[float] = Field(None, alias="VOLUMEHOURTO")
    open_hour: Optional[float] = Field(None, alias="OPENHOUR")
    high_hour: Optional[float] = Field(None, alias="HIGHHOUR")
    low_hour: Optional[float] = Field(None, alias="LOWHOUR")
    top_tier_volume_24h: Optional[float] = Field(None, alias="TOPTIERVOLUME24HOUR")
    top_tier_volume_24h_to: Optional[float] = Field(None, alias="TOPTIERVOLUME24HOURTO")
    change_24h: Optional[float] = Field(None, alias="CHANGE24HOUR")
    change_pct_24h: Optional[float] = Field(None, alias="CHANGEPCT24HOUR")
    change_day: Optional[float] = Field(None, alias="CHANGEDAY")
    change_pct_day: Optional[float] = Field(None, alias="CHANGEPCTDAY")
    change_hour: Optional[float] = Field(None, alias="CHANGEHOUR")
    change_pct_hour: Optional[float] = Field(None, alias="CHANGEPCTHOUR")
    conversion_type: Optional[str] = Field(None, alias="CONVERSIONTYPE")
    conversion_symbol: Optional[str] = Field(None, alias="CONVERSIONSYMBOL")
    supply: Optional[float] = Field(None, alias="SUPPLY")
    market_cap: Optional[float] = Field(None, alias="MKTCAP")
    total_volume_24h: Optional[float] = Field(None, alias="TOTALVOLUME24H")
    total_volume_24h_to: Optional[float] = Field(None, alias="TOTALVOLUME24HTO")
    total_top_tier_volume_24h: Optional[float] = Field(None, alias="TOTALTOPTIERVOLUME24H")
    total_top_tier_volume_24h_to: Optional[float] = Field(None, alias="TOTALTOPTIERVOLUME24HTO")
    image_url: Optional[str] = Field(None, alias="IMAGEURL")
    
    class Config:
        populate_by_name = True


class PriceFullData(BaseModel):
    """Full price data with raw and display information"""
    
    raw: Optional[RawData] = Field(None, alias="RAW")
    display: Optional[DisplayData] = Field(None, alias="DISPLAY")
    
    class Config:
        populate_by_name = True


class MultiPriceFullData(BaseModel):
    """Multiple symbols full price data"""
    
    raw: Dict[str, Dict[str, RawData]] = Field(default_factory=dict, alias="RAW")
    display: Dict[str, Dict[str, DisplayData]] = Field(default_factory=dict, alias="DISPLAY")
    
    class Config:
        populate_by_name = True


class OHLCVData(BaseModel):
    """OHLCV (Open, High, Low, Close, Volume) historical data point"""
    
    time: int = Field(..., description="Timestamp")
    close: float = Field(..., description="Close price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    open: float = Field(..., description="Open price")
    volume_from: float = Field(..., alias="volumefrom", description="Volume from")
    volume_to: float = Field(..., alias="volumeto", description="Volume to")
    conversion_type: Optional[str] = Field(None, alias="conversionType")
    conversion_symbol: Optional[str] = Field(None, alias="conversionSymbol")
    
    class Config:
        populate_by_name = True


class HistoricalResponse(BaseModel):
    """Response for historical data"""
    
    response: str = Field(..., description="Response status")
    message: Optional[str] = Field(None, description="Response message")
    has_warning: Optional[bool] = Field(None, alias="HasWarning")
    type: int = Field(..., alias="Type")
    rate_limit: Optional[Dict[str, Any]] = Field(None, alias="RateLimit")
    data: List[OHLCVData] = Field(default_factory=list, alias="Data")
    time_from: Optional[int] = Field(None, alias="TimeFrom")
    time_to: Optional[int] = Field(None, alias="TimeTo")
    first_value_in_array: Optional[bool] = Field(None, alias="FirstValueInArray")
    conversion_type: Optional[Dict[str, str]] = Field(None, alias="ConversionType")
    aggregated: Optional[bool] = Field(None, alias="Aggregated")
    
    class Config:
        populate_by_name = True


class CoinInfo(BaseModel):
    """Cryptocurrency information"""
    
    id: Optional[str] = Field(None, alias="Id")
    url: Optional[str] = Field(None, alias="Url")
    image_url: Optional[str] = Field(None, alias="ImageUrl")
    name: Optional[str] = Field(None, alias="Name")
    symbol: Optional[str] = Field(None, alias="Symbol")
    coin_name: Optional[str] = Field(None, alias="CoinName")
    full_name: Optional[str] = Field(None, alias="FullName")
    algorithm: Optional[str] = Field(None, alias="Algorithm")
    proof_type: Optional[str] = Field(None, alias="ProofType")
    fully_premined: Optional[str] = Field(None, alias="FullyPremined")
    total_coin_supply: Optional[str] = Field(None, alias="TotalCoinSupply")
    built_on: Optional[str] = Field(None, alias="BuiltOn")
    smart_contract_address: Optional[str] = Field(None, alias="SmartContractAddress")
    decimals: Optional[int] = Field(None, alias="Decimals")
    
    class Config:
        populate_by_name = True


class CoinListResponse(BaseModel):
    """Response for coin list"""
    
    response: str = Field(..., alias="Response")
    message: str = Field(..., alias="Message")
    base_image_url: Optional[str] = Field(None, alias="BaseImageUrl")
    base_link_url: Optional[str] = Field(None, alias="BaseLinkUrl")
    data: Dict[str, CoinInfo] = Field(default_factory=dict, alias="Data")
    
    class Config:
        populate_by_name = True


class TopVolume(BaseModel):
    """Top volume coin data"""
    
    symbol: str = Field(..., alias="SYMBOL")
    supply: Optional[float] = Field(None, alias="SUPPLY")
    full_name: Optional[str] = Field(None, alias="FULLNAME")
    name: Optional[str] = Field(None, alias="NAME")
    id: Optional[str] = Field(None, alias="ID")
    volume_24h: Optional[float] = Field(None, alias="VOLUME24HOURTO")
    
    class Config:
        populate_by_name = True


class TopVolumeResponse(BaseModel):
    """Response for top volume coins"""
    
    message: Optional[str] = Field(None, alias="Message")
    type: Optional[int] = Field(None, alias="Type")
    metadata_response: Optional[str] = Field(None, alias="MetaData")
    sponsored_data: Optional[List[Any]] = Field(None, alias="SponsoredData")
    data: List[TopVolume] = Field(default_factory=list, alias="Data")
    rate_limit: Optional[Dict[str, Any]] = Field(None, alias="RateLimit")
    has_warning: Optional[bool] = Field(None, alias="HasWarning")
    
    class Config:
        populate_by_name = True


class ExchangeInfo(BaseModel):
    """Exchange information"""
    
    id: Optional[str] = Field(None, alias="Id")
    name: Optional[str] = Field(None, alias="Name")
    logo_url: Optional[str] = Field(None, alias="LogoUrl")
    item_type: Optional[List[str]] = Field(None, alias="ItemType")
    
    class Config:
        populate_by_name = True


class ExchangeListResponse(BaseModel):
    """Response for exchange list"""
    
    response: Optional[str] = Field(None, alias="Response")
    message: Optional[str] = Field(None, alias="Message")
    data: Dict[str, ExchangeInfo] = Field(default_factory=dict, alias="Data")
    
    class Config:
        populate_by_name = True


class APIError(BaseModel):
    """API error response"""
    
    response: str = Field(..., alias="Response")
    message: str = Field(..., alias="Message")
    has_warning: Optional[bool] = Field(None, alias="HasWarning")
    type: Optional[int] = Field(None, alias="Type")
    rate_limit: Optional[Dict[str, Any]] = Field(None, alias="RateLimit")
    
    class Config:
        populate_by_name = True
