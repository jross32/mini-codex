from . import create_app


app = create_app()


if __name__ == "__main__":
    app.run(host=app.config["SETTINGS"].api_host, port=app.config["SETTINGS"].api_port)
