import logging

from fastapi import FastAPI
# packages
from api.middlewares.global_catch import catch_exceptions_middleware
from api.services.agent_tools import router
from fastapi.middleware.cors import CORSMiddleware
# settings


# init application
app = FastAPI(
    title = 'TIMS CHATBOT',
    description = "This API was built with FastAPI. Plugin/module in TIMS that supported about auto answer any questions of employees.",
    version = "1.0.0",
)
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware('http')(catch_exceptions_middleware)


app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
    