from app.entities.agent_data import AgentData
from app.entities.processed_agent_data import ProcessedAgentData

def process_agent_data(agent_data: AgentData) -> ProcessedAgentData:
    """
    Process agent data and classify the state of the road surface.
    Parameters:
    agent_data (AgentData): Agent data that contains accelerometer, GPS, and timestamp.
    Returns:
    processed_data (ProcessedAgentData): Processed data containing the classified state of
    the road surface and agent data.
    """
    state= "Bad"

    val = agent_data.accelerometer.x

    if val <= 75:
        state = "Good"
    elif 75 < val <= 150:
        state = "Medium"
    return ProcessedAgentData(road_state=state, agent_data=agent_data)
        