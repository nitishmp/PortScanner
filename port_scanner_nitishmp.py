import tkinter as tk
import socket as sk
import sqlite3 as db
import threading
import time
import tkinter.ttk as ttk
import datetime as time

class PortScannerDAL:
    def __init__(self):  #Function to initialize  all the objects and the required methods 
        self.conn=None
        self.first_query=None
        self.__connect_()
        
    def __connect_(self):  #Function to establish a connection between the database and user
        self.conn=db.connect('PortScanner.sqlite3')
        self.cur=self.conn.cursor()
        
    def read_host(self, host_ip, host_name = None):  #Function to call the read data from the host table in the databse
        self.cur.execute("SELECT HostId FROM Host WHERE HostIP = (?)",(host_ip,))
        data=self.cur.fetchone()
        if (data==None):
            return 0
        return data[0]
        
    def create_host(self, host_ip, host_name): #Fucntion to create a row in host table when the program is executed
        
        self.cur.execute(
        '''INSERT INTO 
        Host(HostName,HostIP)
        VALUES(?,?)'''
        ,(host_name,host_ip)
        )
        self.conn.commit()
        self.cur.execute("SELECT HostId FROM Host WHERE HostIP = (?)",(host_ip,))
        data = self.cur.fetchone()
        return data[0]

    def create_scan(self, host_id):  #Fucntion to create an entry in the scan table
        host_id = int(host_id)
        StartTime = time.datetime.now()
        self.cur.execute('''Insert into Scan(HostId,ScanStartTime) VALUES(?,?)''', (host_id,StartTime))
        self.conn.commit()
        first_query = "Select ScanId from Scan where HostId = \"" + str(host_id) + "\""+ "and ScanStartTime= \"" + str(StartTime)+"\""
        self.cur.execute(first_query)
        data = self.cur.fetchone()
        ScanId, = data
        return ScanId
    def update_scan_end_time(self, scan_id): #Fucntion to update the current datetime from the entries in scan table
        EndTime = time.datetime.now()
        first_query = "Update  Scan set ScanEndTime = \""+ str(EndTime) + "\" where ScanId=" + str(scan_id)
        self.cur.execute(first_query)
        self.conn.commit()
        pass
    def read_port_status(self, host_ip, host_name):  #Fucntion is called when the view results button is pressed to view all the joined tables in a tree format
        first_query = "SELECT ps.*, s.ScanStartTime FROM PortStatus ps JOIN Scan s on ps.ScanId = s.ScanId JOIN Host h on h.HostId = s.HostId WHERE h.HostIP = \"{}\" AND h.HostName = \"{}\"".format(host_ip,host_name)
        self.cur.execute(first_query)
        data = self.cur.fetchall()
        return data
    def create_port_status(self, scan_id, port, is_open): #Fucntion to insert a value to port status table
        scan_id = int(scan_id)
        port = int(port)
        is_open = int(is_open)
        self.cur.execute('''Insert into PortStatus(ScanId,PortNumber,IsPortOpen) VALUES(?,?,?)''', (scan_id,port,is_open))
        self.conn.commit()
        pass
    def __close_connection_(self): #Fucntion to close the connection with the file in the database.
        self.cur.close()
        pass
    def __del__(self):
        pass

class ResultsDialog(tk.Toplevel):  #Fucntion is used to create a custom dialog box to view the port status table in a treeview format
    def __init__(self, master, host_ip, host_name): 
        self.top = tk.Toplevel(master)
        self.top.geometry('800x750')
        self.treeview = ttk.Treeview(self.top)
        self.treeview["columns"] = ("first", "second", "third", "fourth")
        self.treeview.column("#0", width=0)
        self.treeview.column("first", width=50)
        self.treeview.column("second", width=50)
        self.treeview.column("third", width=50)
        self.treeview.column("fourth", width=100)
        self.treeview.heading("first", text="ScanId")
        self.treeview.heading("second", text="Port Number")
        self.treeview.heading("third", text="Is Open")
        self.treeview.heading("fourth", text="Scan Time")
        self.treeview.pack(expand = tk.TRUE , fill = 'both')
        self.top.grab_set()
        pass

class PortScanner:
    def __init__(self,port_min = 0, port_max=1023,ip="127.0.0.1"):  #Fucntion to initialize all the default constructor, instance attributes and other methods at object creation
        self.min_port = port_min
        self.max_port = port_max
        self.ip_address = ip
        self.scan_ID = None
        self.__init_gui()
        
    def __init_gui(self):  #Function to create the gui widgets for the main window
        self.gui = tk.Tk()
        self.gui.title("Port Scanner")
        self.gui.geometry('300x300')

        self.IPAddr = " 127.0.0.1" 
        tk.Label(self.gui,text="Host IP:").grid(row=0,column=0)
        tk.Label(self.gui,text="Host Name:").grid(row=1,column=0)
        self.IP=tk.Entry(self.gui,width=40)
        self.IP.insert(tk.END,self.IPAddr)
        self.IP.grid(row=0,column=1)
        self.hName = tk.Label(self.gui,text="Nitish's PC:")
        self.hName.grid(row=1,column=1)

        self.scan_btn = tk.Button(self.gui,text="Scan", command=self.__start_scanner)
        self.scan_btn.grid(row=2,column=1)
        self.result_btn = tk.Button(self.gui,text="View Results", command=self.__view_results)
        self.result_btn.grid(row=3,column=1)
        self.status_lbl = tk.Label(self.gui,text="Scanner is idle",)
        self.status_lbl.grid(row=4,column=0,columnspan = 1)
        self.gui.mainloop()
        
    def __start_scanner(self):  #Function is called when Scan button is clicked
        self.ip_addr = self.ip_address
        self.scan_btn.config(state = tk.DISABLED)
        self.socket = sk.socket()
        self.host = sk.gethostname()
        self.hName.config(text=self.host)
        t = threading.Thread(target=self.start_scanner)
        t.start()
        
    def start_scanner(self): #Fucntion to create a new host id in host table and begin the scanning of the ports
        self.dal = PortScannerDAL()
        self.host_id=self.dal.read_host(self.IP.get())
        if(self.host_id==0):
            self.host_id=self.dal.create_host(self.IP.get(),self.host)
        self.scan_ID=self.dal.create_scan(self.host_id)
        for i in range(self.min_port,self.max_port):
            self.status_lbl["text"]="Scanning port number: "+ str(i)
            self.scan_port(i)
        self.dal.update_scan_end_time(self.scan_ID)
        self.status_lbl["text"]="Finished Scanning"
        self.scan_btn["state"]=tk.NORMAL
        self.result_btn["state"]=tk.NORMAL
    
    def scan_port(self, port): #Function to check if the port to scan is open or closed and also creeate the socket connection to the client
        result = self.socket.connect_ex((self.ip_addr, port))
        if(result == 0):
            self.dal.create_port_status(self.scan_ID,port,1)
            
        else:
            self.dal.create_port_status(self.scan_ID,port,0)
    
    def __view_results(self): #Function is called when view results button is clicked and diplay all the joined coloums scan id,port number, is port open, start time details
        self.dal2=PortScannerDAL()
        self.results=ResultsDialog(self.gui, self.IP.get(),self.host)
        result = self.dal2.read_port_status(self.IP.get(),self.host)
        for i in range(len(result)):
            self.results.treeview.insert("", i, text=str(i), values=result[i])
    
    def __update_host_name(self): # Function to update the host name to the PC name using the system IP address.
        self.hName['text']=self.host
    
if __name__ == '__main__':
    ps = PortScanner()