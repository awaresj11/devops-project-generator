export interface ProjectConfig {
  projectName: string;
  ci: CIOption;
  infra: InfraOption;
  deploy: DeployOption;
  envs: EnvOption;
  observability: ObservabilityOption;
  security: SecurityOption;
}

export type CIOption = "github-actions" | "gitlab-ci" | "jenkins" | "none";
export type InfraOption = "terraform" | "cloudformation" | "none";
export type DeployOption = "vm" | "docker" | "kubernetes";
export type EnvOption = "single" | "dev,stage,prod";
export type ObservabilityOption = "logs" | "logs-metrics" | "full";
export type SecurityOption = "basic" | "standard" | "strict";

export interface OptionCard {
  value: string;
  label: string;
  description: string;
  icon: string;
  recommended?: boolean;
}

export interface StepConfig {
  id: string;
  title: string;
  description: string;
  field: keyof ProjectConfig;
}

export interface GeneratedFile {
  path: string;
  content: string;
  type: "file" | "directory";
}

export interface GenerationResult {
  success: boolean;
  projectName: string;
  files: GeneratedFile[];
  summary: {
    totalFiles: number;
    totalDirs: number;
    components: string[];
  };
}
