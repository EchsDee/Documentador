import os
import sys
import threading
import win32event
import win32service
import win32serviceutil
import logging
from Documentador import app
from waitress import serve

# Add the directory containing DocumentadorService.py to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

def run_server():
    try:
        serve(app, host='0.0.0.0', port=8000)
    except Exception as e:
        logging.exception("Exception in run_server")

class DocumentadorService(win32serviceutil.ServiceFramework):
    _svc_name_ = "DocumentadorService"
    _svc_display_name_ = "Documentador Service"

    def __init__(self, args):
        super().__init__(args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.server_thread = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)
        logging.info("Service stopped.")

    def SvcDoRun(self):
        logging.basicConfig(
            filename='C:\\DocumentadorService\\service.log',
            level=logging.DEBUG,
            format='[%(asctime)s] %(levelname)s - %(message)s'
        )
        logging.info('Service is starting.')

        try:
            self.server_thread = threading.Thread(target=run_server)
            self.server_thread.start()
            logging.info('Server thread started.')

            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
            logging.info('Stop signal received.')
        except Exception as e:
            logging.exception("Exception in SvcDoRun")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(DocumentadorService)