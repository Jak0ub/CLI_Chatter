# CLI_Chatter

> ℹ️ **Info:**
>  **Please ignore the IP addresses in the GIF below. It shows the program in a lab testing environment.**


![gif](https://github.com/Jak0ub/Jak0ub/blob/main/cli_chatter.gif)

> ⚠️ **Warning:**
>  This project is meant to be used by smaller groups of chatters (2-10max at one time). 

* Available for docker w/o interactive mode. Everything is automated. 
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

* If client leaves using ^C after joining a room and waiting there, the client can't enter the same room (The client MUST enter a new one to become legitimate client once again)
* **Try to AVOID ^C AT ANY COSTS**
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


# Installation

**`report.txt` will be now saved to your current dir as `report_from_docker.txt`. The file WILL be overwritten after restarting the docker.**


### Download the docker (/tmp is **NEEDED** for mounting to work (permissions). Trust me. I found out the hard way)
```
cd /tmp
curl -L "https://raw.githubusercontent.com/jak0ub/CLI_Chatter/main/Dockerfile" -o Dockerfile
curl -L "https://raw.githubusercontent.com/jak0ub/CLI_Chatter/main/docker-compose.yml" -o docker-compose.yml
touch report_from_docker.txt
```
### EDIT THE `docker-compose.yml` PASSWORD AND PORT

### Start the docker
```
sudo docker compose up -d
```

# DDOS protection setup

* Do not share server password with everyone. Once someone has your password, they can send as many packets as they'd like.
* Server stores potential threats inside `report.txt` or `report_from_docker.txt`(docker version) to your current dir.
* If you want to ban any IP inside this report, use **fail2ban**. **Setup provided below**

### **Fail2ban setup** for *docker* (Ban any ip afer 10 failed attempts until server is rebooted)

*Switch to super user*
```
sudo su
```
*Install fail2ban(Use your own package manager)*
```
apt install fail2ban
```

*Edit conf file*
```
vi /etc/fail2ban/filter.d/cli_chatter.conf
```
*Paste this inside vi session and use `ESC` + `:wq` + `Enter`*
```
[Definition]
failregex = ^<HOST>\s+->\s+\d+x packets$
ignoreregex = ^Logged IP addresses|^If needed|^$
```
*Now edit another config file*
```
vi /etc/fail2ban/jail.d/cli_chatter.local
```
*Paste this inside vi session and use `ESC` + `:wq` + `Enter`*
```
[cli_chatter]
enabled = true
filter  = cli_chatter
logpath = /tmp/report_from_docker.txt
backend = polling
maxretry= 1
findtime= 1
bantime = 86400
action  = iptables[name=CliChatter, protocol=all]
```
*Start the program*
```
sudo systemctl start fail2ban 
```