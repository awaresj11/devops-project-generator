# DevOps Project Generator — Web UI

A modern, beautiful web interface for the [DevOps Project Generator](https://github.com/NotHarshhaa/devops-project-generator) CLI tool. Scaffold production-ready DevOps repositories through an interactive multi-step form — no terminal required.

## Tech Stack

- **Next.js 16** — React framework with App Router
- **shadcn/ui** — Accessible, composable component library
- **Tailwind CSS v4** — Utility-first styling
- **Lucide Icons** — Beautiful open-source icons
- **JSZip + FileSaver** — Client-side ZIP generation & download

## Features

- **7-step guided wizard** — Project name, CI/CD, Infrastructure, Deployment, Environments, Observability, Security
- **Live file preview** — Browse generated project structure and file contents before downloading
- **ZIP download** — Download the entire scaffolded project as a `.zip` file
- **CLI command export** — Copy the equivalent CLI command for reproducibility
- **Dark / Light theme** — Toggle between themes with one click
- **Fully responsive** — Works on desktop, tablet, and mobile

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Production build
npm run build
npm start
```

Open [http://localhost:3000](http://localhost:3000) to use the generator.

## Project Structure

```
web-ui/
├── src/
│   ├── app/
│   │   ├── api/generate/    # API route for project generation
│   │   ├── globals.css      # Theme & animation styles
│   │   ├── layout.tsx       # Root layout with providers
│   │   └── page.tsx         # Main page with hero + generator
│   ├── components/
│   │   ├── ui/              # shadcn/ui primitives
│   │   ├── file-tree.tsx    # Interactive file tree preview
│   │   ├── option-card.tsx  # Selection card component
│   │   ├── project-generator.tsx  # Main wizard form
│   │   ├── step-indicator.tsx     # Step progress bar
│   │   ├── theme-provider.tsx     # Dark/light theme context
│   │   └── theme-toggle.tsx       # Theme switch button
│   └── lib/
│       ├── generator.ts    # Project generation logic (mirrors Python CLI)
│       ├── options.ts      # Step & option configurations
│       ├── types.ts        # TypeScript type definitions
│       └── utils.ts        # Utility functions
```

## Supported Options

| Category       | Options                                        |
|----------------|------------------------------------------------|
| CI/CD          | GitHub Actions, GitLab CI, Jenkins, None        |
| Infrastructure | Terraform, CloudFormation, None                 |
| Deployment     | Docker, Kubernetes, VM                          |
| Environments   | Single, Dev / Stage / Prod                      |
| Observability  | Logs, Logs + Metrics, Full                      |
| Security       | Basic, Standard, Strict                         |

## Deploy

Deploy to Vercel, Netlify, or any platform that supports Next.js:

```bash
npm run build
```

## License

MIT — Part of the [DevOps Project Generator](https://github.com/NotHarshhaa/devops-project-generator) project by [@NotHarshhaa](https://github.com/NotHarshhaa).
