from config import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
)

from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    DateTime,
)

from pydantic import BaseModel, field_validator, ValidationError, validator
from datetime import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Body
from typing import Set, Dict, List, Any
import json
from sqlalchemy.sql import select, insert, delete, update
from sqlalchemy.orm import sessionmaker



# FastAPI app setup
app = FastAPI()
# SQLAlchemy setup
DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(DATABASE_URL)
metadata = MetaData()


# Define the ProcessedAgentData table
processed_agent_data = Table(
    "processed_agent_data",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("road_state", String),
    Column("user_id", Integer),
    Column("x", Float),
    Column("y", Float),
    Column("z", Float),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("timestamp", DateTime),
    schema="public", 
)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# SQLAlchemy model
class ProcessedAgentDataInDB(BaseModel):
    id: int
    road_state: str
    user_id: int
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime


# FastAPI models
class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float


class GpsData(BaseModel):
    latitude: float
    longitude: float


class AgentData(BaseModel):
    user_id: int
    accelerometer: AccelerometerData
    gps: GpsData
    timestamp: datetime

    @classmethod
    @field_validator("timestamp", mode="before")
    def check_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError(
                "Invalid timestamp format. Expected ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)."
            )


class ProcessedAgentData(BaseModel):
    road_state: str
    agent_data: AgentData


# WebSocket subscriptions
subscriptions: Dict[int, Set[WebSocket]] = {}


# FastAPI WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    if user_id not in subscriptions:
        subscriptions[user_id] = set()
    subscriptions[user_id].add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        subscriptions[user_id].remove(websocket)


# Function to send data to subscribed users
async def send_data_to_subscribers(user_id: int, data):
    if user_id in subscriptions:
        for websocket in subscriptions[user_id]:
            await websocket.send_json(json.dumps(data))

# FastAPI CRUDL endpoints
@app.post("/processed_agent_data/")
async def create_processed_agent_data(data:List[ProcessedAgentData]):
  try:
        for item in data:
            query =insert( processed_agent_data).values(
                user_id = item.agent_data.user_id,
                road_state=item.road_state,
                x= item.agent_data.accelerometer.x,
                y = item.agent_data.accelerometer.y,
                z = item.agent_data.accelerometer.z,
                latitude = item.agent_data.gps.latitude,
                longitude = item.agent_data.gps.longitude,
                timestamp = item.agent_data.timestamp,
            )
            data = session.execute(query)
            result = await send_data_to_subscribers(item.agent_data.user_id, item.json())
            session.commit()
            return result
  except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e.errors()))
# Insert data to database
# Send data to subscribers
@app.get( "/processed_agent_data/{processed_agent_data_id}",  response_model=ProcessedAgentDataInDB)
async def read_processed_agent_data(processed_agent_data_id: int):
  try:
    query = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
    data =  session.execute(query).fetchone()
    return data
  except ValidationError as e:
    raise HTTPException(status_code=422, detail=str(e.errors()))


@app.get("/processed_agent_data/", response_model=List[ProcessedAgentDataInDB])
def list_processed_agent_data():
    try:
        query = select(processed_agent_data)
        data = session.execute(query).fetchall()
        return data
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e.errors()))


@app.put("/processed_agent_data/{processed_agent_data_id}",response_model=ProcessedAgentDataInDB)
def update_processed_agent_data(processed_agent_data_id: int,data: ProcessedAgentData):
  try:
    query1 = (
              update(processed_agent_data)
              .where(processed_agent_data.c.id == processed_agent_data_id)
              .values(
                      user_id = data.agent_data.user_id,
                      road_state = data.road_state,
                      x = data.agent_data.accelerometer.x,
                      y = data.agent_data.accelerometer.y,
                      z = data.agent_data.accelerometer.z,
                      latitude = data.agent_data.gps.latitude,
                      longitude =  data.agent_data.gps.longitude,
                      timestamp =  data.agent_data.timestamp,
              )
          )
    data = session.execute(query1)
    session.commit()
    query = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
    data =  session.execute(query).fetchone()
    return data
  except ValidationError as e:
    raise HTTPException(status_code=422, detail=str(e.errors()))

# Update data
@app.delete("/processed_agent_data/{processed_agent_data_id}",response_model=ProcessedAgentDataInDB)
def delete_processed_agent_data(processed_agent_data_id: int):
  try:
    query = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
    data =  session.execute(query).fetchone()
    query1 = delete(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
    session.execute(query1)
    session.commit()
    return data
  except ValidationError as e:
    raise HTTPException(status_code=422, detail=str(e.errors()))
# Delete by id
  
if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="127.0.0.1", port=8000)