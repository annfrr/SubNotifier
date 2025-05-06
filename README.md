# SubNotifier

**SubNotifier** is a wildcard subdomain scanning and notification tool designed to help **bug bounty hunters**, **security researchers**, and **DevOps/security teams** monitor wildcard subdomains for a given root domain. It continuously scans a set of root domains for subdomains, stores discovered subdomains in a database, and notifies the user when new subdomains are detected.

I wanted notifications for newly created subdomains along with a neat setup for saving wildcard subdomains and providing easy access, so I built this.  Most commonly used notification tools are not easy to set up, and each time you need to enter the shell to access domains. Here, you can curl your subdomains to a file and start your tests—or add internal functions for more automation.

Notifications will be sent via email, and with continuous monitoring, it gives you the privilege of accessing untouched subdomains (fresh bounties).

---

## How to Start the Program

### 1. Clone the Repository

```bash
git clone https://github.com/annfrr/SubNotifier.git
cd SubNotifier
```

### 2. Setup Environment

* **Install Docker if not installed already**:

```bash
sudo apt install -y docker.io docker-compose 
```

* **Set up environment variables** in `docker-compose.yml` for domain and SMTP email settings.
* Make sure your domain's A record points to the public IP of the machine hosting SubNotifier.

Set these values:

```env
HOSTNAME=yourdomain
SSL_CONTACT_EMAIL=yourmail@gmail.com
```

**SMTP Configuration**

> I suggest creating a new Gmail account specifically for this purpose, as using an app password on your primary Gmail account is not recommended.
> How to get a Gmail app password: [https://support.google.com/mail/thread/205453566/how-to-generate-an-app-password?hl=en](https://support.google.com/mail/thread/205453566/how-to-generate-an-app-password?hl=en)

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=yourmail@gmail.com
SMTP_PASSWORD=app password
FROM_EMAIL=yourmail@gmail.com
TO_EMAIL=receivermail@gmail.com
```

### 3. Start Docker

```bash
sudo docker-compose up
```

* It takes some time to initialize, so don't worry.
* You will receive an admin password for API authorization (save it somewhere for easy access).
* Check yourdomain/docs for fastapi documentation.
* To start SubNotifier in the background permanently:

```bash
sudo docker-compose up -d
```

### 4. (Optional) Add API Keys to Subfinder Configuration

After the previous steps:

```bash
sudo docker exec -it subnotifier_web_1 /bin/bash
# Inside the container
subfinder    # This creates the config directory if it doesn't exist
nano /root/.config/subfinder/provider-config.yaml
```

Add your API keys for better coverage. You're good to go!

---
## How to use
![image](https://github.com/user-attachments/assets/c971b9b8-6dfa-435f-8f9b-d63d92d67f5f)

Functionalities are self-explanatory. First you add root domain using post request then it starts rest of processes. After addition it starts first scan after a minute.

## Entity-Relationship Diagram (ERD)

Below is a simple **ERD** that reflects the structure of the database and how the root domains and their subdomains are related.

### Tables:

1. **RootDomain**:

   * Stores the root domains (e.g., `example.com`).
   * Tracks the last scan time, next scan time, and scanning interval.

2. **Subdomain**:

   * Stores individual subdomains (e.g., `sub.example.com`).
   * Links to the root domain via a foreign key reference.

### ERD Diagram:

```
+-------------------+     +------------------+
|     RootDomain    |     |    Subdomain     |
+-------------------+     +------------------+
| domain (PK)       |<--->| id (PK)          |
| last_scan         |     | name             |
| next_scan         |     | root_domain_domain (FK) |
| scan_interval     |     | is_new           |
| is_scanning       |     |                  |
+-------------------+     +------------------+
```

* **RootDomain**: A table representing the root domains being monitored.
* **Subdomain**: A table representing all discovered subdomains for a given root domain.

The `RootDomain` table contains the domain name as its primary key. The `Subdomain` table contains subdomains linked to the `RootDomain` table via the `root_domain_domain` field (foreign key). Each subdomain also includes a flag (`is_new`) to indicate if it’s a new discovery.

---

## Key Technical Details

### Subdomain Scanning Logic

**Scheduled Scans**: The scanner performs a scan on each root domain every 12 hours by default. But this interval can be customized:

```json
{
  "domain": "rivian.com",
  "scan_interval": 12
}
```

* The `scan_interval` is set in hours.
* You can adjust the interval based on your needs, but keep in mind that Subfinder scans can take time and consume system resources.

### Important Functions

* **Subdomain Scan**: The core function uses Subfinder to perform the scan and add new subdomains to the database.
* **Deduplication**: After the first five scans, subdomains already stored in the database are not added again.
* **Notifications**: Any subdomains discovered during a scan will trigger an email notification to the user.

---

## Hosting in the Cloud

**SubNotifier** is designed to be cloud-ready. It can be deployed on various cloud providers (e.g., AWS, Azure, Google Cloud) using virtual machines or containers.

* **Docker Support**: The system is containerized with Docker, making it portable and easy to scale horizontally.
