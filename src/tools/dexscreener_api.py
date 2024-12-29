import os
from typing import Dict, Any, List, Optional
import pandas as pd
import requests
from time import sleep

# Base URL for DexScreener API
BASE_URL = "https://api.dexscreener.com/latest/dex"

# Rate limiting constants
RATE_LIMIT_PAIRS = 300  # requests per minute
RATE_LIMIT_WAIT = 60 / RATE_LIMIT_PAIRS  # seconds between requests

def _handle_rate_limit():
    """Simple rate limit handler"""
    sleep(RATE_LIMIT_WAIT)

def get_crypto_pair_info(
    token_address: str,
    chain_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch basic token information from DexScreener.
    
    Args:
        token_address: The token's contract address
        chain_id: Optional chain ID to filter results
        
    Returns:
        Dictionary containing all pairs data
    """
    url = f"{BASE_URL}/tokens/{token_address}"
    print(f"Fetching data from: {url}")  # Debug print
    
    response = requests.get(url)
    _handle_rate_limit()
    
    if response.status_code != 200:
        raise Exception(
            f"Error fetching data: {response.status_code} - {response.text}"
        )
    
    data = response.json()
    pairs = data.get("pairs", [])
    
    if not pairs:
        raise ValueError(f"No pairs found for token {token_address}")
    
    print(f"Found {len(pairs)} pairs for token")  # Debug print
    
    # If chain_id is specified, filter for that chain
    if chain_id:
        # Convert chain names to lowercase for case-insensitive comparison
        chain_id = chain_id.lower()
        pairs = [p for p in pairs if p.get("chainId", "").lower() == chain_id]
        if not pairs:
            # List available chains
            available_chains = set(p.get("chainId", "").lower() for p in data.get("pairs", []))
            raise ValueError(
                f"No pairs found for token {token_address} on chain {chain_id}. "
                f"Available chains: {', '.join(available_chains)}"
            )
    
    return {
        "pairs": pairs,
        "schemaVersion": data.get("schemaVersion")
    }

def get_crypto_market_cap(
    token_address: str,
    chain_id: Optional[str] = None
) -> float:
    """
    Get current market cap from DexScreener
    
    Args:
        token_address: The token's contract address
        chain_id: Optional chain ID to filter results
        
    Returns:
        Market cap in USD
    """
    try:
        pair_info = get_crypto_pair_info(token_address, chain_id)
        pairs = pair_info.get("pairs", [])
        if pairs:
            most_liquid_pair = max(pairs, key=lambda x: float(x.get("liquidity", {}).get("usd", 0)))
            return float(most_liquid_pair.get("marketCap", 0)) if most_liquid_pair.get("marketCap") else 0.0
        else:
            return 0.0
    except Exception as e:
        print(f"Error fetching market cap: {e}")
        return 0.0

def get_dex_liquidity(
    token_address: str,
    chain_id: Optional[str] = None
) -> Dict[str, float]:
    """
    Get liquidity information across different DEXes
    
    Args:
        token_address: The token's contract address
        chain_id: Optional chain ID to filter results
        
    Returns:
        Dictionary mapping DEX names to their liquidity in USD
    """
    url = f"{BASE_URL}/tokens/{token_address}"
    print(f"Fetching data from: {url}")  # Debug print
    
    response = requests.get(url)
    _handle_rate_limit()
    
    if response.status_code != 200:
        raise Exception(
            f"Error fetching data: {response.status_code} - {response.text}"
        )
    
    data = response.json()
    pairs = data.get("pairs", [])
    
    if chain_id:
        pairs = [p for p in pairs if p.get("chainId") == chain_id]
    
    liquidity_by_dex = {}
    for pair in pairs:
        dex_id = pair.get("dexId")
        liquidity_usd = float(pair.get("liquidity", {}).get("usd", 0))
        
        if dex_id in liquidity_by_dex:
            liquidity_by_dex[dex_id] += liquidity_usd
        else:
            liquidity_by_dex[dex_id] = liquidity_usd
    
    return liquidity_by_dex

def get_crypto_prices(
    token_address: str,
    chain_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch price data from DexScreener
    Note: DexScreener's free API doesn't provide historical OHLCV data
    This returns the latest price data from the most liquid pairs
    
    Args:
        token_address: The token's contract address
        chain_id: Optional chain ID to filter results
        
    Returns:
        List of dictionaries containing price and volume data
    """
    url = f"{BASE_URL}/tokens/{token_address}"
    print(f"Fetching data from: {url}")  # Debug print
    
    response = requests.get(url)
    _handle_rate_limit()
    
    if response.status_code != 200:
        raise Exception(
            f"Error fetching data: {response.status_code} - {response.text}"
        )
    
    data = response.json()
    pairs = data.get("pairs", [])
    
    if chain_id:
        pairs = [p for p in pairs if p.get("chainId") == chain_id]
    
    if not pairs:
        raise ValueError(f"No pairs found for token {token_address}")
    
    price_data = []
    for pair in pairs:
        price_data.append({
            "time": pair.get("priceTimestamp"),
            "price": float(pair.get("priceUsd", 0)),
            "volume_24h": float(pair.get("volume", {}).get("h24", 0)),
            "liquidity": float(pair.get("liquidity", {}).get("usd", 0)),
            "txns_24h": pair.get("txns", {}).get("h24", {}).get("total", 0),
            "dex": pair.get("dexId"),
            "chain": pair.get("chainId"),
            "pair_address": pair.get("pairAddress")
        })
    
    return price_data

def prices_to_df(prices: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert price data to DataFrame
    
    Args:
        prices: List of price data dictionaries
        
    Returns:
        Pandas DataFrame with price data
    """
    try:
        df = pd.DataFrame(prices)
        if not df.empty:
            df["time"] = pd.to_datetime(df["time"])
            df.set_index("time", inplace=True)
            df.sort_index(inplace=True)
        return df
    except Exception as e:
        print(f"Error converting prices to DataFrame: {e}")
        return pd.DataFrame()
