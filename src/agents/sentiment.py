from langchain_core.messages import HumanMessage
from agents.state import AgentState, show_agent_reasoning
import json

##### Sentiment Agent #####
def sentiment_agent(state: AgentState):
    """Analyzes market sentiment and generates trading signals based on DEX trading patterns."""
    data = state["data"]
    pair_info = data["pair_info"]
    show_reasoning = state["metadata"]["show_reasoning"]

    # Initialize signals and reasoning
    signals = []
    reasoning = {}
    
    # 1. Transaction Pattern Analysis
    txn_score = 0
    buys_1h = pair_info["txns"]["h1"]["buys"]
    sells_1h = pair_info["txns"]["h1"]["sells"]
    buys_6h = pair_info["txns"]["h6"]["buys"]
    sells_6h = pair_info["txns"]["h6"]["sells"]
    buys_24h = pair_info["txns"]["h24"]["buys"]
    sells_24h = pair_info["txns"]["h24"]["sells"]
    
    # Calculate buy/sell ratios for different timeframes
    ratio_1h = buys_1h / sells_1h if sells_1h > 0 else 1
    ratio_6h = buys_6h / sells_6h if sells_6h > 0 else 1
    ratio_24h = buys_24h / sells_24h if sells_24h > 0 else 1
    
    # Check if buy pressure is increasing
    if ratio_1h > ratio_6h:
        txn_score += 1
    if ratio_6h > ratio_24h:
        txn_score += 1
        
    signals.append('bullish' if txn_score >= 2 else 'bearish' if txn_score == 0 else 'neutral')
    reasoning["transaction_pattern"] = {
        "signal": signals[0],
        "details": f"1h B/S: {ratio_1h:.2f}, 6h B/S: {ratio_6h:.2f}, 24h B/S: {ratio_24h:.2f}"
    }
    
    # 2. Price Impact Analysis
    impact_score = 0
    price_change_1h = float(pair_info["priceChange"]["h1"])
    price_change_6h = float(pair_info["priceChange"]["h6"])
    price_change_24h = float(pair_info["priceChange"]["h24"])
    
    # Check if recent price changes are more positive
    if price_change_1h > price_change_6h:
        impact_score += 1
    if price_change_6h > price_change_24h:
        impact_score += 1
        
    signals.append('bullish' if impact_score >= 2 else 'bearish' if impact_score == 0 else 'neutral')
    reasoning["price_impact"] = {
        "signal": signals[1],
        "details": f"1h: {price_change_1h:.2f}%, 6h: {price_change_6h:.2f}%, 24h: {price_change_24h:.2f}%"
    }
    
    # 3. Volume Trend Analysis
    volume_score = 0
    volume_1h = float(pair_info["volume"]["h1"])
    volume_6h = float(pair_info["volume"]["h6"])
    volume_24h = float(pair_info["volume"]["h24"])
    
    # Calculate hourly averages
    hourly_vol_1h = volume_1h
    hourly_vol_6h = volume_6h / 6
    hourly_vol_24h = volume_24h / 24
    
    # Check if recent volume is higher
    if hourly_vol_1h > hourly_vol_6h:
        volume_score += 1
    if hourly_vol_6h > hourly_vol_24h:
        volume_score += 1
        
    signals.append('bullish' if volume_score >= 2 else 'bearish' if volume_score == 0 else 'neutral')
    reasoning["volume_trend"] = {
        "signal": signals[2],
        "details": f"1h Avg: ${hourly_vol_1h:,.2f}, 6h Avg: ${hourly_vol_6h:,.2f}, 24h Avg: ${hourly_vol_24h:,.2f}"
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
        print("\nSentiment Analysis:")
        print(json.dumps(reasoning, indent=2))
        
    # Update state
    state["signals"] = state.get("signals", {})
    state["reasoning"] = state.get("reasoning", {})
    state["signals"]["sentiment"] = final_signal
    state["reasoning"]["sentiment"] = reasoning
    
    return state
