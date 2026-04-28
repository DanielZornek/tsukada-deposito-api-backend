from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from firebase_admin import firestore
import cloudinary.uploader  
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

class ProdutoListarView(APIView):
    def get(self, request):
        db = firestore.client()
        produtos_ref = db.collection('produtos').stream()
        lista_produtos = [dict(doc.to_dict(), id=doc.id) for doc in produtos_ref]
        return Response(lista_produtos)

class ProdutoCreateView(APIView):
    
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def post(self, request):
        db = firestore.client()
        
        # O DRF já resolve o parse para você automaticamente
        data = request.data

        try:
            # Pegar o nome com segurança
            nome = data.get('nome')

            if not nome:
                return Response({"erro": "Nome do produto é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

            imagem_arquivo = request.FILES.get('imagem') 
            url_final = data.get('imagem_url', '') 

            if imagem_arquivo:
                resultado = cloudinary.uploader.upload(imagem_arquivo)
                url_final = resultado['secure_url']

            # Conversão segura para números
            try:
                preco = float(data.get('preco', 0))
                estoque = int(data.get('estoque', 0))
            except (ValueError, TypeError):
                preco = 0
                estoque = 0

            dados_produto = {
                'nome': nome,
                'marca': data.get('marca'),
                'preco': preco,
                'descricao': data.get('descricao', ''),
                'imagem_url': url_final,
                'tags': data.get('tags', []),
                'estoque': estoque
            }

            # No Firestore, o .add() retorna (time, doc_ref)
            _, novo_doc = db.collection('produtos').add(dados_produto)
            
            return Response({
                "id": novo_doc.id, 
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