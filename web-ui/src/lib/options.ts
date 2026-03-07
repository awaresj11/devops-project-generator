import { OptionCard, StepConfig } from "./types";

export const steps: StepConfig[] = [
  {
    id: "project",
    title: "Project Name",
    description: "Give your DevOps project a name",
    field: "projectName",
  },
  {
    id: "ci",
    title: "CI/CD Platform",
    description: "Choose your continuous integration and delivery platform",
    field: "ci",
  },
  {
    id: "infra",
    title: "Infrastructure",
    description: "Select your Infrastructure as Code tool",
    field: "infra",
  },
  {
    id: "deploy",
    title: "Deployment",
    description: "Pick your deployment strategy",
    field: "deploy",
  },
  {
    id: "envs",
    title: "Environments",
    description: "Configure your deployment environments",
    field: "envs",
  },
  {
    id: "observability",
    title: "Observability",
    description: "Set up monitoring and alerting",
    field: "observability",
  },
  {
    id: "security",
    title: "Security",
    description: "Define your security posture",
    field: "security",
  },
];

export const ciOptions: OptionCard[] = [
  {
    value: "github-actions",
    label: "GitHub Actions",
    description: "Native CI/CD for GitHub repositories with YAML workflows",
    icon: "github",
    recommended: true,
  },
  {
    value: "gitlab-ci",
    label: "GitLab CI",
    description: "Integrated CI/CD pipelines within GitLab",
    icon: "gitlab",
  },
  {
    value: "jenkins",
    label: "Jenkins",
    description: "Self-hosted automation server with extensible plugins",
    icon: "server",
  },
  {
    value: "none",
    label: "None",
    description: "Skip CI/CD setup for now",
    icon: "x",
  },
];

export const infraOptions: OptionCard[] = [
  {
    value: "terraform",
    label: "Terraform",
    description: "Multi-cloud IaC with HCL, state management & modules",
    icon: "layers",
    recommended: true,
  },
  {
    value: "cloudformation",
    label: "CloudFormation",
    description: "AWS-native infrastructure provisioning with YAML/JSON",
    icon: "cloud",
  },
  {
    value: "none",
    label: "None",
    description: "Skip infrastructure setup for now",
    icon: "x",
  },
];

export const deployOptions: OptionCard[] = [
  {
    value: "docker",
    label: "Docker",
    description: "Containerized deployment with Dockerfile & Compose",
    icon: "container",
    recommended: true,
  },
  {
    value: "kubernetes",
    label: "Kubernetes",
    description: "Container orchestration with manifests & Helm charts",
    icon: "ship",
  },
  {
    value: "vm",
    label: "Virtual Machine",
    description: "Traditional VM-based deployment with scripts",
    icon: "monitor",
  },
];

export const envOptions: OptionCard[] = [
  {
    value: "single",
    label: "Single",
    description: "One environment for simple projects or prototypes",
    icon: "box",
  },
  {
    value: "dev,stage,prod",
    label: "Dev / Stage / Prod",
    description: "Multi-environment pipeline for production workflows",
    icon: "git-branch",
    recommended: true,
  },
];

export const observabilityOptions: OptionCard[] = [
  {
    value: "logs",
    label: "Logs Only",
    description: "Basic logging configuration for your application",
    icon: "file-text",
  },
  {
    value: "logs-metrics",
    label: "Logs + Metrics",
    description: "Logging with Prometheus metrics collection",
    icon: "bar-chart",
    recommended: true,
  },
  {
    value: "full",
    label: "Full Observability",
    description: "Logs, metrics, and alerting rules for production",
    icon: "activity",
  },
];

export const securityOptions: OptionCard[] = [
  {
    value: "basic",
    label: "Basic",
    description: "Essential security: input validation, HTTPS, dependency scanning",
    icon: "shield",
  },
  {
    value: "standard",
    label: "Standard",
    description: "RBAC, secret management, container & dependency scanning",
    icon: "shield-check",
    recommended: true,
  },
  {
    value: "strict",
    label: "Strict",
    description: "Network policies, pod security, audit logging, compliance",
    icon: "shield-alert",
  },
];

export function getOptionsForStep(stepId: string): OptionCard[] {
  switch (stepId) {
    case "ci":
      return ciOptions;
    case "infra":
      return infraOptions;
    case "deploy":
      return deployOptions;
    case "envs":
      return envOptions;
    case "observability":
      return observabilityOptions;
    case "security":
      return securityOptions;
    default:
      return [];
  }
}
