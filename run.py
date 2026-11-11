import sys
import os
import socket

# Set standard UTF-8 environment
os.environ["PYTHONIOENCODING"] = "utf-8"

def is_port_in_use(port: int, host: str = '127.0.0.1') -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def find_available_port(start_port: int = 8000) -> int:
    port = start_port
    while is_port_in_use(port) and port < 8020:
        port += 1
    return port

if __name__ == "__main__":
    print("==================================================================")
    print(">> SMART LOAN VERIFICATION & APPROVAL SYSTEM")
    print("Academic Prototype with Blockchain, OCR, Face Auth & Explainable ML")
    print("==================================================================")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

    try:
        from backend.seed_data import seed_database
        seed_database()
    except Exception as e:
        print(f"Database Init Note: {e}")

    target_port = 8000
    if is_port_in_use(target_port):
        # Find next open port if 8000 is still busy
        target_port = find_available_port(8000)

    print(f"\nWeb App Live at: http://127.0.0.1:{target_port}")
    print(f"Interactive Swagger API Docs at: http://127.0.0.1:{target_port}/docs")
    print("------------------------------------------------------------------\n")

    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=target_port, reload=False)
