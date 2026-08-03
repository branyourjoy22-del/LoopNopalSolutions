from fastapi import FastAPI

app = FastAPI(title="Loop Nopal Solutions Traffic API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/simulation/status")
def simulation_status():
    return {
        "project": "LoopNopalSolutions",
        "simulation": "Sombrerete crossing",
        "api": "ready-for-integration",
    }

