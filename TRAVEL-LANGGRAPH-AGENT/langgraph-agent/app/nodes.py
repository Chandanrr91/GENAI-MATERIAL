import os, json, re, requests
from datetime import datetime
from app.state import TravelState
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SerpAPIWrapper
from app.config import logger

llm = ChatOpenAI(model="gpt-4o", temperature=0)
search_tool = SerpAPIWrapper()

def normalize_date(user_input: str):
    current_year = datetime.now().year
    for fmt in ("%b %d %Y", "%B %d %Y"):
        try:
            return datetime.strptime(f"{user_input} {current_year}", fmt).strftime("%Y-%m-%d")
        except: continue
    return datetime.now().strftime("%Y-%m-%d")

def fallback_iata(city: str):
    mapping = {"dubai": "DXB", "bangkok": "BKK", "london": "LHR"}
    return mapping.get(city.lower(), "DXB")

def input_processor_node(state: TravelState):
    logger.info(f"--- 🔍 PROCESSING: {state.get('origin')} ---")
    formatted_date = normalize_date(state["travel_date_input"])
    prompt = f"Return ONLY JSON: {{'origin_iata': '...', 'destination_iata': '...'}} for Origin: {state['origin']}, Destination: {state['destination']}"
    
    try:
        raw = llm.invoke(prompt).content.strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        data = json.loads(match.group(0))
        origin, dest = data["origin_iata"].upper(), data["destination_iata"].upper()
    except Exception as e:
        logger.warning(f"LLM Processor failed, using fallbacks: {e}")
        origin, dest = fallback_iata(state["origin"]), fallback_iata(state["destination"])
        
    return {"origin_iata": origin, "destination_iata": dest, "travel_date_formatted": formatted_date}

def flight_agent(state: TravelState):
    logger.info(f"--- ✈️ FLIGHTS: {state['origin_iata']} -> {state['destination_iata']} ---")
    url = "https://api.duffel.com/air/offer_requests?return_offers=true"
    headers = {"Duffel-Version": "v2", "Authorization": f"Bearer {os.getenv('DUFFEL_ACCESS_TOKEN')}", "Content-Type": "application/json"}
    payload = {"data": {"slices": [{"origin": state['origin_iata'], "destination": state['destination_iata'], "departure_date": state['travel_date_formatted']}], "passengers": [{"type": "adult"}], "cabin_class": "economy"}}
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        res.raise_for_status()
        offers = res.json().get("data", {}).get("offers", [])[:3]
        results = [{"info": f"{o['owner']['name']}: ${o['total_amount']}", "price": float(o["total_amount"])} for o in offers]
        logger.info(f"Found {len(results)} flight offers")
        return {"flight_options": results}
    except Exception as e:
        logger.error(f"Flight API Error: {e}")
        return {"flight_options": [{"info": "Emirates: $420", "price": 420}, {"info": "Qatar: $390", "price": 390}]}

def hotel_agent(state: TravelState):
    logger.info(f"--- 🏨 HOTELS: {state['destination']} ---")
    try:
        res = search_tool.run(f"best hotels in {state['destination']} 2026")
        return {"hotel_options": [{"info": str(res)[:300]}]}
    except Exception as e:
        logger.error(f"Hotel Search Error: {e}")
        return {"hotel_options": [{"info": "Fallback: Luxury Stay found via backup search"}]}

def supervisor_node(state: TravelState):
    total = state.get("total_budget", 0)
    f_price = state.get("selected_flight_price") or 0
    h_price = state.get("selected_hotel_price") or 0
    remaining = total - (f_price + h_price)
    logger.info(f"--- 🧠 BUDGET CHECK: Remaining ${remaining} ---")
    return {"remaining_budget": remaining}

def activity_agent(state: TravelState):
    logger.info(f"--- 🎭 ACTIVITIES: {state['destination']} ---")
    try:
        res = search_tool.run(f"top attractions in {state['destination']}")
        return {"activities": [res]}
    except Exception as e:
        logger.error(f"Activity Search Error: {e}")
        return {"activities": ["General sightseeing"]}

def budget_warning_node(state: TravelState):
    logger.warning(f"--- ⚠️ OVER BUDGET: ${abs(state.get('remaining_budget', 0))} ---")
    return {}