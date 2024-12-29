from langchain_core.messages import HumanMessage
from agents.state import AgentState, show_agent_reasoning
import json

##### Portfolio Management Agent #####
def portfolio_management_agent(state: AgentState):
    """Makes final trading decisions based on agent signals and risk constraints."""
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    pair_info = data["pair_info"]
    
    # Get signals from state
    signals = state.get("signals", {})
    reasoning = state.get("reasoning", {})
    position_limits = state.get("position_limits", {})
    
    # Initialize portfolio decision
    decision = {
        "action": "hold",  # Default to hold
        "size": 0,
        "reasoning": {}
    }
    
    # 1. Analyze Risk Parameters
    max_position = position_limits.get("max_position", 0)
    risk_level = position_limits.get("risk_level", "high_risk")
    
    decision["reasoning"]["risk_assessment"] = {
        "max_position": f"${max_position:,.2f}",
        "risk_level": risk_level,
        "details": reasoning.get("risk", {})
    }
    
    # 2. Analyze Trading Signals
    bullish_signals = 0
    bearish_signals = 0
    signal_count = 0
    
    # Weight the signals
    signal_weights = {
        "valuation": 0.35,
        "fundamentals": 0.30,
        "technical": 0.25,
        "sentiment": 0.10
    }
    
    weighted_score = 0
    for signal_type, weight in signal_weights.items():
        if signal_type in signals:
            signal = signals[signal_type]
            signal_count += 1
            
            if signal == "bullish":
                bullish_signals += 1
                weighted_score += weight
            elif signal == "bearish":
                bearish_signals += 1
                weighted_score -= weight
                
    # Calculate overall sentiment
    if signal_count > 0:
        sentiment_score = weighted_score
        
        if sentiment_score > 0.15:  # Strong bullish consensus
            base_action = "buy"
        elif sentiment_score < -0.15:  # Strong bearish consensus
            base_action = "sell"
        else:
            base_action = "hold"
    else:
        base_action = "hold"
        
    decision["reasoning"]["signal_analysis"] = {
        "bullish_signals": bullish_signals,
        "bearish_signals": bearish_signals,
        "weighted_score": f"{weighted_score:.2f}",
        "base_action": base_action
    }
    
    # 3. Position Sizing
    if base_action == "buy" and risk_level != "high_risk":
        if risk_level == "low_risk":
            position_size = max_position  # Full position for low risk
        else:
            position_size = max_position * 0.5  # Half position for medium risk
    else:
        position_size = 0  # No position for high risk or bearish signals
        
    # 4. Final Decision
    current_price = float(pair_info["priceUsd"])
    
    if base_action == "buy" and position_size > 0:
        decision["action"] = "buy"
        decision["size"] = position_size
        decision["price"] = current_price
    elif base_action == "sell":
        decision["action"] = "sell"
        decision["size"] = position_size  # Will be 0 as we're selling
        decision["price"] = current_price
    else:
        decision["action"] = "hold"
        decision["size"] = 0
        decision["price"] = current_price
        
    decision["reasoning"]["final_decision"] = {
        "action": decision["action"],
        "size": f"${decision['size']:,.2f}",
        "price": f"${decision['price']:.4f}",
        "explanation": f"Based on {'bullish' if weighted_score > 0 else 'bearish' if weighted_score < 0 else 'neutral'} weighted consensus ({weighted_score:.2f}) and {risk_level} risk assessment"
    }
    
    if show_reasoning:
        print("\nPortfolio Decision:")
        print(json.dumps(decision["reasoning"], indent=2))
        
    # Update state
    state["decision"] = decision
    
    return state