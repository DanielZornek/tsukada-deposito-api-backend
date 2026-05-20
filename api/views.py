import os
import json
import requests
import firebase_admin
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
        
        # Captura os parâmetros de preço enviados pelo React Native
        categoria_query = request.query_params.get('categoria')
        preco_min_query = request.query_params.get('precoMin')
        preco_max_query = request.query_params.get('precoMax')
        
        produtos_ref = db.collection('produtos')
        
        # Filtro de categoria direto na query do banco
        if categoria_query and categoria_query != 'Todas':
            produtos_ref = produtos_ref.where('categoria', '==', categoria_query)
        
        docs = produtos_ref.stream()
        lista_produtos = [dict(doc.to_dict(), id=doc.id) for doc in docs]
        
        # FILTRO DE RANGE DE PREÇO EM PYTHON (Sua lógica perfeita)
        if preco_min_query:
            try:
                min_val = float(preco_min_query)
                lista_produtos = [p for p in lista_produtos if float(p.get('preco', 0)) >= min_val]
            except ValueError:
                pass
                
        if preco_max_query:
            try:
                max_val = float(preco_max_query)
                lista_produtos = [p for p in lista_produtos if float(p.get('preco', 0)) <= max_val]
            except ValueError:
                pass

        return Response(lista_produtos)

class ProdutoCreateView(APIView):
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
            return Response({"id": novo_doc.id, "msg": "Produto saved com sucesso!"}, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({"erro": f"Erro interno: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    # MÉTODO PUT CORRIGIDO E OTIMIZADO
    def put(self, request, pk=None):
        inicializar_firebase_se_necessario()
        db = firestore.client()
        data = request.data

        if not pk:
            return Response({"erro": "O ID do produto é obrigatório para atualização."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            produto_ref = db.collection('produtos').document(pk)
            doc = produto_ref.get()
            
            if not doc.exists:
                return Response({"erro": "Produto não localizado no banco de dados."}, status=status.HTTP_404_NOT_FOUND)

            # Extrai os dados atuais uma única vez para melhor performance e segurança
            dados_antigos = doc.to_dict() or {}

            # Tratamento seguro dos tipos numéricos
            try:
                preco = float(data.get('preco')) if data.get('preco') is not None else float(dados_antigos.get('preco', 0))
            except (ValueError, TypeError):
                preco = float(dados_antigos.get('preco', 0))

            try:
                estoque = int(data.get('estoque')) if data.get('estoque') is not None else int(dados_antigos.get('estoque', 0))
            except (ValueError, TypeError):
                estoque = int(dados_antigos.get('estoque', 0))

            # Monta o dicionário de atualização comparando o dado novo com o antigo
            dados_atualizados = {
                'nome': data.get('nome') if data.get('nome') is not None else dados_antigos.get('nome'),
                'marca': data.get('marca') if data.get('marca') is not None else dados_antigos.get('marca', 'Genérico'),
                'preco': preco,
                'estoque': estoque,
                'categoria': data.get('categoria') if data.get('categoria') is not None else dados_antigos.get('categoria'),
                'descricao': data.get('descricao') if data.get('descricao') is not None else dados_antigos.get('descricao', ''),
                'imagem_url': data.get('imagem_url') if data.get('imagem_url') is not None else dados_antigos.get('imagem_url', ''),
                'tags': data.get('tags') if data.get('tags') is not None else dados_antigos.get('tags', []),
                'data_atualizacao': firestore.SERVER_TIMESTAMP 
            }

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

class PerfilUsuarioView(APIView):
    def delete(self, request, uid):
        inicializar_firebase_se_necessario()
        try:
            # 1. Deleta o usuário da autenticação do Firebase
            auth.delete_user(uid)
            
            # 2. Deleta o documento do usuário no Firestore
            db = firestore.client()
            db.collection('usuarios').document(uid).delete()
            
            return Response({"msg": "Conta excluída com sucesso!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"erro": f"Erro ao excluir conta: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, uid):
        # Aqui você pode implementar a lógica de atualização de nome, por exemplo
        inicializar_firebase_se_necessario()
        db = firestore.client()
        data = request.data
        
        try:
            db.collection('usuarios').document(uid).update({
                'nome': data.get('nome')
            })
            return Response({"msg": "Perfil atualizado com sucesso!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"erro": f"Erro ao atualizar: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)