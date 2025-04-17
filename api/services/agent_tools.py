import os
import shutil
from knowlegde.update_embedding import UpdateEmbedding
from knowlegde.agent import Chat
from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, status, File, UploadFile
from fastapi.responses import JSONResponse
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

