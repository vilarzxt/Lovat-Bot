import os
from datetime import timedelta
from flask import Flask, render_template

from config.assets import ASSETS


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    )

    app.secret_key = os.getenv("FLASK_SECRET_KEY", "troque-essa-chave-no-.env")

    # Sessão de login: sem isso, o Flask trata a sessão como "não
    # permanente" por padrão e o navegador (principalmente no mobile)
    # pode descartá-la a qualquer refresh/fechada de aba. Com isso,
    # o login do site fica válido por 30 dias.
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    from webapp.routes_public import public_bp
    from webapp.routes_auth import auth_bp
    from webapp.routes_dashboard import dashboard_bp
    from webapp.routes_owner import owner_bp, is_owner_session

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(owner_bp)

    @app.context_processor
    def inject_is_owner():
        return {"is_owner": is_owner_session()}

    @app.errorhandler(404)
    def not_found(e):
        return render_template(
            "erro.html",
            logo_url=ASSETS["logo"],
            titulo="Página não encontrada",
            mensagem="Essa página não existe ou foi movida.",
        ), 404

    return app


def start_flask_app(bot, host="0.0.0.0"):
    """
    Sobe o servidor Flask em uma thread separada, sem bloquear o
    event loop do bot (que roda via asyncio na thread principal).
    """
    import threading
    from webapp import state

    state.register_bot(bot)

    app = create_app()
    port = int(os.getenv("PORT", 5000))

    thread = threading.Thread(
        target=lambda: app.run(host=host, port=port, use_reloader=False),
        daemon=True,
    )
    thread.start()

    print(f"🌐 DASHBOARD RODANDO EM http://{host}:{port}", flush=True)
