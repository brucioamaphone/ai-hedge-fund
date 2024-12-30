from langchain_core.messages import HumanMessage
from agents.state import AgentState, show_agent_reasoning
import json

def valuation_agent(state: AgentState):
    """Performs valuation analysis using crypto-specific metrics."""
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    pair_info = data["pair_info"]
    
    # Initialize signals and reasoning
    signals = []
    reasoning = {}
    
    # 1. Market Cap to TVL Ratio Analysis
    mcap_score = 0
    market_cap = float(pair_info["fdv"])  # Fully diluted valuation
    total_liquidity = float(pair_info["liquidity"]["usd"])
    mcap_tvl_ratio = market_cap / total_liquidity if total_liquidity > 0 else float('inf')
    
    # Lower ratio suggests potential undervaluation
    if mcap_tvl_ratio < 4:  # Considered undervalued
        mcap_score += 1
    if mcap_tvl_ratio < 2:  # Significantly undervalued
        mcap_score += 1
        
    signals.append('bullish' if mcap_score >= 2 else 'bearish' if mcap_score == 0 else 'neutral')
    reasoning["mcap_tvl_analysis"] = {
        "signal": signals[0],
        "details": f"Market Cap: ${market_cap:,.2f}, TVL: ${total_liquidity:,.2f}, Ratio: {mcap_tvl_ratio:.2f}"
    }
    
    # 2. Volume to Market Cap Ratio Analysis
    volume_score = 0
    daily_volume = float(pair_info["volume"]["h24"])
    volume_mcap_ratio = daily_volume / market_cap if market_cap > 0 else 0
    
    # Higher ratio suggests more active trading and potential undervaluation
    if volume_mcap_ratio > 0.05:  # Over 5% daily volume/mcap
        volume_score += 1
    if volume_mcap_ratio > 0.10:  # Over 10% daily volume/mcap
        volume_score += 1
        
    signals.append('bullish' if volume_score >= 2 else 'bearish' if volume_score == 0 else 'neutral')
    reasoning["volume_mcap_analysis"] = {
        "signal": signals[1],
        "details": f"24h Volume: ${daily_volume:,.2f}, Volume/MCap Ratio: {volume_mcap_ratio:.3f}"
    }
    
    # 3. Price Momentum Value Analysis
    momentum_score = 0
    price_change_24h = float(pair_info["priceChange"]["h24"])
    price_change_6h = float(pair_info["priceChange"]["h6"])
    
    # Look for oversold conditions with improving momentum
    if price_change_24h < -10 and price_change_6h > 0:  # Potential reversal
        momentum_score += 1
    if price_change_24h < -20 and price_change_6h > 2:  # Strong reversal signal
        momentum_score += 1
        
    signals.append('bullish' if momentum_score >= 2 else 'bearish' if momentum_score == 0 else 'neutral')
    reasoning["momentum_value_analysis"] = {
        "signal": signals[2],
        "details": f"24h Change: {price_change_24h:.2f}%, 6h Change: {price_change_6h:.2f}%"
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
        print("\nValuation Analysis:")
        print(json.dumps(reasoning, indent=2))
        
    # Update state
    state["signals"] = state.get("signals", {})
    state["reasoning"] = state.get("reasoning", {})
    state["signals"]["valuation"] = final_signal
    state["reasoning"]["valuation"] = reasoning
    
    # Store valuation analysis for InfluxDB
    state["data"]["valuation_analysis"] = {
        "symbol": pair_info["baseToken"]["symbol"],
        "name": pair_info["baseToken"]["name"],
        "mcap_tvl_analysis": reasoning["mcap_tvl_analysis"],
        "volume_mcap_analysis": reasoning["volume_mcap_analysis"],
        "momentum_value_analysis": reasoning["momentum_value_analysis"]
    }
    
    return state