

```markdown
# ⚡ Project Dead Drop: Cyberpunk File & Message Share

A secure, Flask-based web application designed for encrypted file sharing and "burn-after-reading" text drops. Built featuring a retro cyberpunk aesthetic, this utility ensures that your data is securely encrypted on the fly and never stored exposed on a server disk.

---

## 🚀 Core Features

* **Zero-Knowledge File Uploads:** Uploaded files are immediately encrypted using **Fernet (AES-128 in CBC mode)** with `PBKDF2HMAC` key derivation. The original unencrypted files are scrubbed from the server instantly.
* **Self-Destructing Share Links:** Generate highly secure tracking tokens for files that automatically expire after **7 days** or **100 downloads**.
* **Burn-After-Reading Messages:** Drop text messages encrypted by a custom password. The moment the recipient decrypts and reads it, the message is permanently expunged from server memory.
* **In-Memory Streaming:** Files are decrypted directly in the server's RAM and streamed straight to your browser, preventing any unencrypted footprints on the host filesystem.
* **Built-in Rate Limiting:** Safe protection with a strict **16MB** maximum file upload restriction.

---

## 🛠️ System Architecture & Workflow

The diagram below illustrates how data flows securely through the application without ever touching the server's hard drive in an unencrypted state:


```

[ User File Upload ]
│
▼
[ Flask Controller ] ──(Generates Unique Salt)──► [ PBKDF2HMAC Key Derivation ]
│                                                      │
▼                                                      ▼
[ Scrub Original File ] ◄──(Encrypts File Data)─────── [ Fernet Engine ]
│
▼
[ Store .enc & .meta on Disk ]
│
▼
[ In-Memory Decryption Stream via BytesIO ] ──► [ Secure User Download ]

```

---

## ⚙️ Installation & Local Setup

### Prerequisites
Make sure you have **Python 3.8+** installed on your machine.

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name

```

### 2. Install Dependencies

Install the required encryption and web framework packages:

```bash
pip install flask cryptography werkzeug

```

### 3. Environment Configuration

For a development environment, the application will default to safe local values. For deployment, configure your unique environment variable:

```bash
# On Linux/macOS
export SECRET_KEY="your-super-secure-production-key"

# On Windows (CMD)
set SECRET_KEY="your-super-secure-production-key"

```

### 4. Fire Up the Server

Run the local development server:

```bash
python app.py

```

Open your browser and navigate to **`http://127.0.0.1:5000`** to view the cyberpunk command interface.

---

## 📂 Project Structure

```text
├── app.py                # Main Flask application & cryptographic backend
├── drop_zone/            # Storage folder for encrypted payload files (.enc & .meta)
├── keys/                 # Designated cryptographic key materials directory
└── templates/            # Frontend Cyberpunk UI elements
    ├── index.html        # Main dashboard terminal
    ├── files.html        # Directory for encrypted active files
    ├── messages.html     # Text drop dashboard
    ├── success.html      # Post-upload landing and link-generation page
    └── share_status.html # Live link telemetry tracker

```

---

## ⚠️ Important Security Notes & Disclaimers

> ❗ **Hackathon Context Warning:** > * **Volatile Memory:** This application stores message drops and active sharing tracking links in global Python dictionaries (`in-memory`). If the server restarts, all active text drops and shared link tracking tokens are wiped out.
> * **Encryption Keying:** File encryption currently uses a unique cryptographic salt per file but relies on a standard global framework password. For a robust production launch, update `encrypt_file()` to handle dynamic, user-input passwords.
> 
> 

```

```
