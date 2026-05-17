import os
import json
import uuid
import firebase_admin
from firebase_admin import credentials, firestore, auth
from azure.storage.blob import BlobServiceClient
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

AZURE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
AZURE_CONTAINER_NAME = os.environ.get('AZURE_CONTAINER_NAME', 'fotos-produtos')

def inicializar_firebase_se_necessario():
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
            except Exception as e:
                print(f"Erro no Firebase: {e}")
        else:
            try:
                cred = credentials.Certificate('firebase-sdk.json')
                firebase_admin.initialize_app(cred)
            except Exception as e:
                print(f"Erro no Firebase: {e}")

class ProdutoListarView(APIView):
    def get(self, request):
        inicializar_firebase_se_necessario()
        db = firestore.client()
        categoria_query = request.query_params.get('categoria')
        produtos_ref = db.collection('produtos')
        if categoria_query:
            produtos_ref = produtos_ref.where('categoria', '==', categoria_query)
        docs = produtos_ref.stream()
        lista_produtos = [dict(doc.to_dict(), id=doc.id) for doc in docs]
        return Response(lista_produtos)

class ProdutoCreateView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def post(self, request):
        inicializar_firebase_se_necessario()
        db = firestore.client()
        data = request.data
        try:
            nome = data.get('nome')
            if not nome:
                return Response({"erro": "Nome do produto é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
            
            categoria = data.get('categoria')
            if not categoria:
                return Response({"erro": "Categoria é obrigatória"}, status=status.HTTP_400_BAD_REQUEST)

            imagem_arquivo = request.FILES.get('imagem') 
            url_final = data.get('imagem_url', '') 

            if imagem_arquivo:
                try:
                    extensao = os.path.splitext(imagem_arquivo.name)[1]
                    nome_blob = f"{uuid.uuid4()}{extensao}"
                    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
                    blob_client = blob_service_client.get_blob_client(container=AZURE_CONTAINER_NAME, blob=nome_blob)
                    blob_client.upload_blob(imagem_arquivo, overwrite=True)
                    url_final = blob_client.url
                except Exception as e:
                    return Response({"erro": f"Erro upload Azure: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                preco = float(data.get('preco', 0))
                estoque = int(data.get('estoque', 0))
            except (ValueError, TypeError):
                preco = 0
                estoque = 0

            dados_produto = {
                'nome': nome,
                'marca': data.get('marca', 'Genérico'),
                'preco': preco,
                'estoque': estoque,
                'categoria': categoria,
                'descricao': data.get('descricao', ''),
                'imagem_url': url_final,
                'tags': data.get('tags', []), 
                'data_cadastro': firestore.SERVER_TIMESTAMP
            }

            _, novo_doc = db.collection('produtos').add(dados_produto)
            return Response({"id": novo_doc.id, "msg": "Produto salvo com sucesso!"}, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({"erro": f"Erro interno: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class RegistroUsuarioView(APIView):
    def post(self, request):
        data = request.data
        try:
            user = auth.create_user(
                email=data.get('email'),
                password=data.get('senha')
            )
            db = firestore.client()
            db.collection('usuarios').document(user.uid).set({
                'nome': data.get('nome'),
                'tipo': 'cliente'
            })
            return Response({"uid": user.uid, "msg": "Usuário criado com sucesso!"})
        except Exception as e:
            return Response({"erro": str(e)}, status=400)

import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class LoginUsuarioView(APIView):
    def post(self, request):
        email = request.data.get('email')
        senha = request.data.get('senha')

        if not email or not senha:
            return Response({"erro": "E-mail e senha são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST)

        firebase_web_api_key = "AIzaSyBX_rii0Q-A7bV0N3iuiVyfBBb9GcZHaNk"
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={firebase_web_api_key}"

        payload = {
            "email": email,
            "password": senha,
            "returnSecureToken": True
        }

        try:
            response = requests.post(url, json=payload)
            res_data = response.json()

            if response.status_code == 200:
                return Response({
                    "msg": "Login bem-sucedido",
                    "idToken": res_data.get("idToken"), # Token de autenticação
                    "localId": res_data.get("localId"), # UID do usuário no Firebase
                    "email": res_data.get("email")
                }, status=status.HTTP_200_OK)
            else:
                erro_message = res_data.get('error', {}).get('message', 'Erro ao autenticar.')
                
                if erro_message == "INVALID_LOGIN_CREDENTIALS" or erro_message == "EMAIL_NOT_FOUND" or erro_message == "INVALID_PASSWORD":
                    erro_message = "E-mail ou senha incorretos."

                return Response({"erro": erro_message}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"erro": f"Erro interno no servidor: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)