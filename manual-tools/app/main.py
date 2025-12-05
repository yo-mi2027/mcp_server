from __future__ import annotations
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import load_settings
from app.repositories.manual import ManualRepository
from app.routers.manuals import router as manuals_router

def create_app() -> FastAPI:
    settings = load_settings()

    logging.basicConfig(
        level=getattr(logging, settings.logging.level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    app = FastAPI(title="manual-tools", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1", "http://localhost"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ルーター登録（Depends(get_repo) を各エンドポイントで使用）
    app.include_router(manuals_router)

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    # 起動時：relaxed 検証（致命的例外のみ停止）
    @app.on_event("startup")
    def on_startup():
        repo = ManualRepository(settings)
        manuals = repo.list_manuals()
        logging.getLogger(__name__).info(f"Found manuals: {manuals}")
        for m in manuals:
            try:
                _ = repo.load_toc(m)
                logging.getLogger(__name__).info(f"validated(manual={m})")
            except Exception as e:
                logging.getLogger(__name__).exception(f"failed to load toc: {m}: {e}")
                raise

    return app

app = create_app()
