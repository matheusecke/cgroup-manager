from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List
import logging

import database as db
from environments import EnvironmentManager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar banco de dados
db.init_db()

# Criar app FastAPI
app = FastAPI(
    title="CGroup Manager",
    description="Gerenciador de ambientes isolados com cgroups e namespaces",
    version="1.0.0"
)

# Inicializar gerenciador de ambientes
env_manager = EnvironmentManager()

# Modelos Pydantic para validação
class EnvironmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    cpu_limit: float = Field(..., gt=0, le=2.0)
    memory_mb: int = Field(..., gt=0, le=4096)
    io_weight: int = Field(500, ge=100, le=1000)
    script_content: str = Field(..., min_length=1)

class EnvironmentResponse(BaseModel):
    id: int
    name: str
    status: str
    cpu_limit: float
    memory_mb: int
    io_weight: int
    script_content: str
    created_at: str
    process_id: int = None

class LogsResponse(BaseModel):
    env_id: int
    logs: str

# Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Servir interface HTML"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>CGroup Manager</h1><p>Interface não encontrada. Verifique os arquivos estáticos.</p>"

@app.post("/api/environments", response_model=EnvironmentResponse)
async def create_environment(env_data: EnvironmentCreate):
    """Criar novo ambiente de execução"""
    try:
        # Inserir no banco primeiro (gera id automaticamente)
        env_id = db.insert_environment(
            name=env_data.name,
            cpu_limit=env_data.cpu_limit,
            memory_mb=env_data.memory_mb,
            io_weight=env_data.io_weight,
            script_content=env_data.script_content,
            process_id=None
        )
        
        logger.info(f"Criando ambiente #{env_id}: {env_data.name}")
        
        # Criar e executar ambiente
        result = env_manager.create_environment(
            env_id=env_id,
            name=env_data.name,
            cpu_limit=env_data.cpu_limit,
            memory_mb=env_data.memory_mb,
            io_weight=env_data.io_weight,
            script_content=env_data.script_content
        )
        
        # Atualizar PID no banco
        db.update_process_id(env_id, result['pid'])
        
        logger.info(f"Ambiente #{env_id} criado com sucesso (PID: {result['pid']})")
        
        # Retornar ambiente criado
        return db.get_environment(env_id)
        
    except Exception as e:
        logger.error(f"Erro ao criar ambiente: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar ambiente: {str(e)}")

@app.get("/api/environments", response_model=List[EnvironmentResponse])
async def list_environments():
    """Listar todos os ambientes"""
    try:
        environments = db.get_all_environments()
        
        # Atualizar status de cada ambiente
        for env in environments:
            current_status = env_manager.get_status(env['id'])
            if env['status'] != current_status:
                db.update_status(env['id'], current_status)
                env['status'] = current_status
        
        return environments
        
    except Exception as e:
        logger.error(f"Erro ao listar ambientes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar ambientes: {str(e)}")

@app.get("/api/environments/{env_id}", response_model=EnvironmentResponse)
async def get_environment(env_id: int):
    """Obter detalhes de um ambiente específico"""
    try:
        env = db.get_environment(env_id)
        
        if not env:
            raise HTTPException(status_code=404, detail="Ambiente não encontrado")
        
        # Atualizar status
        current_status = env_manager.get_status(env_id)
        if env['status'] != current_status:
            db.update_status(env_id, current_status)
            env['status'] = current_status
        
        return env
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter ambiente: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter ambiente: {str(e)}")

@app.get("/api/environments/{env_id}/logs", response_model=LogsResponse)
async def get_logs(env_id: int):
    """Obter logs de execução do ambiente"""
    try:
        env = db.get_environment(env_id)
        
        if not env:
            raise HTTPException(status_code=404, detail="Ambiente não encontrado")
        
        logs = env_manager.get_logs(env_id)
        
        return {
            "env_id": int(env_id),
            "logs": logs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter logs: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter logs: {str(e)}")

@app.post("/api/environments/{env_id}/stop")
async def stop_environment(env_id: int):
    """Parar execução de um ambiente"""
    try:
        env = db.get_environment(env_id)
        
        if not env:
            raise HTTPException(status_code=404, detail="Ambiente não encontrado")
        
        success = env_manager.stop_environment(env_id)
        
        if success:
            db.update_status(env_id, "EXITED")
            logger.info(f"Ambiente #{env_id} parado")
            return {"message": "Ambiente parado com sucesso", "status": "EXITED"}
        else:
            raise HTTPException(status_code=500, detail="Erro ao parar ambiente")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao parar ambiente: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao parar ambiente: {str(e)}")

@app.delete("/api/environments/{env_id}")
async def delete_environment(env_id: int):
    """Remover ambiente completamente"""
    try:
        env = db.get_environment(env_id)
        
        if not env:
            raise HTTPException(status_code=404, detail="Ambiente não encontrado")
        
        # Remover do sistema
        env_manager.remove_environment(env_id)
        
        # Remover do banco
        db.delete_environment(env_id)
        
        logger.info(f"Ambiente #{env_id} removido")
        
        return {"message": "Ambiente removido com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover ambiente: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao remover ambiente: {str(e)}")

@app.get("/health")
async def health():
    """Health check da aplicação"""
    return {
        "status": "healthy",
        "cgroups": "enabled",
        "database": "connected"
    }

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")


