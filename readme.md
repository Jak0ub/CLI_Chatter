# CLI_Chatter (Docker and DDoS solution provided)
### How does it work?

* Server runs as "python -m http.server"(shown in images below), so no network scan can suggest real intent (Chatting app).
* MITM protection is unbreakable if you have strong access_code. Here's why:
    * First you send **access_code** to the server to verify that you're authorized.
    * By default **you have 5 attempts**, but you can lower that down with [fail2ban integration](#ddos-protection-setup).
    * You do send the access code hashed in this way: **"{access_code}{public_ip}"**, so replay attacks outside of LAN wont work. Considering MITM on LAN, one can't do nothing without the access_code, the only thing they can do is DDOS your server.
    * After selecting room number you want to chat in, you retrieve the server public_key, which is encrypted using **Fernet encryption**. Before the server encrypts the key, it cuts down the first and last line.
    * The client retrieves the key. Thanks to the Errors raised when the output of decrypting the encrypted server public_key doesn't match the token, **we can rule out the MITM possibility**. 
    * As described about the server public_key, the server/client does the same for the client public_key.
    * The only way to break this model is bruteforcing the hash if your IP is known. So **ensure having strong access code.**
* Every request is sent via url parameters. Nothing stays unencrypted. 
* When you join the room, you wait for the other side. This is the entire process:
    * You send the get request to join the room. **Tampering with client side source code is solved** by implicit checks on the server side. Fx. If you request to join room with 2 clients, the request will be dropped.
    * When the room state is at 0 clients, you wait and poll every 10s to check, if someone has requested to join in.
    * This process is not E2EE. The other side requests to join in by encrypting the room number with server public key. The server then decrypts the room number and encrypts message for you with the specific IP requesting to join in.
    * If you allow the other side to join in, the server than sends clients public keys to each other to ensure E2EE. Then the chatting can start!
* Every request sent is being deleted after total of 100 requests sent to the server. After using /quit to exit the chats, the server deletes all information about you and the other side.
* Code is separated into multiple files for better modularity.



<table>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Jak0ub/Jak0ub/refs/heads/main/cli-chatter-1.png" width="400"></td>
    <td><img src="https://raw.githubusercontent.com/Jak0ub/Jak0ub/refs/heads/main/cli-chatter-2.png" width="400"></td>
  </tr>
</table>

> ℹ️ **Info:**
>  **Please ignore the IP addresses in the GIF below. It shows the program in a lab testing environment.**


![gif](https://github.com/Jak0ub/Jak0ub/blob/main/cli_chatter.gif)


## Important Notes

* Server is only for UNIX, client is for all platforms.
* Works only on WAN. Avoid using LAN. 2 clients using the same public IP abd knowing the access_Code at the same time is going to crash both clients. **If you want to chat across LAN, use different tool.** *`Be careful about who you give your server access code to!`*
* If client leaves using ^C after joining a room and waiting there, the client can't enter the same room (The client MUST enter a new one to become legitimate client once again)
* No group chats.
* **Try to AVOID ^C AT ANY COSTS**
* If some IP addr. exceeds the **ddos_protection** var limit, than the program stores the IP addr. into `report.txt` permanently to your dir. **Should be used with fail2ban.**
* Change **port** var to any port you'd like to avoid bots.
* You can also change after how many packets the logs will be erased and `report.txt` saved. **(Not for docker)**
* **READ THE FOLLOWING WARNINGS!**

> ⚠️ **Warning:**
>  Do not share your access_code with everyone. The server uses `ast.literal_eval()` so APT could abuse this function for DoS purposes when access_code is publicly known. The exploit is hard to replicate, but not impossible. The exploit could only shut down your server-side system so no RCE etc.

> ⚠️ **Warning:**
>  After using `/quit` your terminal might stop working as intended. If you encounter this type of error, use `reset` command (for Unix)


# Installation

**`report.txt` will be now saved to your current dir as `report_from_docker.txt`. The file WILL be overwritten after restarting the docker.**


### Download the docker
```
cd /tmp
curl -L "https://raw.githubusercontent.com/jak0ub/CLI_Chatter/main/Dockerfile" -o Dockerfile
curl -L "https://raw.githubusercontent.com/jak0ub/CLI_Chatter/main/docker-compose.yml" -o docker-compose.yml
touch report_from_docker.txt
chmod 777 report_from_docker.txt
```
### **EDIT THE `docker-compose.yml` PASSWORD, PORT and PACKET_LIMIT**

### Start the docker
```
sudo docker compose up -d
```

# DDOS protection setup

* **Do not share server password with everyone. Once someone has your password, they can send as many packets as they'd like.**
* Server stores potential threats inside `report.txt` or `report_from_docker.txt`(docker version) to your current dir.
* If you want to ban any IP inside this report, use **fail2ban**

### **Fail2ban setup** for *docker* (Ban any IP after specified amount of packets until the server is rebooted)


*Install fail2ban(Use your own package manager)*
```
sudo apt install fail2ban
```

*Edit conf file*
```
sudo vi /etc/fail2ban/filter.d/cli_chatter.conf
```
*Paste this inside vi session and use `ESC` + `:wq` + `Enter`*
```
[Definition]
datepattern = ^
failregex = ^<HOST>\s+->\s+\d+x packets$
ignoreregex = ^Logged IP addresses|^If needed|^$
```
*Now edit another config file*
```
sudo vi /etc/fail2ban/jail.d/cli_chatter.local
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
action = iptables-multiport[name=CliChatter, chain=DOCKER-USER, port="1:65535", protocol=tcp]
```
*Start the program*
```
sudo systemctl start fail2ban 
sudo systemctl enable fail2ban
```