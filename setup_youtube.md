# YouTube Upload Setup

To enable YouTube uploads, you need to:

1. **Get YouTube API Credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials
   - Download credentials as `client_secrets.json`
   - Place in `workspace/` directory

2. **First Time Authentication**:
   - Click "Upload to Social Media"
   - Select YouTube
   - Browser will open for Google login
   - Grant permissions to your app
   - Token will be saved for future use

3. **Switching Accounts**:
   - Check "Switch YouTube Account" in upload dialog
   - This will clear saved credentials
   - You'll be prompted to login again