from fastapi import FastAPI

app = FastAPI(title='ReasonScore AI API')

@app.get('/')
def root():
    return {'status': 'ok'}
