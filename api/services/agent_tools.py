from datetime import datetime
import os
import shutil
from api.helpers.aws_billing import get_aws_billing, get_s3_bucket
from api.helpers.gcp_billing import get_billing, get_services_in_use
from knowlegde.update_embedding import UpdateEmbedding
from knowlegde.agent import Chat
from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, status, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

class StartTime(BaseModel):
    start_time: str = Field(examples="YYYY-MM-DD")
    class Config:
        schema_json_config = {
            "start_time": "2025/04/01"
        }

router = APIRouter(
    prefix="/api/v1"
)
update_embedding = UpdateEmbedding()
@router.websocket("/chat/ws")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()
    chat_bot = Chat(customer_name="Lê Bình")

    try:
        while True:
            data = await websocket.receive_text()
            await chat_bot.chat(data, websocket)

    except WebSocketDisconnect:
        print("Client đã ngắt kết nối.")

@router.get("/ping")
async def get_software():
    return JSONResponse(status_code=status.HTTP_200_OK, content = {"message": "pong"})

@router.get("/document")
async def get_software():
    data = update_embedding.get_all()
    response = {
        "total_item": len(data),
        "data": data
    }
    return JSONResponse(status_code=status.HTTP_200_OK, content = response)

@router.post("/document")
async def post_document(file: UploadFile = File(...)):
    # Tên file tạm
    file_location = f"document/{file.filename}"
    os.makedirs("document", exist_ok=True)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    document_url = update_embedding.embedding_file(file_location)
    response = {
        "file_location": file_location,
        "s3_url": document_url
    }
    return JSONResponse(status_code=status.HTTP_200_OK, content = response)

@router.delete("/document/{id}")
async def post_document(id: int):
    update_embedding.delete_record(id)
    return JSONResponse(status_code=status.HTTP_200_OK, content = {"message": "success"})

@router.get("/aws/s3/bucket")
async def get_s3_bucket_api():
    return JSONResponse(status_code=status.HTTP_200_OK, content = {"data": get_s3_bucket()})

@router.get("/aws/billing")
async def get_aws_billing_api(item: StartTime):
    try:
        time = datetime.strptime(item.start_time, "%Y-%m-%d")
    except:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content = {"message": "Valid format is: yyyy-MM-dd."})
    return JSONResponse(status_code=status.HTTP_200_OK, content = {"data": get_aws_billing(item.start_time)})

@router.get("/gcp/services")
async def get_gcp_services_api():
    return JSONResponse(status_code=status.HTTP_200_OK, content = {"data": get_services_in_use()})

@router.get("/gcp/billing")
async def get_gcp_billing(item: StartTime):
    try:
        time = datetime.strptime(item.start_time, "%Y-%m-%d")
    except:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content = {"message": "Valid format is: yyyy-MM-dd."})
    return JSONResponse(status_code=status.HTTP_200_OK, content = {"data": get_billing(item.start_time)})
