# CRML Studio Deployment

This repository includes CRML Studio (the interactive web UI) under `web/`.

## Quick Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Faux16/crml&project-name=crml-platform&root-directory=web)

**Or manually:**

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --cwd web
```

## Local Development

```bash
# Install dependencies
cd web
npm install

# Run dev server
npm run dev
```

Visit http://localhost:3000

## Project Structure

```
crml_full_repo/
├── src/crml/          # Python package
├── web/               # CRML Studio (Next.js)
├── examples/          # Example CRML models
└── wiki/              # Documentation (wiki source)
```

## Features

- 🎯 **Interactive Simulation** - Real-time CRML modeling with Monaco editor
- ✅ **Validator** - YAML validation with detailed error reporting
- 📚 **Examples Browser** - Pre-built models with explanations
- 📊 **Simulation Engine** - Monte Carlo simulation with visualization
- 📖 **Documentation** - Comprehensive guides and references

## Deployment Platforms

### Vercel (Recommended)
- Zero configuration
- Automatic HTTPS
- Free tier available
- Deploy: `vercel --cwd web`

### Netlify
- `netlify deploy --dir=web`

### Docker
```bash
cd web
docker build -t crml-web .
docker run -p 3000:3000 crml-web
```

## Environment Variables

No environment variables required for basic deployment.

## Python Backend

CRML Studio calls the Python backend via API routes. Ensure Python 3.9+ is available in your deployment environment.

For Vercel, Python is automatically available.

## License

MIT License - See LICENSE file
