# Static Website Deployment Guide

Your wardrobe website is now configured as a fully static site that can be deployed to any web server without requiring Python or Node.js runtime.

## 📁 Static Site Structure

After running the generator, your `output/website/` directory contains:

```
output/website/
├── index.html              # Main HTML page
├── styles.css              # CSS with dark mode support
├── wardrobe_data.json      # Clothing item data
├── images/                 # All processed images
│   ├── thumbs/            # Thumbnail images
│   └── full/              # Full-size images
└── src/
    └── App.js             # React application
```

## 🚀 Deployment Options

### Option 1: Nginx (Recommended)

1. **Copy files to your server**:
   ```bash
   # Upload the website directory to your server
   rsync -avz output/website/ user@your-server:/var/www/wardrobe/
   ```

2. **Configure Nginx**:
   ```bash
   # Copy the provided nginx config
   sudo cp nginx-wardrobe.conf /etc/nginx/sites-available/wardrobe
   
   # Edit the configuration file
   sudo nano /etc/nginx/sites-available/wardrobe
   
   # Update these lines:
   # - server_name your-domain.com;  # Replace with your domain
   # - root /var/www/wardrobe;       # Update to your actual path
   ```

3. **Enable the site**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/wardrobe /etc/nginx/sites-enabled/
   sudo nginx -t  # Test configuration
   sudo systemctl reload nginx
   ```

### Option 2: Apache

Create a `.htaccess` file in your website directory:

```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.html [L]

# Enable compression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/xml
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE application/xml
    AddOutputFilterByType DEFLATE application/xhtml+xml
    AddOutputFilterByType DEFLATE application/rss+xml
    AddOutputFilterByType DEFLATE application/javascript
    AddOutputFilterByType DEFLATE application/x-javascript
</IfModule>

# Cache static assets
<IfModule mod_expires.c>
    ExpiresActive on
    ExpiresByType image/jpg "access plus 1 year"
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType image/gif "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType text/css "access plus 1 month"
    ExpiresByType application/pdf "access plus 1 month"
    ExpiresByType text/javascript "access plus 1 month"
    ExpiresByType application/javascript "access plus 1 month"
</IfModule>
```

### Option 3: Static Site Hosts

Upload the `output/website/` directory to any of these services:

- **Netlify**: Drag and drop the folder at [netlify.com](https://netlify.com)
- **Vercel**: Connect your Git repository at [vercel.com](https://vercel.com)
- **GitHub Pages**: Push to a GitHub repository and enable Pages
- **AWS S3 + CloudFront**: For scalable hosting

## 🔄 Updates and Regeneration

To update your website with new photos:

1. **Add new photos** to `source_photos/` directories
2. **Regenerate the site**:
   ```bash
   uv run generate_site.py
   ```
3. **Upload updated files**:
   ```bash
   # Upload only changed files
   rsync -avz --delete output/website/ user@your-server:/var/www/wardrobe/
   ```

## 🛠 Customization for Production

### Performance Optimizations

1. **Enable HTTP/2** in your nginx/apache configuration
2. **Use a CDN** for faster global delivery
3. **Optimize images further** if needed:
   ```bash
   # Optional: Further compress images
   find output/website/images -name "*.jpg" -exec jpegoptim --max=85 {} \;
   ```

### Security Headers (Already included in nginx config)

- Content Security Policy (CSP)
- X-Frame-Options
- X-XSS-Protection
- X-Content-Type-Options

### SSL/HTTPS Setup

For production, enable HTTPS:

1. **Get SSL certificate** (Let's Encrypt recommended):
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

2. **Uncomment HTTPS section** in nginx config and update paths

## 📊 Monitoring

Consider adding:
- **Analytics**: Google Analytics, Plausible, or similar
- **Error monitoring**: Sentry or similar service
- **Uptime monitoring**: UptimeRobot or similar

## 🎯 Features Included

✅ **Fully static** - No server-side processing required  
✅ **Dark mode support** - Automatically detects system preference  
✅ **Responsive design** - Works on all devices  
✅ **SEO friendly** - Proper meta tags and structure  
✅ **Fast loading** - Optimized images and caching headers  
✅ **Single Page App** - Smooth navigation with React  

Your wardrobe website is now ready for production deployment! 🚀