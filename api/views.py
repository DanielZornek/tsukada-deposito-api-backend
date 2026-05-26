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
        
        # FILTRO DE RANGE DE PREÇO EM PYTHON
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

            dados_antigos = doc.to_dict() or {}

            try:
                preco = float(data.get('preco')) if data.get('preco') is not None else float(dados_antigos.get('preco', 0))
            except (ValueError, TypeError):
                preco = float(dados_antigos.get('preco', 0))

            try:
                estoque = int(data.get('estoque')) if data.get('estoque') is not None else int(dados_antigos.get('estoque', 0))
            except (ValueError, TypeError):
                estoque = int(dados_antigos.get('estoque', 0))

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
            return Response({"id": pk, "msg": "Produto updated com sucesso!"}, status=status.HTTP_200_OK)

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
                uid = res_data.get("localId")
                
                db = firestore.client()
                user_doc = db.collection('usuarios').document(uid).get()
                
                nome = "Usuário Tsukada"
                if user_doc.exists:
                    nome = user_doc.to_dict().get('nome', "Usuário Tsukada")

                return Response({
                    "msg": "Login bem-sucedido",
                    "idToken": res_data.get("idToken"), 
                    "localId": uid, 
                    "email": res_data.get("email"),
                    "nome": nome
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
        db = firestore.client()
        try:
            try:
                auth.delete_user(uid)
            except Exception:
                pass
            
            db.collection('usuarios').document(uid).delete()
            return Response({"msg": "Conta excluída com sucesso!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"erro": f"Erro ao excluir conta: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, uid):
        inicializar_firebase_se_necessario()
        data = request.data
        db = firestore.client()
        
        try:
            update_args = {}
            if 'email' in data and data['email']: 
                update_args['email'] = data['email']
            if 'senha' in data and data['senha']: 
                if len(str(data['senha'])) < 6:
                    return Response({"erro": "A senha deve ter no mínimo 6 caracteres."}, status=status.HTTP_400_BAD_REQUEST)
                update_args['password'] = data['senha']
            
            if update_args:
                auth.update_user(uid, **update_args)
            
            if 'nome' in data and data['nome']:
                db.collection('usuarios').document(uid).set(
                    {'nome': data['nome']}, 
                    merge=True
                )
            
            return Response({"msg": "Perfil atualizado com sucesso!"}, status=status.HTTP_200_OK)
            
        except Exception as e:
            erro_msg = str(e)
            if "EMAIL_EXISTS" in erro_msg:
                erro_msg = "Este e-mail já está sendo usado por outra conta."
            return Response({"erro": f"Erro ao atualizar: {erro_msg}"}, status=status.HTTP_400_BAD_REQUEST)

class UsuarioReservasView(APIView):
    def get(self, request, uid):
        inicializar_firebase_se_necessario()
        db = firestore.client()
        try:
            reservas_ref = db.collection('reservas').where('usuario_id', '==', uid)
            docs = reservas_ref.stream()
            
            lista_reservas = [dict(doc.to_dict(), id=doc.id) for doc in docs]
            return Response(lista_reservas, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"erro": f"Erro ao buscar histórico de reservas: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProdutoReservarView(APIView):
    parser_classes = (JSONParser,)

    def post(self, request, pk):
        inicializar_firebase_se_necessario()
        db = firestore.client()
        data = request.data

        try:
            usuario_id = data.get('usuario_id')
            if not usuario_id:
                return Response({"erro": "O ID do usuário é obrigatório para vincular a reserva."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                quantidade_reserva = int(data.get('quantidade', 1))
                if quantidade_reserva <= 0:
                    return Response({"erro": "A quantidade deve ser maior que zero."}, status=status.HTTP_400_BAD_REQUEST)
            except (ValueError, TypeError):
                return Response({"erro": "Quantidade inválida."}, status=status.HTTP_400_BAD_REQUEST)

            produto_ref = db.collection('produtos').document(pk)
            doc = produto_ref.get()

            if not doc.exists:
                return Response({"erro": "Produto não localizado."}, status=status.HTTP_404_NOT_FOUND)

            dados_produto = doc.to_dict() or {}
            estoque_atual = int(dados_produto.get('estoque', 0))

            if estoque_atual < quantidade_reserva:
                return Response({
                    "erro": f"Estoque insuficiente. Quantidade disponível: {estoque_atual}"
                }, status=status.HTTP_400_BAD_REQUEST)

            novo_estoque = estoque_atual - quantidade_reserva
            produto_ref.update({'estoque': novo_estoque})

            dados_reserva = {
                'usuario_id': usuario_id,
                'produto_id': pk,
                'nome_produto': dados_produto.get('nome', 'Produto'),
                'quantidade': quantidade_reserva,
                'data_reserva': firestore.SERVER_TIMESTAMP,
                'status': 'pendente'
            }
            
            _, nova_reserva_doc = db.collection('reservas').add(dados_reserva)

            return Response({
                "id_reserva": nova_reserva_doc.id,
                "msg": "Reserva realizada com sucesso!",
                "estoque_restante": novo_estoque
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"erro": f"Erro ao processar reserva: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Adicione esta classe ao final do seu arquivo views.py

class ReservaDetailView(APIView):
    parser_classes = (JSONParser,)

    def put(self, request, pk):
        inicializar_firebase_se_necessario()
        db = firestore.client()
        data = request.data

        novo_status = data.get('status')
        if not novo_status:
            return Response({"erro": "O campo 'status' é obrigatório para atualização."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Aponta direto para o documento da reserva pelo ID dela (pk)
            reserva_ref = db.collection('reservas').document(pk)
            doc = reserva_ref.get()

            if not doc.exists:
                return Response({"erro": "Reserva não localizada."}, status=status.HTTP_404_NOT_FOUND)

            # Atualiza apenas o campo status e adiciona a data de modificação
            reserva_ref.update({
                'status': novo_status,
                'data_atualizacao': firestore.SERVER_TIMESTAMP
            })

            return Response({
                "id_reserva": pk,
                "status_atual": novo_status,
                "msg": "Status da reserva atualizado com sucesso!"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"erro": f"Erro ao atualizar status da reserva: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)        

class DashboardStatsView(APIView):
    def get(self, request):
        inicializar_firebase_se_necessario()
        db = firestore.client()

        try:
            # 1. Buscar todos os produtos para calcular os totais de estoque
            produtos_docs = db.collection('produtos').stream()
            
            total_produtos_cadastrados = 0
            produtos_baixo_estoque = 0
            mapeamento_precos = {} # Guarda o preço de cada produto pelo ID para usar nas reservas

            for doc in produtos_docs:
                total_produtos_cadastrados += 1
                dados = doc.to_dict()
                
                # Guarda o preço convertido para float
                mapeamento_precos[doc.id] = float(dados.get('preco', 0))
                
                # Define "baixa no estoque" se for menor ou igual a 5 unidades
                estoque = int(dados.get('estoque', 0))
                if estoque <= 5:
                    produtos_baixo_estoque += 1

            # 2. Buscar todas as reservas para calcular os totais financeiros
            reservas_docs = db.collection('reservas').stream()
            
            total_reservas_feitas = 0
            total_dinheiro_reservado = 0.0

            for doc in reservas_docs:
                total_reservas_feitas += 1
                dados_reserva = doc.to_dict()
                
                # Ignora cálculos se a reserva foi explicitamente cancelada
                if dados_reserva.get('status') == 'cancelado':
                    continue
                    
                prod_id = dados_reserva.get('produto_id')
                qtd_reservada = int(dados_reserva.get('quantidade', 0))
                
                # Pega o preço do produto mapeado. Se não achar, usa 0
                preco_unitario = mapeamento_precos.get(prod_id, 0.0)
                
                # Multiplica a quantidade pelo preço do produto
                total_dinheiro_reservado += (qtd_reservada * preco_unitario)

            # Retorna todos os dados mastigados para o React Native
            return Response({
                "total_produtos": total_produtos_cadastrados,
                "total_reservas": total_reservas_feitas,
                "produtos_baixo_estoque": produtos_baixo_estoque,
                "total_dinheiro_reservado": round(total_dinheiro_reservado, 2)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"erro": f"Erro ao gerar painel: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)            