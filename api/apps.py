import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Função de segurança para garantir que o Firebase está ligado
def inicializar_firebase_se_necessario():
    if not firebase_admin._apps:
        # Tenta pegar da Azure
        firebase_json = os.environ.get('FIREBASE_CONFIG')
        if firebase_json:
            try:
                cred = credentials.Certificate(json.loads(firebase_json))
                firebase_admin.initialize_app(cred)
            except:
                pass 
        else:
            try:
                firebase_admin.initialize_app()
            except:
                pass