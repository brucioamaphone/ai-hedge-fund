from dotenv import load_dotenv
import os
import json

# Load environment variables from .env file
load_dotenv()

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from agents.fundamentals import fundamentals_agent
from agents.market_data import market_data_agent
from agents.portfolio_manager import portfolio_management_agent
from agents.technicals import technical_analyst_agent
from agents.risk_manager import risk_management_agent
from agents.sentiment import sentiment_agent
from agents.state import AgentState
from agents.valuation import valuation_agent
from tools.influx_writer import InfluxWriter

import argparse
from datetime import datetime


##### Run the Hedge Fund #####
def run_hedge_fund(token_address: str, chain_id: str = None, start_date: str = None, end_date: str = None, portfolio: dict = None, show_reasoning: bool = False):
    """
    Run the AI Hedge Fund with multiple agents analyzing crypto markets
    
    Args:
        token_address: The token's contract address
        chain_id: Optional chain ID to filter specific blockchain
        start_date: Optional start date for analysis
        end_date: Optional end date for analysis
        portfolio: Optional current portfolio state
        show_reasoning: Whether to show agent reasoning
    """
    final_state = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content="Make a trading decision based on the provided data.",
                )
            ],
            "data": {
                "token_address": token_address,
                "chain_id": chain_id,
                "portfolio": portfolio,
                "start_date": start_date,
                "end_date": end_date,
            },
            "metadata": {
                "show_reasoning": show_reasoning,
            }
        },
    )
    
    # Get the final result
    result = final_state["messages"][-1].content
    
    try:
        # Parse the result string into a dictionary
        result_data = json.loads(result)
        
        # Initialize InfluxDB writer
        writer = InfluxWriter()
        
        # Write data to InfluxDB
        if "market_data" in result_data:
            writer.write_market_data(token_address, chain_id, result_data["market_data"])
        if "valuation_analysis" in result_data:
            writer.write_valuation_metrics(token_address, chain_id, result_data["valuation_analysis"])
        if "risk_analysis" in result_data:
            writer.write_risk_metrics(token_address, chain_id, result_data["risk_analysis"])
        if "portfolio_decision" in result_data:
            writer.write_trading_decision(token_address, chain_id, result_data["portfolio_decision"])
            
        writer.close()
        
    except json.JSONDecodeError:
        print("Warning: Could not parse result as JSON for InfluxDB storage")
    except Exception as e:
        print(f"Warning: Failed to write to InfluxDB: {str(e)}")
    
    return result

# Define the new workflow
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("market_data_agent", market_data_agent)
workflow.add_node("technical_analyst_agent", technical_analyst_agent)
workflow.add_node("fundamentals_agent", fundamentals_agent)
workflow.add_node("sentiment_agent", sentiment_agent)
workflow.add_node("risk_management_agent", risk_management_agent)
workflow.add_node("portfolio_management_agent", portfolio_management_agent)
workflow.add_node("valuation_agent", valuation_agent)

# Define the workflow
workflow.set_entry_point("market_data_agent")
workflow.add_edge("market_data_agent", "technical_analyst_agent")
workflow.add_edge("market_data_agent", "fundamentals_agent")
workflow.add_edge("market_data_agent", "sentiment_agent")
workflow.add_edge("market_data_agent", "valuation_agent")
workflow.add_edge("technical_analyst_agent", "risk_management_agent")
workflow.add_edge("fundamentals_agent", "risk_management_agent")
workflow.add_edge("sentiment_agent", "risk_management_agent")
workflow.add_edge("valuation_agent", "risk_management_agent")
workflow.add_edge("risk_management_agent", "portfolio_management_agent")
workflow.add_edge("portfolio_management_agent", END)

app = workflow.compile()

# Add this at the bottom of the file
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the hedge fund trading system')
    parser.add_argument('--token-address', type=str, required=True, help='Token contract address')
    parser.add_argument('--chain-id', type=str, help='Chain ID to filter specific blockchain')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD). Defaults to 3 months before end date')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD). Defaults to today')
    parser.add_argument('--show-reasoning', action='store_true', help='Show reasoning from each agent')
    
    args = parser.parse_args()
    
    # Validate dates if provided
    if args.start_date:
        try:
            datetime.strptime(args.start_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Start date must be in YYYY-MM-DD format")
    
    if args.end_date:
        try:
            datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("End date must be in YYYY-MM-DD format")
    
    # Sample portfolio - you might want to make this configurable too
    portfolio = {
        "cash": 100000.0,  # $100,000 initial cash
        "token": 0         # No initial token position
    }
    
    result = run_hedge_fund(
        token_address=args.token_address,
        chain_id=args.chain_id,
        start_date=args.start_date,
        end_date=args.end_date,
        portfolio=portfolio,
        show_reasoning=args.show_reasoning
    )
    print("\nFinal Result:")
    print(result)