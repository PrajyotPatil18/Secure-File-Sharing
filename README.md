# Secure File Sharing Platform

A lightweight, secure file sharing platform built with Flask and AES-256 encryption, optimized for local network multi-device access. Files remain encrypted on the server and are only decrypted temporarily during authorized downloads.

## Features

- **AES-256 Encryption**: Military-grade encryption for all stored files
- **Password Protection**: Optional password protection for download links
- **Expiring Links**: Automatic link expiration with customizable time limits
- **Local Network Ready**: Configured for multi-device access on same network
- **Minimal UI**: Clean, simple HTML interface with no unnecessary styling
- **Request Logging**: Comprehensive logging of all file operations
- **Cross-Platform**: Works with Linux server and Windows clients

## Security Features

- Files are encrypted using AES-256-CBC mode
- Password-protected files use PBKDF2 key derivation (100,000 iterations)
- Secure random link generation using `secrets.token_urlsafe()`
- Files remain encrypted on disk at all times
- Temporary decryption only during authorized downloads
- Automatic cleanup of expired links and files

## Project Structure

```
Secure-File-Sharing/
├── app.py              # Main Flask application
├── encryption.py        # AES encryption/decryption module
├── requirements.txt     # Python dependencies
├── links.json          # Download links metadata
├── file_sharing.log    # Application logs
├── encrypted/          # Encrypted file storage
├── templates/          # HTML templates
│   ├── upload.html
│   ├── upload_success.html
│   ├── download.html
│   ├── links.html
│   └── error.html
└── README.md
```

## Installation

### Linux Server Setup

1. **Clone or download the project**
```bash
cd /path/to/Secure-File-Sharing
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Start the server**
```bash
python3 app.py
```

The server will start on `http://0.0.0.0:5000` making it accessible from any device on the same network.

### Windows Client Access

1. **Find the server IP address** on the Linux machine:
```bash
ip addr show | grep inet
```
Look for the local network IP (usually 192.168.x.x or 10.x.x.x)

2. **Access from Windows browsers**:
```
http://SERVER_IP:5000
```
Replace `SERVER_IP` with the actual Linux server IP address.

## Usage

### Uploading Files

1. Open the web interface at `http://SERVER_IP:5000`
2. Select a file to upload (supports: txt, pdf, png, jpg, jpeg, gif, doc, docx, zip, rar, mp4, avi, mov)
3. Optionally set a password for additional security
4. Set expiration time (1-168 hours)
5. Click "Upload & Encrypt"

### Downloading Files

1. Use the provided download link
2. If password protected, enter the password
3. Click "Download File"

### Managing Links

- View all active links at `http://SERVER_IP:5000/links`
- Links automatically expire and are cleaned up
- Encrypted files are automatically deleted when links expire

## Configuration

### Security Settings

- **Max file size**: 100MB (configurable in `app.py`)
- **Default expiration**: 24 hours
- **Encryption**: AES-256-CBC
- **Key derivation**: PBKDF2 with 100,000 iterations

### Network Configuration

The server is configured to listen on `0.0.0.0:5000` for network access. To change:

```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

### File Type Restrictions

Allowed file types are defined in `ALLOWED_EXTENSIONS`:
```python
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip', 'rar', 'mp4', 'avi', 'mov'}
```

## Security Considerations

1. **Network Security**: This is designed for trusted local networks. For internet access, consider:
   - Adding HTTPS/TLS
   - Implementing user authentication
   - Using a reverse proxy (nginx/Apache)

2. **Password Security**: 
   - Use strong passwords for protected files
   - Passwords are never stored, only used for key derivation

3. **File Storage**:
   - All files are encrypted at rest
   - Temporary decryption only occurs in memory during download

4. **Logging**:
   - All operations are logged with IP addresses
   - Review logs regularly for suspicious activity

## Troubleshooting

### Common Issues

1. **Cannot access from other devices**:
   - Check firewall settings on Linux server
   - Verify server is running on `0.0.0.0`
   - Confirm IP address is correct

2. **Upload fails**:
   - Check file size limit (100MB)
   - Verify file type is allowed
   - Check server logs for errors

3. **Download fails**:
   - Verify link hasn't expired
   - Check password if protected
   - Ensure file wasn't manually deleted

### Log Files

Check `file_sharing.log` for detailed error information:
```bash
tail -f file_sharing.log
```

## Development

### Adding New Features

The modular structure makes it easy to extend:

- **Encryption**: Modify `encryption.py` for different algorithms
- **Routes**: Add new endpoints in `app.py`
- **Templates**: Update HTML in `templates/` directory
- **Storage**: Change file storage locations in configuration

### Testing

Test with different file types and sizes:
```bash
# Test small text file
echo "test" > test.txt

# Test larger file
dd if=/dev/urandom of=test.bin bs=1M count=10
```

## Dependencies

- Flask 3.1.3 - Web framework
- pycryptodome 3.23.0 - Cryptographic library
- Werkzeug 3.1.8 - WSGI utilities

## License

This project is for educational and internship demonstration purposes. Use responsibly and ensure proper security measures for production use.

## Support

For issues or questions:
1. Check the log files for error details
2. Verify network connectivity
3. Ensure all dependencies are installed
4. Review configuration settings