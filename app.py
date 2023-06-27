from src import create_app
import threading
app = create_app()

if __name__ == '__main__':
    # app.run(threaded=True)
    app.run()
    # threading.Thread(target=lambda: app.run(
    #     debug=True, use_reloader=False)).start()
