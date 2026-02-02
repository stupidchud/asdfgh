from typing import Optional, Dict, Any

import aiohttp
import logging


logger: logging.Logger = logging.getLogger(__name__)
BASE_URL: str = "https://min-api.cryptocompare.com"


class HTTPClient:
    """HTTP client for making requests to CryptoCompare API"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None
    ):
        """
        Initialize HTTP client
        
        Args:
            api_key: Optional API key for authenticated requests
            session: Optional aiohttp ClientSession to use
        """
        self.api_key = api_key
        self._session = session
        self._owned_session = session is None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owned_session = True
        return self._session
    
    async def close(self) -> None:
        """Close the HTTP session if owned by this client"""
        if self._owned_session and self._session and not self._session.closed:
            await self._session.close()
            
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers with optional API key"""
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            headers["authorization"] = f"Apikey {self.api_key}"
            
        return headers
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Optional query parameters
            data: Optional request body data
            
        Returns:
            JSON response as dictionary
            
        Raises:
            aiohttp.ClientError: On request failure
        """
        session = await self._get_session()
        url = f"{BASE_URL}{endpoint}"
        headers = self._build_headers()
        
        # Filter out None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}
        
        logger.debug(f"Making {method} request to {url} with params: {params}")
        
        async with session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
        ) as response:
            response.raise_for_status()
            result = await response.json()
            
            # Check for API errors
            if isinstance(result, dict):
                if result.get("Response") == "Error":
                    error_msg = result.get("Message", "Unknown API error")
                    logger.error(f"API error: {error_msg}")
                    raise ValueError(f"CryptoCompare API error: {error_msg}")
                    
            return result
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a GET request
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            
        Returns:
            JSON response as dictionary
        """
        return await self.request("GET", endpoint, params=params)
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a POST request
        
        Args:
            endpoint: API endpoint path
            data: Optional request body data
            params: Optional query parameters
            
        Returns:
            JSON response as dictionary
        """
        return await self.request("POST", endpoint, params=params, data=data)
