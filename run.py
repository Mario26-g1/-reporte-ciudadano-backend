from app import create_app

app = create_app()

if __name__ == "__main__":
    # Puerto 5050 en vez de 5000: el 5000 está ocupado por un proceso del
    # sistema (PID 4 = "System" de Windows), no por nuestra app.
    app.run(host="0.0.0.0", port=5050)
