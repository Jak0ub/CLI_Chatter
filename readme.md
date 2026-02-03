# CLI_Chatter

* Only for WAN. 
* Server is only for UNIX. Client is for all platforms.
* E2EE CLI chat app created using python.
* Code is separated into multiple files for better modularity.
* Program allows (default) 30 requests from each IP before shuting the IP down -> (default) 10 password attempts for each IP.
* After sending correct access code. IP has unlimited packet count to be processed so `choose carefully who you give your password to`.
* After 100 packets. The server clears all logs. When server is shutting down, all logs are deleted.
* Packet sniffing attack is not problem. Each IP has unique code for authorization process generated based on your server-side code.
* Server does not store any logs.
* Even the server can't read your messages.
* USE /quit to delete all logs about your IP from RAM on the server. 

## Important Notes

* If some IP addr. exceeds the **ddos_protection** var limit, than the program stores the IP addr. into `report.txt` permanently to your dir. BUT, after running the server again, the contents of `report.txt` will be overwritten.
* Use `report.txt` as your way to ban potential threats by using **ufw**.
* Change **ddos_protection** var to your own preffered value.
* Change **port** var to any port you'd like to avoid bots.
* You can also change after how many packets the logs will be erased and `report.txt` saved
* If you intent to deploy this server to someone, give them precompiled version of client-side code which they can't edit. You can use fx. **pyinstaller**
* **READ THE FOLLOWING WARNINGS!**

> ⚠️ **Warning:**
>  Do not share your server-side code with everyone. The server uses `ast.literal_eval()` so APT could abuse this function for DoS purposes when server-side code is publicly known. The exploit is hard to replicate, but not impossible. The exploit could only shut down your server-side system so no RCE etc.

> ⚠️ **Warning:**
>  After using `/quit` your terminal might stop working as intended. If you encounter this type of error, use `reset` command (for Unix)


## Instalation

### 1️⃣ Download
```
git clone https://github.com/Jak0ub/CLI_Chatter
cd CLI_Chatter
```

### 2️⃣ Venv creation

`Unix based`

```
python3 -m venv venv
source venv/bin/activate
pip install -r req.txt
```
`Windows`


```
python -m venv venv
.\venv\Scripts\activate
pip install -r req.txt
```

