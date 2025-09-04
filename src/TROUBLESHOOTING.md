# Deployment Troubleshooting Guide

## Common Issues and Solutions

### 1. JSON Loading Error ("Error loading wardrobe data")

**Symptoms:**
- Error message: "Error loading wardrobe data"
- Console shows HTML instead of JSON
- 404 error for wardrobe_data.json

**Solutions:**

1. **Check file permissions:**
   ```bash
   chmod 644 /path/to/website/wardrobe_data.json
   ```

2. **Verify nginx configuration:**
   ```bash
   # Test nginx config
   sudo nginx -t
   
   # Reload nginx
   sudo systemctl reload nginx
   ```

3. **Check nginx error logs:**
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

4. **Verify file exists:**
   ```bash
   ls -la /path/to/website/wardrobe_data.json
   curl http://your-domain.com/wardrobe_data.json
   ```

### 2. CSP (Content Security Policy) Errors

**Symptoms:**
- Console errors about blocked fonts or scripts
- Missing fonts from CDN

**Solution:**
Update nginx config CSP header to allow external resources:
```nginx
add_header Content-Security-Policy "default-src 'self' https://unpkg.com; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com; img-src 'self' data:; font-src 'self' https://unpkg.com data:;" always;
```

### 3. Images Not Loading

**Symptoms:**
- Broken image icons
- 404 errors for image files

**Solutions:**

1. **Check file structure:**
   ```bash
   ls -la /path/to/website/images/thumbs/
   ls -la /path/to/website/images/full/
   ```

2. **Verify permissions:**
   ```bash
   chmod -R 644 /path/to/website/images/
   chmod 755 /path/to/website/images/
   chmod 755 /path/to/website/images/thumbs/
   chmod 755 /path/to/website/images/full/
   ```

### 4. Favicon 404 Error

**Symptoms:**
- Console error for favicon.ico or favicon.svg

**Solution:**
The updated generator now creates a favicon automatically. If missing:
```bash
# Regenerate site
uv run generate_site.py
```

### 5. React App Not Loading

**Symptoms:**
- Blank page
- Console errors about React not defined

**Solutions:**

1. **Check internet connection** (React is loaded from CDN)
2. **Verify HTML structure** - ensure all script tags are present
3. **Check browser compatibility** (use modern browser)

### 6. SPA Routing Issues

**Symptoms:**
- Direct URLs to items return 404
- Back/forward buttons don't work

**Solution:**
Ensure nginx config has the SPA routing section:
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

## Diagnostic Commands

### Check Nginx Status
```bash
sudo systemctl status nginx
sudo nginx -t
```

### Test JSON Endpoint
```bash
curl -I http://your-domain.com/wardrobe_data.json
curl http://your-domain.com/wardrobe_data.json | head -20
```

### Check File Permissions
```bash
ls -la /path/to/website/
find /path/to/website/ -type f -name "*.json" -exec ls -la {} \;
```

### Monitor Logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Complete Nginx Configuration Test

Save this as a minimal test config:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/website;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location ~ \.json$ {
        add_header Content-Type application/json;
        try_files $uri =404;
    }
}
```

## Browser Developer Tools

1. **Open DevTools** (F12)
2. **Check Console tab** for JavaScript errors
3. **Check Network tab** to see failed requests
4. **Check Sources tab** to verify files are loaded

## Contact Information

If issues persist:
1. Check nginx error logs first
2. Verify all files copied correctly
3. Test with simple HTTP server: `python3 -m http.server 8000` in website directory
4. Compare working local version with deployed version