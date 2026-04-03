from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from firebase_admin import firestore
import cloudinary.uploader  
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

# VIEW 1: APENAS LISTAR (Leitura)
class ProdutoListarView(APIView):
    def get(self, request):
        db = firestore.client()
        produtos_ref = db.collection('produtos').stream()
        lista_produtos = [dict(doc.to_dict(), id=doc.id) for doc in produtos_ref]
        return Response(lista_produtos)

# VIEW 2: APENAS CADASTRAR (Escrita)
class ProdutoCreateView(APIView):
    # Deixando o JSONParser como primeiro para o endpoint web funcionar melhor
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request):
        db = firestore.client()
        data = request.data
        
        # Se o data vier vazio, tentamos forçar a leitura do JSON
        if not data:
            import json
            data = json.loads(request.body)

        try:
            imagem_arquivo = request.FILES.get('imagem') 
            url_final = data.get('imagem_url', '') 

            if imagem_arquivo:
                resultado = cloudinary.uploader.upload(imagem_arquivo)
                url_final = resultado['secure_url']

            # Criando o dicionário com dados garantidos
            dados_produto = {
                'nome': data.get('nome'),
                'marca': data.get('marca'),
                'preco': float(data.get('preco') or 0),
                'descricao': data.get('descricao', ''),
                'imagem_url': url_final,
                'tags': data.get('tags', []),
                'estoque': int(data.get('estoque') or 0)
            }

            # Validação simples: se não tem nome, não salva
            if not dados_produto['nome']:
                return Response({"erro": "Nome do produto é obrigatório"}, status=400)

            novo_doc = db.collection('produtos').add(dados_produto)
            
            return Response({
                "id": novo_doc[1].id, 
                "msg": "Produto salvo com sucesso!"
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
                'tipo': 'cliente' # ou 'vendedor'
            })
            
            return Response({"uid": user.uid, "msg": "Usuário criado com sucesso!"})
        except Exception as e:
            return Response({"erro": str(e)}, status=400)