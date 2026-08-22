# Downtime Analyzer - Deployment Guide

## Deploy to Vercel

### Prerequisites
- Vercel account (free at https://vercel.com)
- GitHub repository pushed with all files

### Steps

1. **Go to Vercel Dashboard**
   - Visit https://vercel.com/dashboard
   - Click "Add New" → "Project"

2. **Import Repository**
   - Select "GitHub" and authorize
   - Find and select `skye-bart/Downtime-analyzer`
   - Click "Import"

3. **Configure Project**
   - Framework Preset: "Other"
   - Root Directory: `./` (default)
   - Build Command: `pip install -r requirements.txt`
   - Output Directory: (leave empty)
   - Environment Variables: (skip for now)

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete (~2-3 minutes)

5. **Access Your App**
   - Once deployed, you'll get a URL like: `https://downtime-analyzer-xyz.vercel.app`
   - Visit the URL to use your app

### Troubleshooting

If deployment fails:
- Check the build logs in Vercel dashboard
- Ensure all files are committed to GitHub
- Verify `requirements.txt` has all dependencies
- Check that Python version is 3.9+ (Vercel default)

### Using the App

1. Upload a CSV with columns: `date`, `shift`, `area`, `equipment_tag`, `reason`, `duration_minutes`
2. View instant Pareto analysis and shift comparisons
3. Download analysis reports

### Notes
- File uploads stored in `/tmp` (temporary, serverless)
- Charts generated on-the-fly for each analysis
- Max file size: 5MB
- Timeout: 60 seconds per request
