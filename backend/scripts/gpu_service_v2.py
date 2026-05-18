"""GPU Service v2 — SDXL + CogVideoX API for ops-video."""
import io, os, sys, time, json
import torch
from PIL import Image
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn
from pydantic import BaseModel

app = FastAPI(title="ops-video GPU Service v2")

SDXL_PATH = os.environ.get("SDXL_MODEL_PATH", "/data/yingtie/ComfyUI/models/checkpoints/sd_xl_base_1.0.safetensors")
COG_MODEL = os.environ.get("COGVIDEO_MODEL", "THUDM/CogVideoX-5b-I2V")
COG_CACHE = os.environ.get("COGVIDEO_CACHE", "/data/yingtie/models")
OUTPUT_DIR = os.environ.get("GPU_OUTPUT_DIR", "/tmp/gpu_output")

sdxl_pipe = None
cog_pipe = None

class ImageReq(BaseModel):
    prompt: str = "anime storyboard panel"
    negative_prompt: str = "blurry, low quality"
    width: int = 1024; height: int = 1024
    steps: int = 25; cfg_scale: float = 7.0; seed: int = -1

class VideoReq(BaseModel):
    image_path: str = ""
    image_url: str = ""
    prompt: str = "cinematic, smooth motion"
    steps: int = 50; seed: int = -1

def load_sdxl():
    global sdxl_pipe
    if sdxl_pipe: return
    from diffusers import StableDiffusionXLPipeline
    sdxl_pipe = StableDiffusionXLPipeline.from_single_file(SDXL_PATH, torch_dtype=torch.float16, use_safetensors=True)
    sdxl_pipe.to("cuda")
    sdxl_pipe.enable_attention_slicing()

def load_cog():
    global cog_pipe
    if cog_pipe: return
    from diffusers import CogVideoXImageToVideoPipeline
    cog_pipe = CogVideoXImageToVideoPipeline.from_pretrained(COG_MODEL, torch_dtype=torch.bfloat16, cache_dir=COG_CACHE)
    cog_pipe.to("cuda")
    cog_pipe.enable_attention_slicing()

@app.on_event("startup")
async def startup():
    load_sdxl()
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

@app.get("/health")
def health():
    return {"sdxl": sdxl_pipe is not None, "cog": cog_pipe is not None}

@app.post("/generate/image")
async def gen_image(req: ImageReq):
    if not sdxl_pipe:
        raise HTTPException(503, "SDXL not loaded")
    g = torch.Generator("cuda").manual_seed(req.seed) if req.seed >= 0 else None
    result = sdxl_pipe(
        prompt=req.prompt, negative_prompt=req.negative_prompt,
        width=req.width, height=req.height,
        num_inference_steps=req.steps, guidance_scale=req.cfg_scale, generator=g,
    )
    buf = io.BytesIO()
    result.images[0].save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

@app.post("/generate/video")
async def gen_video(req: VideoReq):
    if not cog_pipe:
        raise HTTPException(503, "CogVideoX not loaded")
    import httpx
    img = None
    if req.image_path and os.path.exists(req.image_path):
        img = Image.open(req.image_path).convert("RGB")
    elif req.image_url:
        r = httpx.get(req.image_url, timeout=30)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
    else:
        img = Image.new("RGB", (720, 480), (100, 100, 150))

    g = torch.Generator("cuda").manual_seed(req.seed) if req.seed >= 0 else None
    frames = cog_pipe(
        image=img, prompt=req.prompt,
        num_inference_steps=req.steps, generator=g,
        guidance_scale=3.5, use_dynamic_cfg=True,
    ).frames[0]

    ts = int(time.time())
    out_path = f"{OUTPUT_DIR}/cogvideo_{ts}.mp4"
    from diffusers.utils import export_to_video
    export_to_video(frames, out_path, fps=8)

    return StreamingResponse(open(out_path, "rb"), media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename=cogvideo_{ts}.mp4"})

if __name__ == "__main__":
    load_cog = "--load-cog" in sys.argv
    port = 8199
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])
    print(f"GPU service starting on port {port}, SDXL={True}, CogVideoX={load_cog}")
    if load_cog:
        print("Loading CogVideoX...")
        load_cog()
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
