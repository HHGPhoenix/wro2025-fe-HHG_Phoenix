from multiprocessing import Process, Manager
from RPIs.DataManager.DataTransferer.DataTransferer import DataTransferer
from RPIs.WebServer.WebServer import WebServer

if __name__ == "__main__":
    # Initialize Manager for shared list
    manager = Manager()
    shared_list = manager.list([None, None])

    # Initialize the DataTransferer
    data_transferer = DataTransferer(shared_list)
    
    # Start the data processing in a separate process
    p_transferer = Process(target=data_transferer.process_cam_frames)
    p_transferer.start()
    
    # Start the web server in a separate process without directly passing the Flask app
    p_webserver = Process(target=WebServer, args=(shared_list,))
    p_webserver.start()

    print("Processes started")
    
    p_transferer.join()
    p_webserver.join()