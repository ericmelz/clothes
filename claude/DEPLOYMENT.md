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

## 🚀 Deployment

1. **Configure Nginx** (only needed once):
   ```bash
   # Copy the provided nginx config
   cp nginx-wardrobe.conf ~/Data/code/nginx-data/conf/sites-available/ericmelz.site.conf
   pushd $HOME/Data/code/nginx-data
   git status
   git add *
   git commit -m"Updated ericmelz.site to serve clothes"
   git push
   popd
   ```

1. **Copy files to your server**:
   ```bash
   # Copy site to nginx-data repo
   rsync -avz --delete output/website/ $HOME/Data/code/nginx-data/www/ericmelz.site

   # Push site using github actions
   pushd $HOME/Data/code/nginx-data
   git status
   git add *
   git status
   git commit -m"Updated clothes site"
   git push
   popd
   ```


## 🔄 Updates and Regeneration

To update your website with new photos:

1. **Add new photos** to `source_photos/` directories
2. **Regenerate the site**:
   ```bash
   uv run generate_site.py
   ```
3. **Upload updated files**:
   ```bash
   # Copy site to nginx-data repo
   rsync -avz --delete output/website/ $HOME/Data/code/nginx-data/www/ericmelz.site

   # Push site using github actions
   pushd $HOME/Data/code/nginx-data
   git status
   git add *
   git status
   git commit -m"Updated clothes site"
   git push
   popd
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