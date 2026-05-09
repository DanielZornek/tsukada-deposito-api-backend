import os
import json
import firebase_admin
import cloudinary.uploader 
from firebase_admin import credentials, firestore, auth
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

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
                return Response({"erro": "Categoria é obrigatória para a inteligência do Chatbot"}, status=status.HTTP_400_BAD_REQUEST)

            imagem_arquivo = request.FILES.get('imagem') 
            url_final = data.get('imagem_url', '') 

            if imagem_arquivo:
                resultado = cloudinary.uploader.upload(imagem_arquivo)
                url_final = resultado['secure_url']

            try:
                preco = float(data.get('preco', 0))
                estoque = int(data.get('estoque', 0))
            except (ValueError, TypeError):
                preco = 0
                estoque = 0

            # Estrutura otimizada para busca e chatbot
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
            
            return Response({
                "id": novo_doc.id, 
                "msg": "Produto salvo com sucesso!"
            }, status=status.HTTP_201_CREATED)
            
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