from langchain_core.messages import HumanMessage
from agents.state import AgentState, show_agent_reasoning
import json
import math

##### Risk Management Agent #####
def risk_management_agent(state: AgentState):
    """Evaluates crypto trading risk and sets position limits based on DEX-specific risk analysis."""
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    pair_info = data["pair_info"]
    
    # Initialize signals and reasoning
    signals = []
    reasoning = {}
    
    # 1. Liquidity Risk Analysis
    liquidity_score = 0
    total_liquidity = float(pair_info["liquidity"]["usd"])
    daily_volume = float(pair_info["volume"]["h24"])
    liquidity_ratio = daily_volume / total_liquidity if total_liquidity > 0 else float('inf')
    
    # Check liquidity metrics
    if total_liquidity > 5_000_000:  # Over $5M liquidity
        liquidity_score += 1
    if liquidity_ratio < 3:  # Healthy volume to liquidity ratio
        liquidity_score += 1
        
    signals.append('low_risk' if liquidity_score >= 2 else 'high_risk' if liquidity_score == 0 else 'medium_risk')
    reasoning["liquidity_risk"] = {
        "signal": signals[0],
        "details": f"Liquidity: ${total_liquidity:,.2f}, Volume/Liquidity Ratio: {liquidity_ratio:.2f}"
    }
    
    # 2. Volatility Risk Analysis
    volatility_score = 0
    price_change_1h = abs(float(pair_info["priceChange"]["h1"]))
    price_change_24h = abs(float(pair_info["priceChange"]["h24"]))
    
    # Check volatility metrics
    if price_change_1h < 5:  # Less than 5% hourly change
        volatility_score += 1
    if price_change_24h < 20:  # Less than 20% daily change
        volatility_score += 1
        
    signals.append('low_risk' if volatility_score >= 2 else 'high_risk' if volatility_score == 0 else 'medium_risk')
    reasoning["volatility_risk"] = {
        "signal": signals[1],
        "details": f"1h Change: {price_change_1h:.2f}%, 24h Change: {price_change_24h:.2f}%"
    }
    
    # 3. Transaction Risk Analysis
    transaction_score = 0
    buys_24h = pair_info["txns"]["h24"]["buys"]
    sells_24h = pair_info["txns"]["h24"]["sells"]
    total_txns = buys_24h + sells_24h
    buy_sell_ratio = buys_24h / sells_24h if sells_24h > 0 else float('inf')
    
    # Check transaction metrics
    if total_txns > 1000:  # High trading activity
        transaction_score += 1
    if 0.5 <= buy_sell_ratio <= 2:  # Balanced buy/sell ratio
        transaction_score += 1
        
    signals.append('low_risk' if transaction_score >= 2 else 'high_risk' if transaction_score == 0 else 'medium_risk')
    reasoning["transaction_risk"] = {
        "signal": signals[2],
        "details": f"Total Txns: {total_txns}, Buy/Sell Ratio: {buy_sell_ratio:.2f}"
    }
    
    # 4. Market Impact Risk Analysis
    impact_score = 0
    avg_trade_size = daily_volume / total_txns if total_txns > 0 else 0
    max_trade_size = total_liquidity * 0.01  # 1% of liquidity
    
    # Check market impact metrics
    if avg_trade_size < max_trade_size * 0.1:  # Average trade is small relative to max
        impact_score += 1
    if daily_volume > total_liquidity * 0.1:  # Good daily volume
        impact_score += 1
        
    signals.append('low_risk' if impact_score >= 2 else 'high_risk' if impact_score == 0 else 'medium_risk')
    reasoning["market_impact_risk"] = {
        "signal": signals[3],
        "details": f"Avg Trade: ${avg_trade_size:,.2f}, Max Trade: ${max_trade_size:,.2f}"
    }
    
    # Calculate position size limits based on risk assessment
    low_risk_count = len([s for s in signals if s == 'low_risk'])
    high_risk_count = len([s for s in signals if s == 'high_risk'])
    
    # Base position size on liquidity
    if low_risk_count > len(signals) / 2:
        max_position = min(total_liquidity * 0.01, 100_000)  # 1% of liquidity or $100k
        risk_signal = 'low_risk'
    elif high_risk_count > len(signals) / 2:
        max_position = min(total_liquidity * 0.001, 10_000)  # 0.1% of liquidity or $10k
        risk_signal = 'high_risk'
    else:
        max_position = min(total_liquidity * 0.005, 50_000)  # 0.5% of liquidity or $50k
        risk_signal = 'medium_risk'
        
    reasoning["position_limits"] = {
        "max_position": f"${max_position:,.2f}",
        "risk_level": risk_signal
    }
    
    if show_reasoning:
        print("\nRisk Analysis:")
        print(json.dumps(reasoning, indent=2))
        
    # Update state
    state["signals"] = state.get("signals", {})
    state["reasoning"] = state.get("reasoning", {})
    state["signals"]["risk"] = risk_signal
    state["reasoning"]["risk"] = reasoning
    state["position_limits"] = {
        "max_position": max_position,
        "risk_level": risk_signal
    }
    
    return state
