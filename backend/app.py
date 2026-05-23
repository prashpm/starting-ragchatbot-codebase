import warnings
warnings.filterwarnings("ignore", message="resource_tracker: There appear to be.*")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os

from config import config
from rag_system import RAGSystem


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    session_id: str

class CourseStats(BaseModel):
    total_courses: int
    course_titles: List[str]


class DevStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if isinstance(response, FileResponse):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


def create_app(serve_static: bool = True) -> FastAPI:
    application = FastAPI(title="Course Materials RAG System", root_path="")

    application.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    rag_system = RAGSystem(config)

    @application.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = rag_system.session_manager.create_session()
            answer, sources = rag_system.query(request.query, session_id)
            return QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @application.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @application.on_event("startup")
    async def startup_event():
        docs_path = "../docs"
        if os.path.exists(docs_path):
            print("Loading initial documents...")
            try:
                courses, chunks = rag_system.add_course_folder(docs_path, clear_existing=False)
                print(f"Loaded {courses} courses with {chunks} chunks")
            except Exception as e:
                print(f"Error loading documents: {e}")

    if serve_static and os.path.isdir("../frontend"):
        application.mount("/", DevStaticFiles(directory="../frontend", html=True), name="static")

    return application


app = create_app()