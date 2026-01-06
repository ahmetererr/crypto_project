# Güvenli E-posta Sistemi - Detaylı Proje Sunumu

## 1. PROJE GENEL BAKIŞ

### 1.1 Proje Amacı
Bu proje, kullanıcı kimlik doğrulama, mesaj gizliliği, bütünlük doğrulama ve gönderen kimlik doğrulama için kriptografik teknikler kullanan güvenli bir e-posta sistemidir.

### 1.2 Temel Özellikler
- **Kullanıcı Kaydı ve Kimlik Doğrulama**: bcrypt ile güvenli şifre hashleme
- **Mesaj Gizliliği**: AES-256-CBC simetrik şifreleme + RSA ile anahtar şifreleme
- **Mesaj Bütünlüğü**: SHA-256 hash ile bütünlük kontrolü
- **Dijital İmzalar**: RSA-PSS ile gönderen kimlik doğrulama
- **Veritabanı Depolama**: SQLite ile güvenli veri saklama

---

## 2. PROJE YAPISI

### 2.1 Dosya Organizasyonu
```
crypto_project/
├── crypto_utils.py      # Kriptografik işlemler
├── database.py          # Veritabanı işlemleri
├── email_system.py      # E-posta sistemi mantığı
├── main.py              # CLI arayüzü
├── test_system.py       # Test scripti
├── requirements.txt     # Python bağımlılıkları
├── run.sh               # Çalıştırma scripti
├── README.md            # Dokümantasyon
└── secure_email.db      # SQLite veritabanı (otomatik oluşur)
```

### 2.2 Modül İlişkileri
```
main.py (CLI)
    ↓
email_system.py (Business Logic)
    ↓
database.py (Data Layer)    crypto_utils.py (Crypto Layer)
    ↓                              ↓
SQLite Database              Cryptographic Operations
```

---

## 3. DETAYLI MODÜL AÇIKLAMALARI

### 3.1 `crypto_utils.py` - Kriptografik İşlemler

#### 3.1.1 Sınıf: `CryptoUtils`
Tüm kriptografik işlemleri içeren statik metodlar sınıfı.

#### 3.1.2 Şifre Yönetimi Fonksiyonları

**`hash_password(password: str) -> str`**
- **Amaç**: Şifreyi güvenli şekilde hashler
- **Algoritma**: bcrypt
- **Salt**: Otomatik üretilir (her hash için farklı)
- **Çıktı**: Base64 encoded hash string
- **Güvenlik**: Rainbow table saldırılarına karşı koruma

**`verify_password(password: str, password_hash: str) -> bool`**
- **Amaç**: Girilen şifreyi hash ile karşılaştırır
- **Yöntem**: bcrypt.checkpw()
- **Çıktı**: Boolean (True/False)

#### 3.1.3 RSA Anahtar Yönetimi

**`generate_rsa_key_pair() -> (private_key, public_key)`**
- **Anahtar boyutu**: 2048 bit
- **Public exponent**: 65537 (Fermat sayısı)
- **Backend**: default_backend (OpenSSL)
- **Kullanım**: Her kullanıcı için kayıt sırasında üretilir

**`serialize_public_key(public_key) -> str`**
- **Format**: PEM (Privacy-Enhanced Mail)
- **Encoding**: UTF-8
- **Format tipi**: SubjectPublicKeyInfo
- **Kullanım**: Veritabanına kaydetmek için

**`serialize_private_key(private_key) -> str`**
- **Format**: PEM
- **Encoding**: PKCS8
- **Şifreleme**: Yok (production'da ek şifreleme önerilir)
- **Kullanım**: Veritabanına kaydetmek için

**`deserialize_public_key(public_key_str: str) -> PublicKey`**
- **Amaç**: PEM string'den public key objesi oluşturur
- **Kullanım**: Şifreleme ve imza doğrulama için

**`deserialize_private_key(private_key_str: str) -> PrivateKey`**
- **Amaç**: PEM string'den private key objesi oluşturur
- **Kullanım**: Deşifreleme ve imzalama için

#### 3.1.4 Simetrik Şifreleme (AES)

**`generate_symmetric_key() -> bytes`**
- **Boyut**: 32 byte (256 bit)
- **Yöntem**: os.urandom() (kriptografik olarak güvenli rastgele)
- **Kullanım**: Her mesaj için yeni anahtar üretilir

**`encrypt_symmetric(message: str, key: bytes) -> (ciphertext, iv)`**
- **Algoritma**: AES-256-CBC
- **IV (Initialization Vector)**: 16 byte, rastgele üretilir
- **Padding**: PKCS7 (16 byte blok boyutuna tamamlama)
- **Çıktı**: Base64 encoded ciphertext ve IV
- **Güvenlik**: Aynı mesaj farklı IV ile farklı şifrelenir

**`decrypt_symmetric(encrypted_message: str, iv_str: str, key: bytes) -> str`**
- **Amaç**: Şifrelenmiş mesajı çözer
- **İşlemler**:
  1. Base64 decode
  2. IV ve ciphertext'i ayır
  3. AES-CBC ile deşifrele
  4. Padding'i kaldır
  5. UTF-8 decode

#### 3.1.5 Asimetrik Şifreleme (RSA)

**`encrypt_with_public_key(data: bytes, public_key) -> str`**
- **Algoritma**: RSA-OAEP (Optimal Asymmetric Encryption Padding)
- **Hash**: SHA-256
- **MGF**: MGF1 (Mask Generation Function)
- **Çıktı**: Base64 encoded encrypted data
- **Kullanım**: Simetrik anahtarı alıcının public key'i ile şifreleme

**`decrypt_with_private_key(encrypted_data: str, private_key) -> bytes`**
- **Amaç**: RSA ile şifrelenmiş veriyi çözer
- **Padding**: OAEP (RSA-OAEP ile aynı parametreler)
- **Kullanım**: Alıcı kendi private key'i ile simetrik anahtarı çözer

#### 3.1.6 Mesaj Bütünlüğü (Hash)

**`hash_message(message: str) -> str`**
- **Algoritma**: SHA-256
- **Çıktı**: Base64 encoded hash (32 byte)
- **Kullanım**: Mesajın değiştirilip değiştirilmediğini kontrol etmek için
- **Özellik**: Deterministik (aynı mesaj = aynı hash)

#### 3.1.7 Dijital İmza

**`sign_message(message_hash: str, private_key) -> str`**
- **Algoritma**: RSA-PSS (Probabilistic Signature Scheme)
- **Hash**: SHA-256
- **Salt length**: MAX_LENGTH (maksimum güvenlik)
- **Çıktı**: Base64 encoded signature
- **Kullanım**: Gönderen mesaj hash'ini kendi private key'i ile imzalar

**`verify_signature(message_hash: str, signature: str, public_key) -> bool`**
- **Amaç**: Dijital imzayı doğrular
- **İşlem**:
  1. Signature'ı decode et
  2. Public key ile verify et
  3. Hata varsa False, yoksa True döndür
- **Güvenlik**: İmza doğrulanamazsa mesaj gönderen tarafından gönderilmemiş olabilir

---

### 3.2 `database.py` - Veritabanı İşlemleri

#### 3.2.1 Sınıf: `Database`
SQLite veritabanı işlemlerini yönetir.

#### 3.2.2 Veritabanı Şeması

**Tablo 1: `users`**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```
- **Amaç**: Kullanıcı bilgilerini saklar
- **username**: Benzersiz kullanıcı adı
- **password_hash**: bcrypt ile hashlenmiş şifre
- **created_at**: Kayıt zamanı

**Tablo 2: `public_keys`**
```sql
CREATE TABLE public_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    public_key TEXT NOT NULL,
    FOREIGN KEY (username) REFERENCES users(username)
)
```
- **Amaç**: Kullanıcıların public key'lerini saklar
- **public_key**: PEM formatında RSA public key
- **Kullanım**: Mesaj şifreleme ve imza doğrulama için

**Tablo 3: `private_keys`**
```sql
CREATE TABLE private_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    private_key TEXT NOT NULL,
    FOREIGN KEY (username) REFERENCES users(username)
)
```
- **Amaç**: Kullanıcıların private key'lerini saklar
- **private_key**: PEM formatında RSA private key
- **Güvenlik**: Production'da ek şifreleme önerilir

**Tablo 4: `messages`**
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT NOT NULL,
    recipient TEXT NOT NULL,
    encrypted_content TEXT NOT NULL,
    encrypted_symmetric_key TEXT NOT NULL,
    message_hash TEXT NOT NULL,
    digital_signature TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender) REFERENCES users(username),
    FOREIGN KEY (recipient) REFERENCES users(username)
)
```
- **encrypted_content**: IV:Base64(ciphertext) formatında
- **encrypted_symmetric_key**: RSA ile şifrelenmiş simetrik anahtar
- **message_hash**: SHA-256 hash
- **digital_signature**: RSA-PSS imza

#### 3.2.3 Veritabanı Fonksiyonları

**`init_database()`**
- **Amaç**: Veritabanı tablolarını oluşturur
- **Çalışma**: İlk çağrıldığında tabloları oluşturur, varsa dokunmaz

**`add_user(username, password_hash) -> bool`**
- **Amaç**: Yeni kullanıcı ekler
- **Hata**: Username zaten varsa False döner

**`get_user_password_hash(username) -> Optional[str]`**
- **Amaç**: Kullanıcının şifre hash'ini getirir
- **Kullanım**: Login işlemi için

**`user_exists(username) -> bool`**
- **Amaç**: Kullanıcının var olup olmadığını kontrol eder

**`save_public_key(username, public_key) -> bool`**
- **Amaç**: Public key'i kaydeder
- **Özellik**: INSERT OR REPLACE (güncelleme destekler)

**`save_private_key(username, private_key) -> bool`**
- **Amaç**: Private key'i kaydeder

**`get_public_key(username) -> Optional[str]`**
- **Amaç**: Kullanıcının public key'ini getirir

**`get_private_key(username) -> Optional[str]`**
- **Amaç**: Kullanıcının private key'ini getirir

**`save_message(...) -> bool`**
- **Amaç**: Şifrelenmiş mesajı kaydeder
- **Parametreler**: sender, recipient, encrypted_content, encrypted_symmetric_key, message_hash, digital_signature

**`get_messages_for_user(username) -> List[Tuple]`**
- **Amaç**: Kullanıcının gelen mesajlarını listeler
- **Sıralama**: created_at DESC (en yeni önce)

---

### 3.3 `email_system.py` - E-posta Sistemi Mantığı

#### 3.3.1 Sınıf: `EmailSystem`
E-posta sisteminin ana mantığını yönetir.

#### 3.3.2 Kullanıcı Yönetimi

**`register_user(username, password) -> (bool, str)`**
- **İşlem adımları**:
  1. Kullanıcı adı kontrolü (zaten varsa hata)
  2. Şifreyi bcrypt ile hashle
  3. Kullanıcıyı veritabanına ekle
  4. RSA key pair üret (2048 bit)
  5. Public ve private key'leri serialize et
  6. Key'leri veritabanına kaydet
- **Çıktı**: (True, "User registered successfully") veya (False, hata mesajı)

**`authenticate_user(username, password) -> (bool, str)`**
- **İşlem adımları**:
  1. Kullanıcının password hash'ini getir
  2. Kullanıcı yoksa hata döndür
  3. bcrypt ile şifreyi doğrula
  4. Başarılı/başarısız sonucu döndür

#### 3.3.3 Mesaj Gönderme

**`send_email(sender, recipient, message) -> (bool, str)`**
- **İşlem adımları**:
  1. Gönderen ve alıcı kontrolü
  2. Alıcının public key'ini al
  3. Gönderenin private key'ini al
  4. 256-bit simetrik anahtar üret
  5. Mesajı AES-256-CBC ile şifrele (IV ile birlikte)
  6. Simetrik anahtarı alıcının public key'i ile RSA-OAEP ile şifrele
  7. Mesajın SHA-256 hash'ini hesapla
  8. Hash'i gönderenin private key'i ile RSA-PSS ile imzala
  9. IV ve ciphertext'i birleştir (IV:ciphertext)
  10. Veritabanına kaydet
- **Güvenlik özellikleri**:
  - Mesaj sadece alıcı tarafından okunabilir
  - Mesaj değiştirilemez (hash kontrolü)
  - Gönderen kimliği doğrulanabilir (dijital imza)

#### 3.3.4 Mesaj Alma ve Doğrulama

**`receive_email(username, message_id) -> (bool, Optional[Dict], str)`**
- **İşlem adımları**:
  1. Mesajı veritabanından getir
  2. Alıcının private key'ini al
  3. Gönderenin public key'ini al
  4. Simetrik anahtarı RSA ile çöz (alıcının private key'i ile)
  5. Mesajı AES ile çöz (IV ve ciphertext'i ayır)
  6. Mesajın hash'ini hesapla
  7. Hash'i veritabanındaki hash ile karşılaştır (bütünlük kontrolü)
  8. Dijital imzayı doğrula (gönderenin public key'i ile)
  9. Sonuçları döndür
- **Çıktı formatı**:
```python
{
    'id': message_id,
    'sender': sender_username,
    'recipient': recipient_username,
    'message': decrypted_message,
    'created_at': timestamp,
    'integrity_verified': True/False,
    'signature_verified': True/False
}
```

**`list_messages(username) -> List[Dict]`**
- **Amaç**: Kullanıcının mesaj listesini getirir (şifreleme yapmadan)
- **Çıktı**: Mesaj ID, gönderen, alıcı, tarih

---

### 3.4 `main.py` - Komut Satırı Arayüzü

#### 3.4.1 Sınıf: `EmailClient`
Kullanıcı arayüzünü yönetir.

#### 3.4.2 Menü Sistemi

**Giriş yapılmamış menü:**
1. Register
2. Login
3. Exit

**Giriş yapılmış menü:**
1. Send Email
2. View Inbox
3. Read Email
4. Logout
5. Exit

#### 3.4.3 Fonksiyonlar

**`register()`**
- Kullanıcıdan username ve password alır
- EmailSystem.register_user() çağırır
- Sonucu gösterir

**`login()`**
- Kullanıcıdan username ve password alır
- EmailSystem.authenticate_user() çağırır
- Başarılıysa current_user'ı set eder

**`send_email()`**
- Kullanıcıdan recipient ve message alır
- EmailSystem.send_email() çağırır
- Şifreleme ve imzalama bilgisini gösterir

**`view_inbox()`**
- EmailSystem.list_messages() çağırır
- Mesaj listesini gösterir

**`read_email()`**
- Kullanıcıdan message_id alır
- EmailSystem.receive_email() çağırır
- Mesajı, bütünlük ve imza doğrulama sonuçlarını gösterir

**`run()`**
- Ana döngü
- Menüyü gösterir, kullanıcı seçimini alır
- İlgili fonksiyonu çağırır

---

### 3.5 `test_system.py` - Test Scripti

#### 3.5.1 Test Senaryoları

**Test 1: Kullanıcı Kaydı**
- Alice ve Bob kaydedilir
- Her kayıt için RSA key pair üretilir

**Test 2: Kimlik Doğrulama**
- Doğru şifre ile login
- Yanlış şifre ile login (başarısız olmalı)

**Test 3: E-posta Gönderme**
- Alice'den Bob'a mesaj gönderilir
- Mesaj şifrelenir ve imzalanır

**Test 4: Mesaj Listeleme**
- Bob'un inbox'u kontrol edilir
- Mesaj sayısı doğrulanır

**Test 5: Mesaj Alma ve Doğrulama**
- Mesaj çözülür
- Orijinal mesaj ile karşılaştırılır
- Bütünlük ve imza doğrulaması kontrol edilir

---

## 4. GÜVENLİK MİMARİSİ

### 4.1 Şifreleme Akışı (Mesaj Gönderme)

```
1. Kullanıcı mesaj yazar
   ↓
2. 256-bit simetrik anahtar üretilir (os.urandom)
   ↓
3. Mesaj AES-256-CBC ile şifrelenir
   - IV (16 byte) rastgele üretilir
   - PKCS7 padding uygulanır
   ↓
4. Simetrik anahtar alıcının public key'i ile RSA-OAEP ile şifrelenir
   ↓
5. Mesajın SHA-256 hash'i hesaplanır
   ↓
6. Hash gönderenin private key'i ile RSA-PSS ile imzalanır
   ↓
7. Tüm veriler veritabanına kaydedilir:
   - encrypted_content (IV:ciphertext)
   - encrypted_symmetric_key
   - message_hash
   - digital_signature
```

### 4.2 Deşifreleme ve Doğrulama Akışı (Mesaj Alma)

```
1. Mesaj veritabanından getirilir
   ↓
2. Alıcının private key'i ile simetrik anahtar çözülür (RSA)
   ↓
3. IV ve ciphertext ayrılır
   ↓
4. Mesaj AES-256-CBC ile çözülür
   ↓
5. Mesajın hash'i hesaplanır
   ↓
6. Hash veritabanındaki hash ile karşılaştırılır
   - Eşleşmezse: Bütünlük hatası
   ↓
7. Dijital imza gönderenin public key'i ile doğrulanır
   - Doğrulanamazsa: İmza hatası
   ↓
8. Tüm kontroller geçerse mesaj gösterilir
```

### 4.3 Güvenlik Özellikleri

**1. Mesaj Gizliliği (Confidentiality)**
- AES-256-CBC simetrik şifreleme
- Her mesaj için yeni simetrik anahtar
- Simetrik anahtar RSA ile korunur
- Sadece alıcı okuyabilir

**2. Mesaj Bütünlüğü (Integrity)**
- SHA-256 hash ile kontrol
- Mesaj değiştirilirse hash eşleşmez
- Değişiklik tespit edilir

**3. Gönderen Kimlik Doğrulama (Authentication)**
- RSA-PSS dijital imza
- Gönderenin private key'i ile imzalanır
- Alıcı public key ile doğrular
- Sahte gönderen tespit edilir

**4. Şifre Güvenliği**
- bcrypt hash (salt ile)
- Plaintext şifre saklanmaz
- Rainbow table saldırılarına karşı korumalı

**5. Anahtar Yönetimi**
- Her kullanıcı için benzersiz RSA key pair
- 2048-bit RSA (güvenli)
- Public key paylaşılır, private key gizli tutulur

---

## 5. KRİPTOGRAFİK ALGORİTMALAR DETAYI

### 5.1 AES-256-CBC
- **AES**: Advanced Encryption Standard
- **256-bit**: Anahtar boyutu
- **CBC**: Cipher Block Chaining mode
- **IV**: Her şifreleme için farklı IV (aynı mesaj farklı şifrelenir)
- **Padding**: PKCS7 (16 byte blok boyutuna tamamlama)

### 5.2 RSA
- **Key Size**: 2048 bit
- **Public Exponent**: 65537
- **OAEP Padding**: Şifreleme için (optimal güvenlik)
- **PSS Padding**: İmza için (probabilistic signature)

### 5.3 SHA-256
- **Hash Function**: Secure Hash Algorithm 256-bit
- **Çıktı**: 32 byte (256 bit)
- **Özellik**: Deterministik, tek yönlü, çarpışma direnci

### 5.4 bcrypt
- **Password Hashing**: Adaptive hash function
- **Salt**: Otomatik üretilir
- **Cost Factor**: Varsayılan (zaman içinde artırılabilir)
- **Güvenlik**: Rainbow table saldırılarına karşı korumalı

---

## 6. VERİ AKIŞI DİYAGRAMI

### 6.1 Kayıt İşlemi
```
Kullanıcı → username, password
    ↓
EmailSystem.register_user()
    ↓
┌─────────────────────────┐
│ 1. Password hash (bcrypt)│
│ 2. RSA key pair üret     │
│ 3. Keys serialize        │
└─────────────────────────┘
    ↓
Database.add_user()
Database.save_public_key()
Database.save_private_key()
    ↓
SQLite Database
```

### 6.2 Mesaj Gönderme İşlemi
```
Kullanıcı → sender, recipient, message
    ↓
EmailSystem.send_email()
    ↓
┌─────────────────────────────────────┐
│ 1. Generate symmetric key (256-bit) │
│ 2. Encrypt message (AES-256-CBC)    │
│ 3. Encrypt key (RSA-OAEP)           │
│ 4. Hash message (SHA-256)           │
│ 5. Sign hash (RSA-PSS)              │
└─────────────────────────────────────┘
    ↓
Database.save_message()
    ↓
SQLite Database (encrypted)
```

### 6.3 Mesaj Alma İşlemi
```
Kullanıcı → username, message_id
    ↓
EmailSystem.receive_email()
    ↓
Database.get_messages_for_user()
    ↓
┌─────────────────────────────────────┐
│ 1. Decrypt symmetric key (RSA)      │
│ 2. Decrypt message (AES-256-CBC)    │
│ 3. Compute hash (SHA-256)          │
│ 4. Verify hash (integrity check)   │
│ 5. Verify signature (RSA-PSS)       │
└─────────────────────────────────────┘
    ↓
Decrypted message + verification results
```

---

## 7. HATA YÖNETİMİ

### 7.1 Hata Senaryoları

**Kayıt Hataları:**
- Username zaten varsa → "Username already exists"
- Veritabanı hatası → "Failed to register user"

**Giriş Hataları:**
- Kullanıcı yoksa → "User does not exist"
- Yanlış şifre → "Invalid password"

**Mesaj Gönderme Hataları:**
- Gönderen/alıcı yoksa → "Sender/Recipient does not exist"
- Public key bulunamazsa → "Recipient's public key not found"
- Veritabanı hatası → "Failed to save message"

**Mesaj Alma Hataları:**
- Mesaj bulunamazsa → "Message not found"
- Private key bulunamazsa → "Private key not found"
- Bütünlük hatası → "Message integrity verification failed"
- İmza hatası → "Digital signature verification failed"
- Deşifreleme hatası → "Error decrypting message"

---

## 8. KULLANIM ÖRNEKLERİ

### 8.1 Kullanıcı Kaydı
```python
email_system = EmailSystem()
success, message = email_system.register_user("alice", "password123")
# success = True
# message = "User registered successfully"
# RSA key pair otomatik üretilir ve kaydedilir
```

### 8.2 Mesaj Gönderme
```python
success, message = email_system.send_email(
    "alice", 
    "bob", 
    "Hello Bob! This is a secret message."
)
# Mesaj otomatik olarak:
# - AES-256-CBC ile şifrelenir
# - Simetrik anahtar Bob'un public key'i ile şifrelenir
# - SHA-256 hash hesaplanır
# - Hash Alice'in private key'i ile imzalanır
# - Veritabanına kaydedilir
```

### 8.3 Mesaj Alma
```python
success, email_data, message = email_system.receive_email("bob", message_id)
# email_data = {
#     'id': 1,
#     'sender': 'alice',
#     'recipient': 'bob',
#     'message': 'Hello Bob! This is a secret message.',
#     'created_at': '2024-01-01 12:00:00',
#     'integrity_verified': True,
#     'signature_verified': True
# }
```

---

## 9. GÜVENLİK NOTLARI VE ÖNERİLER

### 9.1 Mevcut Güvenlik Özellikleri
- ✅ Tüm kriptografik işlemler güvenli algoritmalar kullanır
- ✅ Şifreler plaintext saklanmaz
- ✅ Mesajlar end-to-end şifrelenir
- ✅ Dijital imzalar mesaj değişikliğini ve gönderen kimliğini doğrular

### 9.2 Production İçin Öneriler
1. **Private Key Şifreleme**: Private key'ler için ek şifreleme (password-based encryption)
2. **HTTPS**: Web arayüzü için HTTPS kullanımı
3. **Rate Limiting**: Brute force saldırılarına karşı rate limiting
4. **Session Yönetimi**: JWT tokens ile güvenli session yönetimi
5. **Logging ve Monitoring**: Güvenlik olaylarını loglama ve izleme
6. **Key Rotation**: Düzenli anahtar rotasyonu mekanizması
7. **Backup ve Recovery**: Yedekleme ve kurtarma stratejisi

---

## 10. PROJE ÖZETİ

### 10.1 Teknik Özellikler
- **Dil**: Python 3.7+
- **Veritabanı**: SQLite
- **Kriptografi**: cryptography library (OpenSSL backend)
- **Şifre Hashleme**: bcrypt
- **Arayüz**: Komut satırı (CLI)

### 10.2 Güvenlik Standartları
- **AES-256**: NIST onaylı simetrik şifreleme
- **RSA-2048**: Endüstri standardı asimetrik şifreleme
- **SHA-256**: Güvenli hash algoritması
- **RSA-PSS**: Güvenli dijital imza şeması
- **RSA-OAEP**: Güvenli şifreleme padding

### 10.3 Proje Başarı Kriterleri
- ✅ Kullanıcı kaydı ve kimlik doğrulama
- ✅ Mesaj gizliliği (sadece alıcı okuyabilir)
- ✅ Mesaj bütünlüğü (değişiklik tespit edilir)
- ✅ Gönderen kimlik doğrulama (dijital imza)
- ✅ Tüm testler başarılı

---

## 11. KOD ÖRNEKLERİ

### 11.1 Kullanıcı Kaydı Örneği
```python
from email_system import EmailSystem

# EmailSystem nesnesi oluştur
email_system = EmailSystem()

# Yeni kullanıcı kaydet
success, message = email_system.register_user("alice", "secure_password_123")
if success:
    print(f"✓ {message}")
    print("✓ RSA key pair oluşturuldu ve kaydedildi")
else:
    print(f"✗ Hata: {message}")
```

### 11.2 Mesaj Gönderme Örneği
```python
# Kullanıcı giriş yaptıktan sonra
sender = "alice"
recipient = "bob"
message = "Bu çok gizli bir mesajdır!"

success, result = email_system.send_email(sender, recipient, message)
if success:
    print(f"✓ {result}")
    print("✓ Mesaj şifrelendi ve imzalandı")
else:
    print(f"✗ Hata: {result}")
```

### 11.3 Mesaj Okuma Örneği
```python
# Mesaj listesini al
messages = email_system.list_messages("bob")
print(f"Bob'un {len(messages)} mesajı var")

# İlk mesajı oku
if messages:
    message_id = messages[0]['id']
    success, email_data, message = email_system.receive_email("bob", message_id)
    
    if success and email_data:
        print(f"\n✓ {message}")
        print(f"\nGönderen: {email_data['sender']}")
        print(f"Tarih: {email_data['created_at']}")
        print(f"Bütünlük Doğrulandı: {'✓' if email_data['integrity_verified'] else '✗'}")
        print(f"İmza Doğrulandı: {'✓' if email_data['signature_verified'] else '✗'}")
        print(f"\nMesaj:\n{email_data['message']}")
```

---

## 12. TEST SENARYOLARI

### 12.1 Test Çalıştırma
```bash
python test_system.py
```

### 12.2 Test Adımları
1. **Kullanıcı Kaydı Testi**: Alice ve Bob kaydedilir
2. **Kimlik Doğrulama Testi**: Doğru ve yanlış şifre ile login
3. **Mesaj Gönderme Testi**: Alice'den Bob'a mesaj gönderilir
4. **Mesaj Listeleme Testi**: Bob'un inbox'u kontrol edilir
5. **Mesaj Doğrulama Testi**: Mesaj çözülür ve doğrulanır

### 12.3 Beklenen Sonuçlar
- ✅ Tüm kullanıcılar başarıyla kaydedilir
- ✅ Doğru şifre ile login başarılı
- ✅ Yanlış şifre ile login başarısız
- ✅ Mesaj başarıyla gönderilir
- ✅ Mesaj başarıyla çözülür
- ✅ Bütünlük ve imza doğrulaması başarılı

---

## 13. KURULUM VE ÇALIŞTIRMA

### 13.1 Gereksinimler
- Python 3.7 veya üzeri
- pip (Python paket yöneticisi)

### 13.2 Kurulum Adımları
```bash
# 1. Virtual environment oluştur (önerilir)
python3 -m venv venv

# 2. Virtual environment'ı aktif et
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. Bağımlılıkları yükle
pip install -r requirements.txt
```

### 13.3 Çalıştırma
```bash
# Ana uygulamayı çalıştır
python main.py

# Veya test scriptini çalıştır
python test_system.py

# Veya run.sh scriptini kullan (Linux/macOS)
./run.sh
```

---

## 14. SONUÇ

Bu proje, modern kriptografik teknikler kullanarak güvenli bir e-posta sistemi oluşturmuştur. Sistem, mesaj gizliliği, bütünlük ve gönderen kimlik doğrulama gibi temel güvenlik gereksinimlerini karşılamaktadır. Tüm kriptografik işlemler endüstri standardı algoritmalar kullanılarak gerçekleştirilmiştir.

Proje, COMP 417 dersi kapsamında kriptografi prensiplerinin pratik uygulamasını göstermektedir ve gerçek dünya senaryolarına uyarlanabilir bir yapıya sahiptir.

---

**Hazırlayan**: [Proje Ekibi]  
**Tarih**: 2024  
**Ders**: COMP 417 - Kriptografi

