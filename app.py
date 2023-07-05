from src import create_app
import threading

app = create_app()
if __name__ == '__main__':
    try:
        app.run()
    except Exception as ex:
        print(f"Failed to run server.Excaption{ex}")
