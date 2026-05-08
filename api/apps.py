def ready(self):
        import json
        if not firebase_admin._apps:
            try:
                # 1. Tenta pegar da variável de ambiente (Azure)
                firebase_json = os.environ.get('FIREBASE_CONFIG')
                
                if firebase_json:
                    cred_dict = json.loads(firebase_json)
                    cred = credentials.Certificate(cred_dict)
                else:
                    # 2. Se não tiver a variável, tenta o arquivo local (Seu PC)
                    file_name = 'firebase-sdk.json'
                    cred_path = os.path.join(settings.BASE_DIR, file_name)
                    cred = credentials.Certificate(cred_path)

                firebase_admin.initialize_app(cred)
                print("✅ [Firebase] Conectado com sucesso!")
            except Exception as e:
                print(f"❌ [Firebase] Erro ao conectar: {e}")