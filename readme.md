# CLI_Chatter (Docker and DDoS solution provided)
### How does it work?

* Server runs as Simple HTTP Server(shown in images below), so no cheap network scan can suggest real intent (Chatting app). Only the encrypted server public key is publicly available, so the server doesn't look that blank.
* MITM protection works as following:
    * First you get the server public key which is encrypted using Fernet with the server access_code so no third-party could tamper with your future communication. If someone does tamper with data being sent, server will detect it and wont respond.
    * After obtaining the server public key, you prove your integrity by decrypting the server public key by access_code entered on the client-side. You than use the public_key to encrypt the authorization process.
    * The auth works by you hashing "{access_code}{client_ip}" and than encrypting this to the server. Meaning this process is C2S.
    * After the server responds with "AUTH OK", you send the server your client_public_key which is also encrypted using access_code with Fernet. This also ensures MITM protection.
    * After sending the public_key, you load room details using /rooms endpoint. Server does not store room details in accessible files, but loads the details and responds with encrypted response which you than decrypt.
    * You than select room number. Also C2S. Server responds after checking some details itself, not relying on client-side.
    * Now you're waiting in chat room. The server is set by default to hold your request for 60s (long poll). If noone requests to join in to your room, you leave the room and are met with the room selection once again. This ensures room rotation. Every request is long polled by default for 60s. 
    * If someone does request to join in, they send encrypted request to the server which then decrypts it and executes it if it does meet certain criteria. Execution means sending you an encrypted response to your long poll (meaning real time responses) using your public key.
    * You're met with "y/n" asking whether to allow specific ip to join in. Rejecting leaves you in the room. If you do accept, you send your response to the server and are met with another password, this time it is the room password.
    * The room password should be known only by those, who are using the same room. Using this password, you encrypt your another key so even the server cant tamper with your messages. You send the key and the server then acts as relay server. The other side tries to decrypt the public key by the specific password. If the pub key was decrypted successfully, that means you've created E2EE even the server cant tamper with.
    * Client code is equipped with MITM detection to warn you, if someting was tampered with.
### General info
* Code is separated into multiple files for better modularity.
* Leaving the room in process just leaves the logs on the server side RAM. Rejoining was accounted for. 
* [fail2ban](#ddos-protection-setup) and [docker](#docker-installation) integration is available.
* Once you authorize your ip, anyone can send as many requests as they'd like from your public ip. The server is E2EE so they wont do any real damage, just maybe cause DDOS.




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
* Clients are represented by IP addr. Avoid 2 clients from the same IP at the same time.
* If some IP addr. exceeds the **ddos_protection** var limit, than the program stores the IP addr. into `report.txt` permanently to your dir. **Should be used with fail2ban.**
* Change **port** var to any port you'd like to avoid bots.
* You can also change after how many packets the logs will be erased and `report.txt` saved. **(Not for docker)**
* **READ THE FOLLOWING WARNING!**


> ⚠️ **Warning:**
>  After using `/quit` your terminal might stop working as intended. If you encounter this type of error, use `reset` command (for Unix)

# Installation

```
git clone https://github.com/Jak0ub/Cli_Chatter
cd Cli_Chatter
pip install -r req.txt
python client.py
```

# Docker installation

**`report.txt` will be now saved to your current dir as `report_from_docker.txt`. The file WILL be overwritten after restarting the docker.**


### Download the docker
```
cd /tmp
git clone https://github.com/Jak0ub/Cli_Chatter
cd Cli_Chatter
touch report_from_docker.txt
chmod 666 report_from_docker.txt
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