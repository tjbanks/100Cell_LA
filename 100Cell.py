# -*- coding: utf-8 -*-
"""
Created on Wed May 16 08:18:30 2018

@author: tjbanks
"""

import re
import subprocess
import threading
from tempfile import mkstemp
from shutil import move
import os
from os import fdopen, remove
from random import randint

import pandas as pd
import paramiko
import getpass

import zipfile

import tkinter as tk # this is for python3
from tkinter import ttk
from tkinter import messagebox

root = tk.Tk()

class Autoresized_Notebook(ttk.Notebook):
    def __init__(self, master=None, **kw):
        ttk.Notebook.__init__(self, master, **kw)
        self.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self,event):
        event.widget.update_idletasks()
        tab = event.widget.nametowidget(event.widget.select())
        event.widget.configure(height=tab.winfo_reqheight())

class CreateToolTip(object):
    """
    create a tooltip for a given widget
    https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tkinter
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()
            
def menu_bar(root):
    def hello():
        print("hello!")
        
    def about():
        messagebox.showinfo("About", "Simulation Builder written for:\nProfessor Satish Nair's Neural Engineering Laboratory\nat The University of Missouri\n\nWritten by: Tyler Banks\n\nContributors:\nFeng Feng\n\nInitial Neuron Code:  Feng et al. (2016)\n\nEmail tbg28@mail.missouri.edu with questions", icon='info')

    menubar = tk.Menu(root)
    
    # create a pulldown menu, and add it to the menu bar
    filemenu = tk.Menu(menubar, tearoff=0)
    #filemenu.add_command(label="Open", command=hello)
    #filemenu.add_command(label="Save", command=hello)
    #filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)
    
    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="About", command=about)
    menubar.add_cascade(label="Help", menu=helpmenu)
    return menubar

#pass the method that will create the content for your frame
def bind_page(page, gen_frame):
    #### Scrollable Frame Window ####
    #https://stackoverflow.com/questions/42237310/tkinter-canvas-scrollbar
    frame = tk.Frame(page, bd=2)
    frame.pack(side="left",fill="both",expand=True)
    
    yscrollbar = tk.Scrollbar(frame)
    yscrollbar.pack(side=tk.RIGHT,fill=tk.Y)
    xscrollbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
    xscrollbar.pack(side=tk.BOTTOM,fill=tk.X)
    
    canvas = tk.Canvas(frame, bd=0,
                    xscrollcommand=xscrollbar.set,
                    yscrollcommand=yscrollbar.set,)
    
    xscrollbar.config(command=canvas.xview)
    yscrollbar.config(command=canvas.yview)
    
    f=tk.Frame(canvas)
    canvas.pack(side="left",fill="both",expand=True)
    canvas.create_window(0,0,window=f,anchor='nw')
    ###############################
    gen_frame(f)
    frame.update()
    canvas.config(scrollregion=canvas.bbox("all"))
    
    
def parameters_page(root):
    
    param_option_frame = tk.LabelFrame(root, text="Selected Parameters")
    top_option_frame = tk.LabelFrame(root, text="Management")
    table_frame = tk.Frame(root)
    console_frame = tk.LabelFrame(root, text="Console Output")
    
    param_option_frame.grid(column=0,row=0,sticky='news',padx=10,pady=5)
    top_option_frame.grid(column=0,row=1,sticky='news',padx=10,pady=5)
    table_frame.grid(column=0,row=2,sticky='news',padx=10,pady=5)
    console_frame.grid(column=1,row=0,sticky='news',padx=10,pady=5,rowspan=2)
    
    ##############################
    
    ######Console section
    ##############################
    
    c = tk.Label(console_frame,text='Live output for current run.')
    c.grid(column=0, row=0)
    
    console = tk.Text(console_frame)
    console.config(width= 70, height=25, bg='black',fg='light green')
    console.grid(column=0, row=1, padx=5, pady=5, sticky='NEWS')
    
    console.configure(state='normal')
    #console.insert('end', 'console > ')
    console.configure(state='disabled')
    
    def run_command(command):
        try:
            p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return iter(p.stdout.readline, b'')
        except Exception as e:
            return iter(str(e).splitlines())

    def run_command_in_console(command, comment=False, cons="console"):
        console.configure(state='normal')
        console.insert('end', '{} > '.format(cons) + command + '\n')
        if(not comment):
            command = command.split()
            for line in run_command(command):
                try:
                    string = line.decode('unicode_escape')
                except Exception:
                    string = line
                console.insert('end', '' + string)
                console.see(tk.END)
        #console.insert('1.0', 'console > ')
        console.configure(state='disabled')
        #display_app_status('Command Running')
        
        return
    #TODO THREADING IS A WIP, need to convert everything to classes first to ensure we only run 1 at a time
    def run_command_in_console_threaded(command):
        import threading
        t1 = threading.Thread(target=lambda r=command:run_command_in_console(r))
        t1.start()
        return
    
    def replace(file_path, pattern, subst):
                #Create temp file
                #print("searching for: {}".format(pattern))
                fh, abs_path = mkstemp()
                with fdopen(fh,'w') as new_file:
                    with open(file_path) as old_file:
                        for line in old_file:
                            line = re.sub(r"{}".format(pattern), subst, line)
                            new_file.write(line)
                #Remove original file
                remove(file_path)
                #Move new file
                move(abs_path, file_path)
    
    ##############################
    
    class ServerEntryBox:
        
        def __init__(self, parent, display=False):
            self.params_file = "serverparams.csv"
            self.column_names = ["hostname", "user", "password", "keyfile", "partition", "nodes", "cores"]
            self.load_file(parent)
            if display:
                self.display(parent)
            return
        
        def display(self, parent):
            
            top = self.top = tk.Toplevel(parent)
            top.geometry('325x350')
            top.resizable(0,0)
            tk.Label(top, text='Server Properties').grid(row=0,column=0,sticky="WE",columnspan=2)
            
            conn_option_frame = tk.LabelFrame(top, text="Connection Parameters")
            conn_option_frame.grid(column=0,row=1,sticky='news',padx=10,pady=5)
            
            run_option_frame = tk.LabelFrame(top, text="Runtime Parameters")
            run_option_frame.grid(column=0,row=2,sticky='news',padx=10,pady=5)
            
            
            l = tk.Label(conn_option_frame, text='Hostname',width=15, background='light gray')
            l.grid(row=2,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            
            self.host_e = tk.Entry(conn_option_frame,width=25,textvariable=self.hostname)
            self.host_e.grid(row=2,column=1,padx=5)
            
            l = tk.Label(conn_option_frame, text='User',width=15, background='light gray')
            l.grid(row=3,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            
            self.user_e = tk.Entry(conn_option_frame,width=25,textvariable=self.user)
            self.user_e.grid(row=3,column=1,padx=5)
            
            l = tk.Label(conn_option_frame, text='Password',width=15, background='light gray')
            l.grid(row=4,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            
            self.pass_e = tk.Entry(conn_option_frame,width=25,textvariable=self.password)
            self.pass_e.grid(row=4,column=1,padx=5)
            
            l = tk.Label(conn_option_frame, text='Private Key',width=15, background='light gray')
            l.grid(row=5,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            
            self.key_e = tk.Entry(conn_option_frame,width=25,textvariable=self.keyfile)
            self.key_e.grid(row=5,column=1,padx=5)
            
            

            l = tk.Label(run_option_frame, text='Partition',width=15, background='light gray')
            l.grid(row=2,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            
            self.partition_e = tk.Entry(run_option_frame,width=25,textvariable=self.partition)
            self.partition_e.grid(row=2,column=1,padx=5)
            
            l = tk.Label(run_option_frame, text='Nodes',width=15, background='light gray')
            l.grid(row=3,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            
            self.nodes_e = tk.Entry(run_option_frame,width=25,textvariable=self.nodes)
            self.nodes_e.grid(row=3,column=1,padx=5)
            
            l = tk.Label(run_option_frame, text='Cores per Node',width=15, background='light gray')
            l.grid(row=4,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            
            self.cores_e = tk.Entry(run_option_frame,width=25,textvariable=self.cores)
            self.cores_e.grid(row=4,column=1,padx=5)
            
            #Return
            
            button_frame = tk.Frame(top)
            button_frame.grid(row=20,column=0,columnspan=2)
            
            b = tk.Button(button_frame, text="Ok", command=self.ok)
            b.grid(pady=5, padx=5, column=0, row=0, sticky="WE")
            
            b = tk.Button(button_frame, text="Cancel", command=self.cancel)
            b.grid(pady=5, padx=5, column=1, row=0, sticky="WE")
            
        def load_file(self, top):
            self.hostname = tk.StringVar(top)
            self.user = tk.StringVar(top)
            self.password = tk.StringVar(top)
            self.keyfile = tk.StringVar(top)
            self.partition = tk.StringVar(top)
            self.nodes = tk.StringVar(top)
            self.cores = tk.StringVar(top)
            self.confirm = False
            
            #Inputs            
            #tc.rnet.missouri.edu tbg28 INPUT NONE General 2 40
            params_pd = pd.read_csv(self.params_file ,delimiter=' ',\
                           header=None,\
                           names = self.column_names)
            self.hostname.set(params_pd[self.column_names[0]].get(0))
            self.user.set(params_pd[self.column_names[1]].get(0))
            self.password.set(params_pd[self.column_names[2]].get(0))
            self.keyfile.set(params_pd[self.column_names[3]].get(0))
            self.partition.set(params_pd[self.column_names[4]].get(0))
            self.nodes.set(params_pd[self.column_names[5]].get(0))
            self.cores.set(params_pd[self.column_names[6]].get(0))
            
        def save_file(self):
            d = [self.hostname.get(), self.user.get(),\
                  self.password.get(), self.keyfile.get(),\
                  self.partition.get(), self.nodes.get(),\
                  self.cores.get()]
            df = pd.DataFrame(d)
            df.transpose().to_csv(self.params_file, sep=' ',\
                           header=None,index=False)
            return
        
        def verify_good(self):
            return True
            
        def ok(self):
            self.confirm = True
            self.save_file()
            self.top.destroy()
        def cancel(self):
            self.top.destroy()

    
    class Row(tk.Frame):
        def __init__(self, parent, *args, **kwargs):
            tk.Frame.__init__(self, parent, *args, **kwargs)
            self.parent = parent
            self.root = tk.Frame(self.parent)
            self.is_string = False
            return
        
        def config(self, file_name, variable, search_for, comment):
            self.v_value = tk.StringVar(self.root)
            
            try:
                f = open(file_name, "r")
    
                for line in f:
                    if re.match(search_for, line):
                        #print("{} - {}".format(file_name,line))
                        line = re.sub(search_for, "", line)
                        line = re.sub("//.+", "", line)
                        self.v_value.set(line)
                        self.original_value = line
                        break
            except Exception:
                self.v_value.set("Err var not found")
                
            #self.v_value.set(variable)#Not correct
            
            self.search_for = search_for
            
            self.file_name = file_name
            
            frame = tk.Frame(self.root)
            var = tk.Label(frame, text="{} ({})".format(variable,file_name) ,width=30,background='light gray',anchor=tk.W)
            var.config(relief=tk.GROOVE)
            var.grid(column=0, row=0, padx=5, sticky='WE') 
            
            val = tk.Entry(frame,textvariable=self.v_value,width=50)
            val.grid(column=1, row=0, sticky='E')
               
            CreateToolTip(var,comment)
            frame.pack()
            return self
        
        
        
        def save_replacement(self):
            replace(self.file_name, self.search_for+"(.*)", "{}{}".format(self.search_for, self.v_value.get()))
              
        def reset(self):
            self.v_value.set(self.original_value)
            
        def row_to_str(self):
            #default_var("RunName","testrun")		// Name of simulation run
            proto = "{}{}"
            line = proto.format(self.search_for,self.v_value.get())
            return line
        
        def pack(self,*args,**kwargs):
            super(Row,self).pack(*args,**kwargs)
            self.root.pack(*args,**kwargs)
        
        def grid(self,*args,**kwargs):
            super(Row,self).grid(*args,**kwargs)
            self.root.grid(*args,**kwargs)
    
    
    def temp():
        run_command_in_console("Working", comment=True)
    
    def save_params():
        for row in rows: 
            row.save_replacement()
        run_command_in_console("Parameters saved", comment=True)
        
    def reset_values():
        result = messagebox.askquestion("Reset", "Are you sure you want to reset the data?", icon='warning')
        if result != 'yes':
            return
        for row in rows:
            row.reset()
        display_app_status("Values reset to initially loaded values")
        
    def server_config():
        d = ServerEntryBox(root,display=True)
        root.wait_window(d.top)
        
        if d.confirm==False:
            return
        if d.verify_good():
            return
        return
    
    def run_locally():
        save_params()
        run_command_in_console("Running code locally...", comment=True)
    
    def run_server():
        runServerButton.config(state=tk.DISABLED)
        port = 22
        testing = False
        batch_file = "batch_file.sh"
        zip_dir = '100Cell_LA_RUN_RESULTS-'+str(randint(0, 9999))
        zip_file = zip_dir+'.zip'
        remote_dir = "100Cell_LA_remote"
        
        save_params()
        run_command_in_console("Initiating remote server process...", comment=True)
        
        ###SSH###
        d = ServerEntryBox(root,display=False)
        run_command_in_console("Writing parameters to batch file", comment=True)
        replace(batch_file, "#SBATCH -p " + "(.*)", "{}{}".format("#SBATCH -p ", d.partition.get()))
        replace(batch_file, "#SBATCH -N " + "(.*)", "{}{}".format("#SBATCH -N ", d.nodes.get()))
        replace(batch_file, "#SBATCH -n " + "(.*)", "{}{}".format("#SBATCH -n ", d.cores.get()))
        
                
                
        run_command_in_console("Compressing and zipping code", comment=True)
        def zipdir(path, ziph):
            # ziph is zipfile handle
            for root, dirs, files in os.walk(path):
                for file in files:
                    ziph.write(os.path.join(root, file))
        
        zipf = zipfile.ZipFile("../"+zip_file, 'w', zipfile.ZIP_DEFLATED)
        dir_path = "."
        zipdir(dir_path, zipf)
        zipf.close()
        run_command_in_console("Code written to {}".format("../"+zip_file), comment=True)
        
        
        
        run_command_in_console("Connecting to {}...".format(d.hostname.get()), comment=True)
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            password = d.password.get()
            
            if(password is "INPUT"):
                password = getpass.getpass('Password for %s@%s: ' % (d.user.get(), d.hostname.get()))
            if(not testing):
                print("keyfile: " + d.keyfile.get())
                if(d.keyfile.get() == 'NONE'):
                    print("no keyfile")
                    client.connect(d.hostname.get(), port=port, username=d.user.get(), password=password)
                else:
                    k = paramiko.RSAKey.from_private_key_file(d.keyfile.get(), password)
                    client.connect(d.hostname.get(), port=port, username=d.user.get(), pkey=k)
                #chan.close()
                #client.close()
            
            
            
            run_command_in_console("Uploading code to {}".format(d.hostname.get()), comment=True)
            client.exec_command('mkdir '+ remote_dir)
            rem_loc = "./"+remote_dir+"/"+zip_file
            print(rem_loc)
            ftp_client=client.open_sftp()
            ftp_client.put("../"+zip_file,rem_loc)
            ftp_client.close()
            
            os.remove("../"+zip_file)
            
            run_command_in_console("Unzipping and running code ", comment=True, cons=d.hostname.get())
            
            #chan = client.invoke_shell()
            #unzip -o -d file file.zip
            command = 'unzip -o -d '+remote_dir+'/'+zip_dir+' '+remote_dir+'/'+zip_file
            print("Executing {}".format( command ))
            stdin , stdout, stderr = client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()          # Blocking call
            if exit_status == 0:
                print ("executed")
            else:
                print("Error", exit_status)
                
            command = remote_dir+'/'+zip_dir+'/'+batch_file
            print("Executing {}".format( command ))
            stdin , stdout, stderr = client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()          # Blocking call
            if exit_status == 0:
                print ("executed")
            else:
                print("Error", exit_status)
                for line in stderr.readlines():
                    print(line)
                    
                    
            #######################
            #KEEP CHECKING TO SEE IF DONE
            
            
            #######################
            
            run_command_in_console("Code run complete. Compressing results.", comment=True, cons=d.hostname.get())
            
            command = 'rm -rf '+remote_dir+'/'+zip_file
            print("Executing {}".format( command ))
            stdin , stdout, stderr = client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()          # Blocking call
            if exit_status == 0:
                print ("executed")
            else:
                print("Error", exit_status)
            
            command = "zip -r "+remote_dir+'/'+zip_file+" "+remote_dir+"/"+zip_dir
            print("Executing {}".format( command ))
            stdin , stdout, stderr = client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()          # Blocking call
            if exit_status == 0:
                print ("executed")
            else:
                print("Error", exit_status)
                for line in stderr.readlines():
                    print(line)
                    
            run_command_in_console("Downloading results ", comment=True)
            rem_loc = "./"+remote_dir+"/"+zip_file
            ftp_client=client.open_sftp()
            ftp_client.get(rem_loc,"../"+zip_file)
            ftp_client.close()
            
            zip_ref = zipfile.ZipFile("../"+zip_file, 'r')
            zip_ref.extractall("../"+zip_dir)
            zip_ref.close()
                        
            os.remove("../"+zip_file)
            
            run_command_in_console("Results saved to parent directory in folder: {}".format(zip_dir), comment=True)
            
            
            run_command_in_console("Cleaning up files", comment=True, cons=d.hostname.get())
            
            command = 'rm -rf '+remote_dir+'/'+zip_dir+'*'
            print("Executing {}".format( command ))
            stdin , stdout, stderr = client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()          # Blocking call
            if exit_status == 0:
                print ("executed")
            else:
                print("Error", exit_status)
                
            run_command_in_console("Disconnecting from : {}".format(d.hostname.get()), comment=True)
            client.close()
            
        except Exception as e:
            run_command_in_console('*** Caught exception: %s: %s' % (e.__class__, e))
            #traceback.print_exc()
            try:
                client.close()
            except:
                pass
        
        run_command_in_console("", comment=True)
        run_command_in_console("Remote server process complete ", comment=True)
        runServerButton.config(state=tk.NORMAL)
        #########
        
    
    saveButton = tk.Button(top_option_frame, text="Save Parameters", command=save_params)
    saveButton.grid(column=0, row =0, padx=5, pady=5, sticky='WE')
    
    resetButton = tk.Button(top_option_frame, text="Reset Parameters", command=reset_values)
    resetButton.grid(column=1, row =0, padx=5, pady=5, sticky='WE')
    #configsButton.config(state=tk.DISABLED)
    
    configsButton = tk.Button(top_option_frame, text="Remote Server Config", command=server_config)
    configsButton.grid(column=2, row =0, padx=5, pady=5, sticky='WE')
    #configsButton.config(state=tk.DISABLED)
    
    runLocalButton = tk.Button(top_option_frame, text="Save and Run Locally (Windows)", command=run_locally)
    runLocalButton.grid(column=0, row =1, padx=5, pady=5, sticky='WE')
    runLocalButton.config(state=tk.DISABLED)
    
    runServerButton = tk.Button(top_option_frame, text="Save and Run on Remote Server", command=run_server)
    runServerButton.grid(column=1, row =1, padx=5, pady=5, sticky='WE')
    #runServerButton.config(state=tk.DISABLED)
    
    
    rows = []
    params_frame = tk.Frame(param_option_frame)
    params_frame.grid(column=0, row =0, padx=5, pady=5, sticky='NEWS')
    
    row = Row(params_frame).config("main.hoc", "tstop", "tstop = ", "tstop")
    row.pack(padx=10)
    rows.append(row)
    
    row = Row(params_frame).config("bg2pyr.mod", "initW", "\tinitW = ", "Background to pyramidal initial weights")
    row.pack(padx=10)
    rows.append(row)
    
    row = Row(params_frame).config("bg2inter.mod", "initW", "\tinitW = ", "Background to interneuron initial weights")
    row.pack(padx=10)
    rows.append(row)
    
    row = Row(params_frame).config("tone2pyrD_new.mod", "initW", "\tinitW = ", "Tone to pyramidal initial weights")
    row.pack(padx=10)
    rows.append(row)
    
    row = Row(params_frame).config("tone2interD_new.mod", "initW", "\tinitW = ", "Tone to interneuron initial weights")
    row.pack(padx=10)
    rows.append(row)
    
    row = Row(params_frame).config("pyrD2pyrD_STFD_new.mod", "initW", "\tinitW = ", "Pyramidal to pyramidal initial weights")
    row.pack(padx=10)
    rows.append(row)
    
    row = Row(params_frame).config("pyrD2interD_STFD.mod", "initW", "\tinitW = ", "Background to Interneurons initial weights")
    row.pack(padx=10)
    rows.append(row)
    
    row = Row(params_frame).config("interD2pyrD_STFD_new.mod", "initW", "\tinitW = ", "Interneurons to pyramidal initial weights")
    row.pack(padx=10)
    rows.append(row)
    
    
def main(root):
    
    print('Starting. Please wait...')
    style = ttk.Style()
    try:
        style.theme_create( "colored", parent="alt", settings={
                "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0] } },
                "TNotebook.Tab": {
                    "configure": {"padding": [5, 2], "background": "#D9D9D9" },
                    "map":       {"background": [("selected", "#C0C0E0")],
                                  "expand": [("selected", [1, 1, 1, 0])] } } } )
    
        style.theme_create( "largertheme", parent="alt", settings={
                "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0] } },
                "TNotebook.Tab": {
                    "configure": {"padding": [5, 2] },
                    "map":       {
                                  "expand": [("selected", [1, 1, 1, 0])] } } } )
        style.theme_use("colored")
    except Exception:
        print('Style loaded previously. Continuing.')
    
    frame1 = tk.Frame(root)
    frame1.grid(row=0,column=0,sticky='news')
    frame1.columnconfigure(0,weight=1)
    frame1.columnconfigure(0,weight=1)
    frame2 = tk.Frame(root)
    frame2.grid(row=1,column=0,sticky='news')
    
    nb = Autoresized_Notebook(frame1)
    nb.pack(padx=5,pady=5,side="left",fill="both",expand=True)
    
    bottom_status_bar = tk.Frame(frame2)
    bottom_status_bar.grid(row=0,column=0,padx=5,pady=2)#,fill=tk.X,expand=True)
    
    label = tk.Label(bottom_status_bar,textvariable=app_status)
    label.pack(expand=True)

    page1 = ttk.Frame(nb)
    
    nb.add(page1, text='Model Configuration')
    
    
    #Alternatively you could do parameters_page(page1), but wouldn't get scrolling
    bind_page(page1, parameters_page)
    
    display_app_status("Ready")
    try:
        print('Load complete. Running...')
        root.mainloop()
    except Exception:
        print('Error, closing display loop')
    print('Closing.\n')

default_status = "Status: Ready"
def reset_app_status():
    app_status.set(default_status)

def display_app_status(str):
    app_status.set("Status: "+str)
    threading.Timer(4.0, reset_app_status).start()
            
root.columnconfigure(0,weight=1)
root.rowconfigure(0,weight=1)
root.title("100 Cell LA Configuration (University of Missouri - Neural Engineering Laboratory - Nair)")
root.geometry('1220x600')

#root.resizable(0,0)
root.config(menu=menu_bar(root))

app_status = tk.StringVar(root,'')
reset_app_status()

main(root)