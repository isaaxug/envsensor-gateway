import websocket

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

if __name__ == "__main__":
    import os
    DEVICEID = os.environ.get('SOCKET_DEVICEID', 'E782E5311100')

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://localhost:5000/talk/"+DEVICEID,
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.run_forever()
