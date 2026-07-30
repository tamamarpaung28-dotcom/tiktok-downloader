import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import uvicorn

app = FastAPI()

# PENTING: CORS harus diizinkan untuk semua HTTP Method termasuk OPTIONS (Preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str
    format_type: str  # "video" atau "audio"

# Disesuaikan ke /info (tanpa /api) sesuai dengan request dari Frontend Netlify
@app.post("/info")
async def get_tiktok_info(request: DownloadRequest):
    url = request.url.strip()

    if "tiktok.com" not in url:
        raise HTTPException(status_code=400, detail="Masukkan link TikTok yang valid!")

    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        try:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            res = await client.get(api_url)
            data = res.json()

            if data.get("code") == 0:
                video_data = data.get("data", {})
                
                if request.format_type == "audio":
                    download_link = video_data.get("music")
                else:
                    download_link = video_data.get("play")
                
                if download_link and not download_link.startswith("http"):
                    download_link = "https://www.tikwm.com" + download_link

                if not download_link:
                    raise HTTPException(status_code=400, detail="Format media tidak ditemukan pada video ini.")

                return {
                    "status": "success",
                    "title": video_data.get("title", "TikTok Media"),
                    "thumbnail": video_data.get("cover"),
                    "download_url": download_link,
                    "type": request.format_type
                }
            else:
                raise HTTPException(status_code=400, detail="Gagal mengambil video TikTok. Pastikan akun/video tidak privat!")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Terjadi kesalahan: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
