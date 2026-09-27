"""FatiaExpress no navegador. Execute: python web_app.py."""

import os
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest, HTTPException

from database.connection import DB_PATH, init_database, seed_data_if_empty
from services.web_order_service import CheckoutError, WebOrderService


def create_app(config=None):
    web_dir = Path(__file__).resolve().parent / "web"
    app = Flask(__name__, static_folder=str(web_dir), static_url_path="/static")
    app.config.from_mapping(
        DATABASE=os.environ.get("FATIA_DB_PATH", str(DB_PATH)),
        MAX_CONTENT_LENGTH=64 * 1024,
    )
    if config:
        app.config.update(config)
    app.json.ensure_ascii = False
    app.json.sort_keys = False
    init_database(app.config["DATABASE"])
    seed_data_if_empty(include_demo_orders=False, db_path=app.config["DATABASE"])
    orders = WebOrderService(app.config["DATABASE"])
    app.extensions["web_orders"] = orders

    @app.before_request
    def validate_origin():
        if request.method == "POST":
            if request.headers.get("Sec-Fetch-Site") in ("cross-site", "same-site"):
                raise CheckoutError("Abra o cardápio neste site para enviar seu pedido.", status=403)
            origin = request.headers.get("Origin")
            if origin:
                expected = urlsplit(request.host_url)
                try:
                    actual = urlsplit(origin)
                except ValueError:
                    raise CheckoutError("Origem do pedido não autorizada.", status=403) from None
                if (actual.scheme, actual.netloc) != (expected.scheme, expected.netloc):
                    raise CheckoutError("Origem do pedido não autorizada.", status=403)

    @app.after_request
    def response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "script-src 'self'; connect-src 'self'; font-src 'self'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        )
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def home():
        return send_from_directory(web_dir, "index.html")

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/api/catalog")
    def catalog():
        return jsonify(orders.catalog())

    @app.post("/api/orders")
    def checkout():
        if not request.is_json:
            raise CheckoutError("Envie o pedido em formato JSON.", status=415)
        try:
            data = request.get_json()
        except BadRequest:
            raise CheckoutError("Não foi possível ler o pedido. Revise os dados e tente novamente.") from None
        return jsonify(orders.checkout(data)), 201

    @app.get("/api/orders/<int:order_id>")
    def track(order_id):
        authorization = request.headers.get("Authorization", "")
        token = authorization[7:] if authorization.startswith("Bearer ") else None
        return jsonify(orders.track(order_id, token))

    @app.errorhandler(CheckoutError)
    def checkout_error(error):
        result = {"error": str(error)}
        if error.field:
            result["field"] = error.field
        return jsonify(result), error.status

    @app.errorhandler(sqlite3.Error)
    def database_error(error):
        app.logger.exception("Falha ao acessar o banco de dados")
        return jsonify(error="Não foi possível salvar ou consultar agora. Tente novamente em instantes."), 503

    @app.errorhandler(HTTPException)
    def http_error(error):
        messages = {404: "Página ou recurso não encontrado.", 405: "Operação não permitida.",
                    413: "Pedido muito grande. Reduza as observações ou os itens."}
        return jsonify(error=messages.get(error.code, "Não foi possível processar esta solicitação.")), error.code

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", "8000")), debug=False)
