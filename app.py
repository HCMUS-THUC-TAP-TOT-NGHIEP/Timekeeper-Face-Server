from src import create_app
import threading

if __name__ == '__main__':
    # app.run(threaded=True)
    try:
        app = create_app()
        app.run()
    # threading.Thread(target=lambda: app.run(
    #     debug=True, use_reloader=False)).start()
    except Exception as ex:
        print(f"Failed to run server.Excaption{ex}")
