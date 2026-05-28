from pydantic import BaseModel
from typing import Optional

class SiniestroResponse(BaseModel):
    id_siniestro: str
    cobertura: str
    monto_reclamado: float
    score_riesgo: int
    nivel_riesgo: str
    explicacion_ia: Optional[str] = None
