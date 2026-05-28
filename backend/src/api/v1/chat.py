from fastapi import APIRouter

router = APIRouter()

@router.post('/')
def chat_query():
    return {'respuesta': 'Hola, soy ReasonScore AI'}
