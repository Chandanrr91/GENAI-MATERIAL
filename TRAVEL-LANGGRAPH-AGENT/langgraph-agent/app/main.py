from fastapi import FastAPI, Body, HTTPException
from app.graph import graph
from app.config import logger

app = FastAPI(title="Travel Agent API")

@app.post("/chat")
async def chat(payload: dict = Body(...)):
    thread_id = payload.get("thread_id", "session_1")
    config = {"configurable": {"thread_id": thread_id}}
    action = payload.get("action")
    data = payload.get("data", {})

    logger.info(f"REQUEST | Action: {action} | Thread: {thread_id}")

    try:
        if action == "start":
            graph.invoke(data, config)
        
        elif action == "select_prices":
            graph.update_state(config, data)
            graph.invoke(None, config)

        elif action == "fix_budget":
            graph.update_state(config, data)
            graph.update_state(config, {}, as_node="supervisor")
            graph.invoke(None, config)
            
        else:
            raise HTTPException(status_code=400, detail="Invalid action provided")

        final_state = graph.get_state(config).values
        logger.info(f"SUCCESS | Thread: {thread_id} | State: {final_state.get('remaining_budget')}")
        return final_state

    except Exception as e:
        logger.error(f"FATAL ERROR | Thread: {thread_id} | Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error during Graph Execution")

@app.get("/health")
def health():
    return {"status": "healthy"}