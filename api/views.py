import os
import json
import firebase_admin
import requests
from firebase_admin import credentials, firestore, auth
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser # Aceitamos apenas JSON simples

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
    # Força a API a aceitar apenas JSON puro, resolvendo o erro 415 (Unsupported Media Type)
    parser_classes = (JSONParser,) 

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

            url_final = data.get('imagem_url', '') 

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

    # 🛠️ NOVO MÉTODO: Responsável por atualizar o produto no Firestore da Azure
    def put(self, request, pk=None):
        inicializar_firebase_se_necessario()
        db = firestore.client()
        data = request.data

        if not pk:
            return Response({"erro": "O ID do produto é obrigatório para atualização."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Referência direta ao documento do Firestore usando a string do ID (ex: f3WQYAZyZeoN3vBeU5PZ)
            produto_ref = db.collection('produtos').document(pk)
            
            # Verifica se o produto realmente existe antes de tentar atualizar
            doc = produto_ref.get()
            if not doc.exists:
                return Response({"erro": "Produto não localizado no banco de dados."}, status=status.HTTP_404_NOT_FOUND)

            # Tratamento básico dos tipos de dados numéricos
            try:
                preco = float(data.get('preco', 0))
                estoque = int(data.get('estoque', 0))
            except (ValueError, TypeError):
                preco = doc.to_dict().get('preco', 0)
                estoque = doc.to_dict().get('estoque', 0)

            # Monta o dicionário com os campos atualizados
            dados_atualizados = {
                'nome': data.get('nome', doc.to_dict().get('nome')),
                'marca': data.get('marca', doc.to_dict().get('marca', 'Genérico')),
                'preco': preco,
                'estoque': estoque,
                'categoria': data.get('categoria', doc.to_dict().get('categoria')),
                'descricao': data.get('descricao', doc.to_dict().get('descricao', '')),
                'imagem_url': data.get('imagem_url', doc.to_dict().get('imagem_url', '')),
                'tags': data.get('tags', doc.to_dict().get('tags', [])),
                'data_atualizacao': firestore.SERVER_TIMESTAMP # Registra o momento da edição
            }

            # Executa a atualização parcial ou total no documento do Firestore
            produto_ref.update(dados_atualizados)

            return Response({"id": pk, "msg": "Produto atualizado com sucesso no Firestore!"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"erro": f"Erro ao atualizar no Firestore: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

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
            
            return Response({
                "uid": user.uid, 
                "msg": "Usuário criado com sucesso!"
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                "erro": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

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
                    "idToken": res_data.get("idToken"), 
                    "localId": res_data.get("localId"), 
                    "email": res_data.get("email")
                }, status=status.HTTP_200_OK)
            else:
                erro_message = res_data.get('error', {}).get('message', 'Erro ao autenticar.')
                
                if erro_message in ["INVALID_LOGIN_CREDENTIALS", "EMAIL_NOT_FOUND", "INVALID_PASSWORD"]:
                    erro_message = "E-mail ou senha incorretos."

                return Response({"erro": erro_message}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"erro": f"Erro interno no servidor: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)