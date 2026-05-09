import os
import json
import firebase_admin
from firebase_admin import credentials
from django.apps import AppConfig

def carregar_firebase():
    if not firebase_admin._apps:
        config_raw = os.environ.get('FIREBASE_CONFIG')
        
        if config_raw:
            try:
                if "\\n" in config_raw:
                    config_raw = config_raw.replace("\\n", "\n")
                
                cred_dict = json.loads(config_raw, strict=False)
                
                if 'private_key' in cred_dict:
                    cred_dict['private_key'] = cred_dict['private_key'].replace("\\n", "\n")
                
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                print("✅ Firebase conectado via Variável!")
            except Exception as e:
                print(f"❌ Erro ao processar JSON: {e}")
        else:
            cred = credentials.Certificate('firebase-sdk.json')
            firebase_admin.initialize_app(cred)

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        carregar_firebase()