from langchain_core.messages import HumanMessage
from agents.state import AgentState, show_agent_reasoning
import json

##### Fundamental Agent #####
def fundamentals_agent(state: AgentState):
    """Analyzes fundamental data and generates trading signals for crypto tokens."""
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    pair_info = data["pair_info"]  # This comes from DexScreener API

    # Initialize signals list for different fundamental aspects
    signals = []
    reasoning = {}
    
    # 1. Liquidity Analysis
    liquidity_score = 0
    total_liquidity = float(pair_info["liquidity"]["usd"])
    if total_liquidity > 1_000_000:  # Over $1M liquidity
        liquidity_score += 1
    if total_liquidity > 5_000_000:  # Over $5M liquidity
        liquidity_score += 1
        
    signals.append('bullish' if liquidity_score >= 2 else 'bearish' if liquidity_score == 0 else 'neutral')
    reasoning["liquidity_signal"] = {
        "signal": signals[0],
        "details": f"Total Liquidity: ${total_liquidity:,.2f}"
    }
    
    # 2. Volume Analysis
    volume_score = 0
    daily_volume = float(pair_info["volume"]["h24"])
    volume_to_liquidity = daily_volume / total_liquidity if total_liquidity > 0 else 0
    
    if daily_volume > 1_000_000:  # Over $1M daily volume
        volume_score += 1
    if volume_to_liquidity > 0.1:  # Healthy volume relative to liquidity
        volume_score += 1
        
    signals.append('bullish' if volume_score >= 2 else 'bearish' if volume_score == 0 else 'neutral')
    reasoning["volume_signal"] = {
        "signal": signals[1],
        "details": f"24h Volume: ${daily_volume:,.2f}, Volume/Liquidity Ratio: {volume_to_liquidity:.2f}"
    }
    
    # 3. Price Movement Analysis
    price_score = 0
    price_change_24h = float(pair_info["priceChange"]["h24"])
    price_change_6h = float(pair_info["priceChange"]["h6"])
    
    if price_change_24h > 0:  # Positive 24h trend
        price_score += 1
    if price_change_6h > 0:  # Positive 6h trend
        price_score += 1
        
    signals.append('bullish' if price_score >= 2 else 'bearish' if price_score == 0 else 'neutral')
    reasoning["price_signal"] = {
        "signal": signals[2],
        "details": f"24h Change: {price_change_24h:.2f}%, 6h Change: {price_change_6h:.2f}%"
    }
    
    # 4. Transaction Analysis
    txn_score = 0
    buys_24h = pair_info["txns"]["h24"]["buys"]
    sells_24h = pair_info["txns"]["h24"]["sells"]
    buy_sell_ratio = buys_24h / sells_24h if sells_24h > 0 else 1
    total_txns = buys_24h + sells_24h
    
    if buy_sell_ratio > 1.5:  # Strong buy pressure
        txn_score += 1
    if total_txns > 1000:  # High trading activity
        txn_score += 1
        
    signals.append('bullish' if txn_score >= 2 else 'bearish' if txn_score == 0 else 'neutral')
    reasoning["transaction_signal"] = {
        "signal": signals[3],
        "details": f"Buy/Sell Ratio: {buy_sell_ratio:.2f}, Total Transactions: {total_txns}"
    }
    
    # Aggregate signals
    bullish_count = len([s for s in signals if s == 'bullish'])
    bearish_count = len([s for s in signals if s == 'bearish'])
    
    if bullish_count > len(signals) / 2:
        final_signal = 'bullish'
    elif bearish_count > len(signals) / 2:
        final_signal = 'bearish'
    else:
        final_signal = 'neutral'
        
    if show_reasoning:
        print("\nFundamental Analysis:")
        print(json.dumps(reasoning, indent=2))
        
    # Update state
    state["signals"] = state.get("signals", {})
    state["reasoning"] = state.get("reasoning", {})
    state["signals"]["fundamental"] = final_signal
    state["reasoning"]["fundamental"] = reasoning
    
    return state