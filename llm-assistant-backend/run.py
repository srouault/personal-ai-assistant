import uvicorn
from dotenv import load_dotenv
import os

if __name__ == "__main__":
    load_dotenv()
    
    os.environ["MODEL_PATH"] = "app/models/Qwen2-7B-Instruct.Q5_K_M.gguf"

    uvicorn.run(
        "app.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8080)),
        reload=True
    ) 