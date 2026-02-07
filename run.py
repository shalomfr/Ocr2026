"""
Hebrew OCR Training System - Local Runner
Run this from the project root: python run.py
"""
import os
import sys
import webbrowser
import threading

def main():
    # Ensure we're running from the project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    sys.path.insert(0, project_root)

    from backend.app import create_app

    app = create_app()
    port = int(os.getenv('PORT', 5000))

    print("=" * 50)
    print("  Hebrew OCR Training System")
    print("=" * 50)
    print(f"  Backend:  http://localhost:{port}")
    print(f"  Frontend: cd frontend && npm run dev")
    print("=" * 50)

    # Open browser after short delay
    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open(f'http://localhost:{port}')

    threading.Thread(target=open_browser, daemon=True).start()

    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    main()
