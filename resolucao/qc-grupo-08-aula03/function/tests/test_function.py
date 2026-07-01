import json
import pytest
from unittest.mock import MagicMock, patch


def make_request(params: dict) -> MagicMock:
    """Cria um mock de HttpRequest com os params fornecidos."""
    req = MagicMock()
    req.params = params
    return req


class TestBuscarProdutos:
    """Testa a function buscar_produtos com diferentes combinações de parâmetros."""

    @patch("function_app.BlobServiceClient")
    def test_busca_por_categoria_retorna_lista(self, mock_blob):
        """Busca por categoria conhecida deve retornar lista não-vazia."""
        from function_app import buscar_produtos

        mock_blob.return_value.get_blob_client.return_value \
            .download_blob.return_value.readall.return_value = (
            b"id,nome,categoria,preco\n"
            b"1,Cadeira DXRacer,moveis,1299.90\n"
            b"2,Mesa Escritorio,moveis,599.00\n"
        )

        req = make_request({"categoria": "moveis"})
        response = buscar_produtos(req)

        assert response.status_code == 200
        body = json.loads(response.get_body())
        assert isinstance(body, list)
        assert len(body) > 0
        assert all(p["categoria"] == "moveis" for p in body)

    @patch("function_app.BlobServiceClient")
    def test_sem_parametros_retorna_todos(self, mock_blob):
        """Chamada sem parâmetros deve retornar todos os produtos."""
        from function_app import buscar_produtos

        mock_blob.return_value.get_blob_client.return_value \
            .download_blob.return_value.readall.return_value = (
            b"id,nome,categoria,preco\n"
            b"1,Cadeira DXRacer,moveis,1299.90\n"
            b"2,Smartphone Samsung,eletronicos,3999.00\n"
        )

        req = make_request({})
        response = buscar_produtos(req)

        assert response.status_code == 200
        body = json.loads(response.get_body())
        assert len(body) == 2

    @patch("function_app.BlobServiceClient")
    def test_categoria_inexistente_retorna_lista_vazia(self, mock_blob):
        """Categoria sem produtos deve retornar lista vazia, não erro."""
        from function_app import buscar_produtos

        mock_blob.return_value.get_blob_client.return_value \
            .download_blob.return_value.readall.return_value = (
            b"id,nome,categoria,preco\n"
            b"1,Cadeira DXRacer,moveis,1299.90\n"
        )

        req = make_request({"categoria": "categoria_inexistente"})
        response = buscar_produtos(req)

        assert response.status_code == 200
        body = json.loads(response.get_body())
        assert body == []