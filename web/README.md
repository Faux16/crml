# CRML Studio

A modern, interactive web UI for validating and exploring CRML (Cyber Risk Modeling Language) models. Built with Next.js and shadcn/ui.

## Features

- 🎯 **Interactive Validator** - Real-time CRML validation with detailed error reporting
- 📝 **Monaco Editor** - Professional code editor with YAML syntax highlighting
- 📚 **Examples Gallery** - Browse and load example risk models
- 📖 **Documentation** - Comprehensive guides and API reference
- 🎨 **Modern UI** - Beautiful, responsive design with dark mode support
- ⚡ **Fast Performance** - Built on Next.js 14+ with optimized builds

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Python 3.9+ (for the backend API routes)
- CRML engine installed (`pip install crml-engine`)

### Installation

1. Navigate to the web directory:
```bash
cd web
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Building for Production

```bash
npm run build
npm start
```

## Project Structure

```
web/
├── app/                    # Next.js app directory
│   ├── api/               # API routes
│   │   ├── validate/      # CRML validation endpoint
│   │   └── examples/      # Examples fetching endpoint
│   ├── validator/         # Validator page
│   ├── examples/          # Examples gallery page
│   ├── docs/              # Documentation page
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Landing page
├── components/            # React components
│   ├── ui/               # shadcn/ui components
│   ├── Navbar.tsx        # Navigation bar
│   ├── Footer.tsx        # Footer
│   ├── CodeEditor.tsx    # Monaco editor wrapper
│   └── ValidationResults.tsx  # Results display
└── lib/                  # Utilities
```

## API Routes

### POST /api/validate

Validates CRML YAML content.

**Request:**
```json
{
  "yaml": "crml: \"1.1\"\nmeta:\n  name: \"test\"\n..."
}
```

**Response:**
```json
{
  "valid": true,
  "info": {
    "name": "test",
    "version": "1.1",
    "description": "..."
  }
}
```

### GET /api/examples

Fetches available example CRML files.

**Response:**
```json
{
  "examples": [
    {
      "id": "qber-enterprise",
      "filename": "qber-enterprise.yaml",
      "name": "QBER Enterprise Model",
      "description": "...",
      "tags": ["qber", "bayesian"],
      "content": "..."
    }
  ]
}
```

## Technologies

- **Framework:** Next.js 14+ with App Router
- **UI Library:** shadcn/ui
- **Styling:** Tailwind CSS
- **Code Editor:** Monaco Editor
- **Icons:** Lucide React
- **Language:** TypeScript

## Development

### Adding New Components

Use shadcn/ui CLI to add components:

```bash
npx shadcn@latest add [component-name]
```

### Environment Variables

Create a `.env.local` file for local development:

```env
# Add any environment variables here
```

## Deployment

CRML Studio can be deployed to:

- **Vercel** (recommended for Next.js)
- **Netlify**
- **AWS Amplify**
- **Docker** (custom deployment)

### Vercel Deployment

```bash
npm install -g vercel
vercel
```

## Contributing

Contributions are welcome! Please see the main [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](../LICENSE) for details.

## Support

- **GitHub Issues:** [Report bugs](https://github.com/Faux16/crml/issues)
- **Email:** research@zeron.one
- **Website:** [zeron.one](https://zeron.one)

---

**Maintained by Zeron Research Labs**
