import win32serviceutil
import win32service
import win32event
import os
import sys
import multiprocessing
from Documentador import app
from waitress import serve

def run_server():
    serve(app, host='0.0.0.0', port=8000)

class DocumentadorService(win32serviceutil.ServiceFramework):
    _svc_name_ = "DocumentadorService"
    _svc_display_name_ = "Documentador Service"

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.server_process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.server_process and self.server_process.is_alive():
            self.server_process.terminate()
            self.server_process.join()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)

        self.server_process = multiprocessing.Process(target=run_server)
        self.server_process.start()

        # Wait for the stop event to be set
        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

        # Cleanup if necessary
        if self.server_process.is_alive():
            self.server_process.terminate()
            self.server_process.join()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(DocumentadorService)