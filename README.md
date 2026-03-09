# 🚀 DevOps Project Generator 🚀

A powerful CLI tool that scaffolds production-ready DevOps repositories with ease, allowing you to quickly bootstrap complete DevOps projects by selecting user-friendly options for pipeline frameworks, infrastructure patterns, deployment strategies, observability stacks, and security compliance frameworks.

## ✨ Why DevOps Project Generator?

Setting up a real-world DevOps project from scratch is repetitive and error-prone. This tool helps you bootstrap a complete DevOps-ready repository in seconds, following industry best practices and modern DevOps patterns.

✔ Opinionated but configurable  
✔ DevOps-focused, production-oriented  
✔ CLI support  
✔ No tool lock-in  
✔ Modern DevOps patterns

## 🎯 Who Is This For?

- **DevOps Engineers**
- **Cloud Engineers** 
- **Platform Engineers**
- **SREs**
- **Infrastructure Engineers**
- **DevOps Architects**
- **Students & professionals building real DevOps projects**

## 🌟 Key Features

- Fast DevOps project generation
- Interactive setup with modern UI
- Pipeline framework selection
- Infrastructure as Code patterns
- Deployment strategy templates
- Observability stack configurations
- Security compliance frameworks
- Best practices project structure
- Multi-environment support
- Integration-ready configurations

## 🖥️ Usage

### Quick Start

```bash
# Install
pip install devops-project-generator

# Generate a project
devops-project-generator init --name my-infra --pipeline nodejs-typescript --infra aws-vpc-eks --deploy blue-green

# Web UI (NEW v2.0.0)
cd web-ui && npm run dev
# Visit http://localhost:3000
```

### Documentation

- 📖 **[Commands Reference](COMMANDS.md)** - Complete command documentation
- 🎯 **[Usage Examples](EXAMPLES.md)** - Practical examples and workflows
- 📋 **[DevOps Patterns Guide](DEVOPS_PATTERNS.md)** - DevOps pattern customization guide

## 🧠 What This Generator Creates

A complete DevOps project structure covering:
- **Pipeline Frameworks** - CI/CD templates for various tech stacks
- **Infrastructure Patterns** - Terraform, CloudFormation, Ansible templates
- **Deployment Strategies** - Blue-green, canary, rolling, GitOps configurations
- **Observability Stacks** - Prometheus, Grafana, ELK, DataDog integrations
- **Security Frameworks** - NIST CSF, CIS Benchmarks, Zero Trust, SOC2, GDPR, HIPAA
- **Environment Management** - Multi-environment configurations
- **Automation Scripts** - Setup, deployment, and maintenance scripts

All generated based on your selected DevOps options.

## ⚙️ Supported Options (v2.0.0)

### 🔄 Pipeline Frameworks
- **Node.js + TypeScript** - Modern JavaScript/TypeScript pipelines
- **Python** - Python application pipelines
- **Java + Maven** - Enterprise Java pipelines
- **Go** - Go application pipelines
- **Docker Multi-Stage** - Containerized application pipelines
- **Terraform Module** - Infrastructure module pipelines
- **Kubernetes Operator** - Kubernetes operator pipelines
- **Microservice** - Microservice architecture pipelines

### ☁️ Infrastructure Patterns
- **AWS VPC + EKS** - Amazon EKS with VPC networking
- **Azure VNet + AKS** - Azure AKS with virtual networking
- **GCP VPC + GKE** - Google GKE with VPC networking
- **Multi-Cloud Terraform** - Cross-cloud infrastructure
- **Kubernetes On-Prem** - On-premises Kubernetes
- **AWS ECS Fargate** - Serverless container orchestration
- **Ansible Automation** - Configuration management

### 🚀 Deployment Strategies
- **Blue-Green** - Zero-downtime deployments
- **Canary** - Gradual rollout deployments
- **Rolling Updates** - Incremental updates
- **GitOps with ArgoCD** - Git-based continuous deployment
- **Helm Charts** - Kubernetes package management
- **Kustomize** - Kubernetes configuration management
- **Serverless Lambda** - AWS Lambda deployments

### 📊 Observability Stacks
- **Prometheus + Grafana** - Metrics and visualization
- **ELK Stack** - Elasticsearch, Logstash, Kibana
- **DataDog** - Full-stack monitoring
- **Jaeger + Prometheus** - Distributed tracing and metrics
- **AWS CloudWatch** - AWS native monitoring
- **New Relic** - Application performance monitoring

### 🔒 Security Frameworks
- **NIST CSF** - NIST Cybersecurity Framework
- **CIS Benchmarks** - Center for Internet Security controls
- **Zero Trust** - Zero Trust Architecture
- **SOC2 Compliance** - Service Organization Control 2
- **GDPR Compliance** - General Data Protection Regulation
- **HIPAA Compliance** - Health Insurance Portability and Accountability Act

### 🌍 Environments
- **Single** - Single environment setup
- **Dev / Stage / Prod** - Multi-environment setup
- **Custom** - Custom environment configuration

## 📦 Installation

### From PyPI

```bash
pip install devops-project-generator
```

### From Source

```bash
git clone https://github.com/NotHarshhaa/devops-project-generator.git
cd devops-project-generator
pip install -e .
```

### Web UI Setup

```bash
git clone https://github.com/NotHarshhaa/devops-project-generator.git
cd devops-project-generator/web-ui
npm install
npm run dev
```

### Development Setup

```bash
git clone https://github.com/NotHarshhaa/devops-project-generator.git
cd devops-project-generator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

## 🏗️ Generated Project Structure

```
devops-project/
├── pipelines/           # CI/CD pipeline configurations
├── infrastructure/      # Terraform/CloudFormation templates
├── deployments/         # Helm charts, Kustomize configs
├── monitoring/          # Prometheus, Grafana, ELK configs
├── security/            # Security policies and compliance
├── scripts/             # Automation scripts
├── config/              # Multi-environment configs
└── docs/               # Documentation
```

For detailed structure information, see the **[DevOps Patterns Guide](DEVOPS_PATTERNS.md)**.

### DevOps Pattern Templates

The generator supports custom DevOps patterns. See the **[DevOps Patterns Guide](DEVOPS_PATTERNS.md)** for detailed information on creating and customizing DevOps patterns.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/NotHarshhaa/devops-project-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/NotHarshhaa/devops-project-generator/discussions)
- **Documentation**: [Wiki](https://github.com/NotHarshhaa/devops-project-generator/wiki)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Typer** - For the amazing CLI framework
- **Rich** - For beautiful terminal output
- **Jinja2** - For powerful templating
- **Next.js** - For the modern web UI
- **DevOps Community** - For best practices and inspiration

## 📞 Contact

This project is crafted with 💡 by **[Harshhaa](https://github.com/NotHarshhaa)**.  
Your feedback is always welcome! Let's build together. 🚀  

📧 **Connect with me:**  
🔗 **GitHub**: [@NotHarshhaa](https://github.com/NotHarshhaa)  
🔗 **Portfolio**: [Personal Portfolio](https://notharshhaa.site)  
🔗 **Links - Portfolio**: [Links](https://link.notharshhaa.site)  
🔗 **Telegram Community**: [Join Here](https://t.me/prodevopsguy)  
🔗 **LinkedIn**: [Harshhaa Vardhan Reddy](https://www.linkedin.com/in/NotHarshhaa/)  

---

**Built with ❤️ by the DevOps community**  
*Making DevOps accessible to everyone*
