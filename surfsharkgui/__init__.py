#----------------------------------------------------------------------
# SurfShark VPN GUI
# by Jake Day
# v1.0
# Basic GUI for connecting to surfshark vpn
#----------------------------------------------------------------------

import requests, os, sys, subprocess, time, wx, zipfile, glob, fnmatch, json, signal

class SlimSelector(wx.ComboBox):
     def __init__(self, *args, **kwargs):
         wx.ComboBox.__init__(self, *args, **kwargs)
         choices = self.GetStrings()
         if choices:
             width, height = self.GetSize()
             dc = wx.ClientDC(self)
             tsize = max(dc.GetTextExtent(c)[0] for c in choices)
             print ('SlimSelector optimum:', tsize)
             self.SetMinSize((tsize+75, height))

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title, size=(600, 720))
        self.my_path = os.path.abspath(os.path.dirname(__file__))
        self.CreateStatusBar()
        self.state = 0
        self.panel = wx.Panel(self)

        config_path = os.path.expanduser('~/.surfshark/configs')

        with open(os.path.join(self.my_path, 'assets/servers.json')) as s:
            self.serverdata = json.load(s)

        servers = list(self.serverdata.keys())

        self.servercmb = SlimSelector(self.panel, choices=servers, style=wx.CB_READONLY)
        self.protocmb = SlimSelector(self.panel, value="tcp", choices=['udp','tcp'], style=wx.CB_READONLY)

        self.credentialsbtn = wx.Button(self.panel, -1, "Enter Credentials")
        self.credentialsbtn.SetBackgroundColour('#ffffff')
        self.credentialsbtn.SetForegroundColour('#00d18a')

        self.cdbtn = wx.Button(self.panel, -1, "Quick Connect")
        self.cdbtn.SetBackgroundColour('#00d18a')
        self.cdbtn.SetForegroundColour('#ffffff')

        logoimg = wx.Image(os.path.join(self.my_path, 'assets/surfsharkgui.png'), wx.BITMAP_TYPE_ANY)
        logoimgBmp = wx.StaticBitmap(self.panel, wx.ID_ANY, wx.Bitmap(logoimg))
        self.Bind(wx.EVT_BUTTON, self.OnConnectDisconnect, self.cdbtn)
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.AddSpacer(10)
        sizer.Add(self.credentialsbtn, 0, wx.ALIGN_CENTER, 10)

        sizer.Add(logoimgBmp, 0, wx.ALIGN_CENTER, 10)
        sizer.AddSpacer(10)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(self.servercmb, 1, wx.ALIGN_LEFT, 10)
        hsizer.Add(self.protocmb, 0, wx.ALIGN_RIGHT, 10)

        sizer.Add(hsizer, 0, wx.ALIGN_CENTER, 10)
        sizer.AddSpacer(10)

        sizer.Add(self.cdbtn, 0, wx.ALIGN_CENTER, 10)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.panel.SetSizerAndFit(sizer)
        self.panel.Layout()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(10)
    def OnTimer(self, evt):
        return None
    def OnClose(self, evt):
        pgid = self.GetPGID()
        if pgid:
            subprocess.check_call(['sudo', 'kill', str(pgid)])
            sys.exit(0)
        else:
            sys.exit(0)
        evt.skip()
    def OnCredentials(self, evt):
        dlg = wx.MessageDialog(self,
            'Please generate your credentials first at https://account.surfshark.com/setup/manual.',
            'Generate Credentials', wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

        dlg = wx.TextEntryDialog(self, 'Enter Your Username','SurfShark Credentials')
        save = True

        if dlg.ShowModal() == wx.ID_OK:
            username = dlg.GetValue()
        else:
            save = False
        dlg.Destroy()

        dlg = wx.PasswordEntryDialog(self, 'Enter Your Password','SurfShark Credentials') 

        if dlg.ShowModal() == wx.ID_OK:
            password = dlg.GetValue()
        else:
            save = False
        dlg.Destroy()

        if save:
            credentials_file = os.path.expanduser('~/.surfshark/configs/credentials')
            with open(credentials_file, 'w') as fw:
                fw.write(username + '\n' + password + '\n')

    def OnConnectDisconnect(self, evt):
        if self.state == 0:
            evt.GetEventObject().SetLabel('Disconnect')
            evt.GetEventObject().SetBackgroundColour('#ffffff')
            evt.GetEventObject().SetForegroundColour('#00d18a')            
            config_path = os.path.expanduser('~/.surfshark/configs')
            credentials_file = os.path.join(config_path, 'credentials')

            config_file = os.path.join(config_path, self.serverdata[self.servercmb.GetValue()] + '_' + self.protocmb.GetValue() + '.ovpn')
            subprocess.Popen(['sudo', os.path.join(self.my_path, 'assets/fix.sh')])
            self.ovpn = subprocess.Popen(['sudo', 'openvpn', '--auth-nocache', '--config', config_file, '--auth-user-pass', credentials_file], preexec_fn=os.setpgrp)
            pgid = os.getpgid(self.ovpn.pid)
            self.state = 1
        else:
            evt.GetEventObject().SetLabel('Quick Connect')
            evt.GetEventObject().SetBackgroundColour('#00d18a')
            evt.GetEventObject().SetForegroundColour('#ffffff')
            pgid = os.getpgid(self.ovpn.pid)
            subprocess.check_call(['sudo', 'kill', str(pgid)])
            self.state = 0
        self.panel.Layout()
    def GetPGID(self):
        try:
            pgid = os.getpgid(self.ovpn.pid)
        except:
            return False
        return pgid
class MyApp(wx.App):
    def OnInit(self):
        self.__frame = MyFrame(None, "SurfShark VPN GUI")
        self.SetTopWindow(self.__frame)

        self.__frame.Show(True)

        self.Prep()
        return True

    def Prep(self):
        config_path = os.path.expanduser('~/.surfshark/configs')

        if not os.path.exists(config_path):
            os.makedirs(config_path)

        if not os.path.exists(os.path.join(config_path, 'configurations')):
            confs_url = 'https://my.surfshark.com/vpn/api/v1/server/configurations'
            fileConfs = requests.get(confs_url)
            open(os.path.join(config_path, 'configurations'), 'wb').write(fileConfs.content)
            with zipfile.ZipFile(os.path.join(config_path, 'configurations'), 'r') as zip_conf:
                zip_conf.extractall(config_path)
    def GetFrame(self):
        return self.__frame
app = MyApp()
def sigint_handler(signal, frame):
    print("\r", end="")    
    print("Killing")
    pgid = app.GetFrame().GetPGID()
    if pgid:
        subprocess.check_call(['sudo', 'kill', str(pgid)])
        sys.exit(0)
    else:
        sys.exit(0)
signal.signal(signal.SIGINT, sigint_handler)
app.MainLoop()
