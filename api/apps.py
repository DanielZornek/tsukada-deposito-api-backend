import os
import firebase_admin
from firebase_admin import credentials
from django.apps import AppConfig
from django.conf import settings

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # Nome exato do arquivo que você colocou na pasta do manage.py
        file_name = 'firebase-sdk.json' 
        cred_path = os.path.join(settings.BASE_DIR, file_name)
        
        # Inicializa o Firebase apenas uma vez
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("✅ [Firebase] Conectado com sucesso à Tsukada API!")
            except Exception as e:
                print(f"❌ [Firebase] Erro ao conectar: {e}")