from pathlib import Path
from typing import Annotated
import urllib.parse

from fastapi import FastAPI, File, Form, Query, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Sentube API")

# Menentukan root directory proyek (folder 'sentube')
BASE_DIR = Path(__file__).resolve().parent.parent

# Setup static files & templates agar path selalu tepat
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# -------------------------------------------------------------------
# 1. Main Page Route
# -------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Menampilkan halaman utama Sentube."""
    return templates.TemplateResponse("index.html", {"request": request})


# -------------------------------------------------------------------
# 2. Form Handlers (Mereturn fragment loading.html)
# -------------------------------------------------------------------
@app.post("/analyze/youtube", response_class=HTMLResponse)
async def analyze_youtube(
    request: Request,
    keyword: Annotated[str, Form()]
):
    """Menerima input keyword/URL dari form YouTube."""
    return templates.TemplateResponse(
        "fragments/loading.html",
        {
            "request": request,
            "source": "youtube",
            "query": keyword
        }
    )


@app.post("/analyze/csv", response_class=HTMLResponse)
async def analyze_csv(
    request: Request,
    file: Annotated[UploadFile, File()]
):
    """Menerima upload file CSV."""
    filename = file.filename or "uploaded_data.csv"

    # Nanti file bisa disimpan sementara ke data/uploads/ menggunakan BASE_DIR / "data" / "uploads"
    
    return templates.TemplateResponse(
        "fragments/loading.html",
        {
            "request": request,
            "source": "csv",
            "query": filename
        }
    )


# -------------------------------------------------------------------
# 3. Async Execution & Results Route (Mereturn fragment result.html)
# -------------------------------------------------------------------
@app.get("/results", response_class=HTMLResponse)
async def get_results(
    request: Request,
    source: str = Query(...),
    query: str = Query(...)
):
    """Mengembalikan fragment 'result.html' beserta data hasil analisis."""
    decoded_query = urllib.parse.unquote(query)

    # TODO: Panggil fungsi dari app.ml_pipeline atau app.services di sini
    mock_results = {
        "summary": {
            "positive": 68,
            "neutral": 20,
            "negative": 12
        },
        "top_features": [
            "bagus", "keren", "membantu", "mantap", "penjelasan", 
            "paham", "terima kasih", "cepat", "mudah", "tutorial"
        ],
        "sample_comments": [
            {
                "text": f"Penjelasan mengenai '{decoded_query}' ini sangat jelas dan mudah dipahami!",
                "sentiment": "Positive"
            },
            {
                "text": "Materi lumayan oke, tapi suara mic agak kurang kencang.",
                "sentiment": "Neutral"
            },
            {
                "text": "Kurang paham di bagian konfigurasi pertamanya, terlalu cepat.",
                "sentiment": "Negative"
            }
        ]
    }

    return templates.TemplateResponse(
        "fragments/result.html",
        {
            "request": request,
            "source": source,
            "query": decoded_query,
            "results": mock_results
        }
    )