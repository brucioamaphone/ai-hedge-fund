from langchain_openai.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage
from agents.state import AgentState, show_agent_reasoning
from tools.dexscreener_api import get_crypto_pair_info, get_crypto_prices, get_crypto_market_cap, get_dex_liquidity
import json
from datetime import datetime

def market_data_agent(state: AgentState):
    """Responsible for gathering and preprocessing market data for crypto assets"""
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]

    # Get the token's trading data
    token_address = data["token_address"]
    chain_id = data.get("chain_id", "base")  # Default to Base chain if not specified
    
    try:
        # Get comprehensive pair info
        pairs = get_crypto_pair_info(token_address, chain_id)
        
        # Get the most liquid pair
        most_liquid_pair = max(pairs["pairs"], key=lambda x: float(x.get("liquidity", {}).get("usd", 0)))
        
        # Update the state with crypto-specific market data
        data.update({
            "pair_info": most_liquid_pair,
            "current_price": float(most_liquid_pair["priceUsd"]),
            "market_cap": float(most_liquid_pair["fdv"]),  # Using fully diluted valuation
            "volume_24h": float(most_liquid_pair["volume"]["h24"]),
            "liquidity": float(most_liquid_pair["liquidity"]["usd"])
        })
        
        # Generate market data summary
        summary = {
            "price": f"${data['current_price']:.4f}",
            "market_cap": f"${data['market_cap']:,.2f}",
            "24h_volume": f"${data['volume_24h']:,.2f}",
            "liquidity": f"${data['liquidity']:,.2f}",
            "24h_change": f"{float(most_liquid_pair['priceChange']['h24']):,.2f}%",
            "trades_24h": f"Buys: {most_liquid_pair['txns']['h24']['buys']}, Sells: {most_liquid_pair['txns']['h24']['sells']}"
        }
        
        if show_reasoning:
            print("\nMarket Data Summary:")
            print(json.dumps(summary, indent=2))
        
        # Update state with the summary
        state["data"] = data
        state["market_summary"] = summary
        
        return state
        
    except Exception as e:
        print(f"Error fetching market data: {str(e)}")
        raise