# CLI_Chatter

* E2EE CLI chat app created using python.
* Code is separated into multiple files for better modularity
* Program allows (default) 30 requests from each IP before shuting the IP down -> (default) 10 password attempts for each IP
* MitM attack is not problem. Each IP has unique code for authorization process generated based on your server-side code
* Server does not store any logs

> ⚠️ **Warning:**
>  Do not share your server-side code with everyone. The server uses `ast.literal_eval()` so APT could abuse this function for DoS purposes when server-side code is publicly known. The exploit is hard to replicate, but not impossible. The exploit could only shut down your server-side system so no RCE etc.


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
---
