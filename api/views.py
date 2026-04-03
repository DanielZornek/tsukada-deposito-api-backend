from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from firebase_admin import firestore
from firebase_admin import auth

# Cloudinary para a imagem  do produto
import cloudinary.uploader  
from rest_framework.parsers import MultiPartParser, FormParser

class ProdutoListarView(APIView):
    def get(self, request):
        db = firestore.client()
        produtos_ref = db.collection('produtos').stream()
        
        lista_produtos = []
        for doc in produtos_ref:
            p = doc.to_dict()
            p['id'] = doc.id
            lista_produtos.append(p)
            
        return Response(lista_produtos)

class ProdutoCreateView(APIView):
    
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        db = firestore.client()

        data = request.data
        imagem_arquivo = request.FILES.get('imagem') 
        
        try:
            url_final = data.get('imagem_url') 

            if imagem_arquivo:
                resultado = cloudinary.uploader.upload(imagem_arquivo)
                url_final = resultado['secure_url']

            novo_doc = db.collection('produtos').add({
                'nome': data.get('nome'),
                'marca': data.get('marca'),
                'preco': float(data.get('preco', 0)),
                'descricao': data.get('descricao'),
                'imagem_url': url_final,
                'tags': data.get('tags', []),
                'estoque': int(data.get('estoque', 0))
            })
            
            return Response({
                "id": novo_doc[1].id, 
                "imagem": url_final, 
                "msg": "Produto salvo!"
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